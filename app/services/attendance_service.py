from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core import storage
from app.models.business import AttendanceStatus, AttendanceType, AuditActionType, DevicePlatform
from app.repositories.admin_repository import (
    create_device,
    get_device_by_fingerprint_and_employee,
    update_device_metadata,
)
from app.repositories.attendance_repository import (
    approve_record,
    create_attendance_record,
    create_fraud_detection,
    get_employee_shift,
    get_employee_with_dept,
    get_exception_records,
    get_history_records,
    get_latest_today_record,
    get_record_by_id,
    get_record_simple,
    get_today_active_checkin,
    get_today_active_checkout,
)
from app.repositories.auth_repository import create_audit_log
from app.repositories.geofence_repository import find_geofence_for_location
from app.schemas.attendance import (
    ApproveData,
    AttendanceDayRecord,
    AttendanceHistoryData,
    AttendanceRecordDetailData,
    AttendanceSummary,
    CheckInData,
    ExceptionEmployeeInfo,
    ExceptionFraudFlags,
    ExceptionItem,
    FraudResultInfo,
    HistoryDayCheckin,
    HistoryDayCheckout,
    HistoryEmployeeInfo,
    LocationInfo,
    RecordDeviceInfo,
    RecordEmployeeInfo,
    RecordFraudDetection,
    RecordShiftInfo,
    ShiftInfo,
    TodayRecordInfo,
    TodayStatusData,
)
from app.schemas.fraud import EvaluateFraudRequest, LivenessSignals, RawSignals
from app.services.fraud_service import evaluate_fraud

_TZ_OFFSET = timezone(timedelta(hours=7))
_GPS_ACCURACY_THRESHOLD = 20.0


def _now_local() -> datetime:
    return datetime.now(tz=_TZ_OFFSET)


def _to_local(dt: datetime) -> datetime:
    return dt.astimezone(_TZ_OFFSET)


def _build_location(record, rule) -> LocationInfo:
    building_id = building_name = floor_id = floor_name = None
    if rule is not None:
        cs = rule.cell_space
        building_id = cs.building_id
        floor_id = cs.floor_id
        if cs.building is not None:
            building_name = cs.building.name
        if cs.floor is not None:
            floor_name = cs.floor.floor_name
    return LocationInfo(
        latitude=record.latitude,
        longitude=record.longitude,
        altitude=record.altitude,
        gps_accuracy=record.gps_accuracy,
        building_id=building_id,
        building_name=building_name,
        floor_id=floor_id,
        floor_name=floor_name,
        geofence_rule_id=record.geofence_rule_id,
    )


def _build_fraud_result(fraud) -> FraudResultInfo:
    return FraudResultInfo(
        fraud_id=fraud.fraud_id,
        mock_location_detected=fraud.mock_location_detected,
        gps_spoofing_detected=fraud.gps_spoofing_detected,
        buddy_punch_suspected=fraud.buddy_punch_suspected,
        unknown_device=fraud.unknown_device,
        face_mismatch_detected=fraud.face_mismatch_detected,
        liveness_failed=fraud.liveness_failed,
        confidence_score=float(fraud.confidence_score) if fraud.confidence_score is not None else None,
    )


def _run_checkin_pipeline(
    db: Session,
    *,
    account,
    employee_id_form: int | None,
    device_fingerprint: str,
    platform_str: str,
    model: str | None,
    latitude: float,
    longitude: float,
    altitude: float,
    gps_accuracy: float,
    liveness_signals_json: str,
    raw_signals_json: str | None,
    face_image_bytes: bytes,
    face_image_content_type: str,
    is_mock_location: bool,
    record_type: AttendanceType,
    ip_address: str | None,
) -> CheckInData:
    # 1. GPS accuracy gate
    if gps_accuracy > _GPS_ACCURACY_THRESHOLD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "GPS_ACCURACY_TOO_LOW", "message": "GPS accuracy exceeds the allowed threshold", "details": {}},
        )

    # 2. Employee identity
    employee_id = account.employee.employee_id
    if employee_id_form is not None and employee_id_form != employee_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "EMPLOYEE_MISMATCH", "message": "Provided employee_id does not match the token", "details": {}},
        )

    # 3. Duplicate / pairing checks
    today_checkin = get_today_active_checkin(db, employee_id)
    today_checkout = get_today_active_checkout(db, employee_id)

    if record_type == AttendanceType.checkin:
        if today_checkin is not None and today_checkout is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "ALREADY_CHECKED_IN", "message": "Employee already has an active check-in today", "details": {}},
            )
    else:
        if today_checkin is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "FAILED_NO_CHECKIN", "message": "No approved check-in found for today", "details": {}},
            )

    # 4. Shift lookup
    now_local = _now_local()
    shift = get_employee_shift(db, employee_id, current_time=now_local.time())
    if shift is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "NO_SHIFT_FOUND", "message": "Employee has no active shift", "details": {}},
        )

    # 5. Device upsert
    device = get_device_by_fingerprint_and_employee(db, device_fingerprint, employee_id)
    if device is None:
        try:
            platform = DevicePlatform(platform_str)
        except ValueError:
            platform = DevicePlatform.other
        device = create_device(
            db,
            employee_id=employee_id,
            device_fingerprint=device_fingerprint,
            platform=platform,
            model=model,
        )
    else:
        device = update_device_metadata(db, device, model=model)

    # 6. Parse JSON signals
    try:
        liveness_signals = LivenessSignals.model_validate_json(liveness_signals_json)
    except Exception:
        liveness_signals = LivenessSignals()

    raw_signals: RawSignals | None = None
    if raw_signals_json:
        try:
            raw_signals = RawSignals.model_validate_json(raw_signals_json)
        except Exception:
            raw_signals = None

    # 7. Upload selfie to MinIO
    now_utc = now_local.astimezone(timezone.utc)
    ts_str = now_utc.strftime("%Y%m%d_%H%M%S")
    face_image_object_key = f"attendance/employee_{employee_id}/{record_type.value}_{ts_str}_{uuid.uuid4().hex[:8]}.jpg"
    try:
        storage.upload_file(face_image_bytes, face_image_object_key, content_type=face_image_content_type)
    except Exception:
        pass

    # 8. Geofence check
    geofence_rule = find_geofence_for_location(
        db, latitude, longitude, altitude,
        allow_checkin=(record_type == AttendanceType.checkin),
        allow_checkout=(record_type == AttendanceType.checkout),
    )

    # 9. Fraud evaluation
    fraud_payload = EvaluateFraudRequest(
        employee_id=employee_id,
        device_fingerprint=device_fingerprint,
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        gps_accuracy=gps_accuracy,
        timestamp=now_utc,
        is_mock_location=is_mock_location,
        face_image_object_key=face_image_object_key,
        liveness_signals=liveness_signals,
        raw_signals=raw_signals,
    )
    fraud_result = evaluate_fraud(db, fraud_payload)

    # 10. Determine record status
    rec_status: AttendanceStatus
    rejection_reason: str | None = None

    if geofence_rule is None:
        rec_status = AttendanceStatus.rejected
        rejection_reason = "outside_geofence"
    elif fraud_result.face_mismatch_detected or fraud_result.liveness_failed:
        rec_status = AttendanceStatus.rejected
        rejection_reason = fraud_result.reason or "face_verification_failed"
    elif fraud_result.flags:
        rec_status = AttendanceStatus.flagged
    else:
        rec_status = AttendanceStatus.approved

    # 11. Compute is_late / is_early_leave / worked_minutes
    is_late = False
    is_early_leave = False
    worked_minutes: int | None = None
    matched_checkin_record_id: int | None = None

    if rec_status in (AttendanceStatus.approved, AttendanceStatus.flagged):
        if record_type == AttendanceType.checkin:
            deadline = (
                datetime.combine(now_local.date(), shift.start_time)
                .replace(tzinfo=_TZ_OFFSET)
            ) + timedelta(minutes=shift.late_tolerance_min)
            is_late = now_local > deadline
        else:
            min_time = (
                datetime.combine(now_local.date(), shift.end_time)
                .replace(tzinfo=_TZ_OFFSET)
            ) - timedelta(minutes=shift.early_leave_min)
            is_early_leave = now_local < min_time
            if today_checkin is not None:
                matched_checkin_record_id = today_checkin.record_id
                delta = now_utc - today_checkin.timestamp.astimezone(timezone.utc)
                worked_minutes = int(delta.total_seconds() // 60)

    # 12. Write attendance record (flush for ID)
    record = create_attendance_record(
        db,
        employee_id=employee_id,
        device_id=device.device_id,
        shift_id=shift.shift_id,
        geofence_rule_id=geofence_rule.geofence_rule_id if geofence_rule else None,
        type=record_type,
        timestamp=now_utc,
        latitude=Decimal(str(latitude)),
        longitude=Decimal(str(longitude)),
        altitude=Decimal(str(altitude)),
        gps_accuracy=Decimal(str(gps_accuracy)),
        status=rec_status,
        rejection_reason=rejection_reason,
        is_late=is_late,
        is_early_leave=is_early_leave,
        face_image_object_key=face_image_object_key,
        matched_checkin_record_id=matched_checkin_record_id,
        worked_minutes=worked_minutes,
    )

    # 13. Write fraud detection
    fraud_db = create_fraud_detection(
        db,
        record_id=record.record_id,
        mock_location_detected=fraud_result.mock_location_detected,
        gps_spoofing_detected=fraud_result.gps_spoofing_detected,
        buddy_punch_suspected=fraud_result.buddy_punch_suspected,
        unknown_device=fraud_result.unknown_device,
        face_mismatch_detected=fraud_result.face_mismatch_detected,
        liveness_failed=fraud_result.liveness_failed,
        confidence_score=fraud_result.confidence_score,
        reason=fraud_result.reason,
    )

    db.commit()
    db.refresh(record)
    db.refresh(fraud_db)

    # 14. Audit log
    action = AuditActionType.checkin if record_type == AttendanceType.checkin else AuditActionType.checkout
    if rec_status == AttendanceStatus.rejected:
        action = AuditActionType.reject
    create_audit_log(
        db,
        account_id=account.account_id,
        action_type=action,
        target_entity="ATTENDANCE_RECORD",
        target_id=record.record_id,
        ip_address=ip_address,
    )

    message_verb = "Check-in" if record_type == AttendanceType.checkin else "Check-out"
    if rec_status == AttendanceStatus.approved:
        message = f"{message_verb} approved"
    elif rec_status == AttendanceStatus.flagged:
        message = f"{message_verb} flagged for review"
    else:
        message = f"{message_verb} rejected: {rejection_reason}"

    return CheckInData(
        record_id=record.record_id,
        employee_id=employee_id,
        type=record_type.value,
        status=rec_status.value,
        rejection_reason=rejection_reason,
        message=message,
        timestamp=_to_local(record.timestamp),
        is_late=is_late,
        is_early_leave=is_early_leave,
        matched_checkin_record_id=matched_checkin_record_id,
        worked_minutes=worked_minutes,
        shift=ShiftInfo.model_validate(shift),
        location=_build_location(record, geofence_rule),
        fraud_result=_build_fraud_result(fraud_db),
    )


def check_in(db: Session, *, account, **kwargs) -> CheckInData:
    return _run_checkin_pipeline(db, account=account, record_type=AttendanceType.checkin, **kwargs)


def check_out(db: Session, *, account, **kwargs) -> CheckInData:
    return _run_checkin_pipeline(db, account=account, record_type=AttendanceType.checkout, **kwargs)


def get_today_status(db: Session, account) -> TodayStatusData:
    employee_id = account.employee.employee_id
    now_local = _now_local()
    shift = get_employee_shift(db, employee_id, current_time=now_local.time())
    latest_checkin = get_latest_today_record(db, employee_id, AttendanceType.checkin)
    latest_checkout = get_latest_today_record(db, employee_id, AttendanceType.checkout)

    today_active_checkin = get_today_active_checkin(db, employee_id)
    today_active_checkout = get_today_active_checkout(db, employee_id)

    can_check_in = today_active_checkin is None or today_active_checkout is not None
    can_check_out = today_active_checkin is not None and today_active_checkout is None

    return TodayStatusData(
        date=now_local.date(),
        employee_id=employee_id,
        can_check_in=can_check_in,
        can_check_out=can_check_out,
        current_shift=ShiftInfo.model_validate(shift) if shift else None,
        latest_checkin=TodayRecordInfo(
            record_id=latest_checkin.record_id,
            timestamp=_to_local(latest_checkin.timestamp),
            status=latest_checkin.status.value,
        ) if latest_checkin else None,
        latest_checkout=TodayRecordInfo(
            record_id=latest_checkout.record_id,
            timestamp=_to_local(latest_checkout.timestamp),
            status=latest_checkout.status.value,
        ) if latest_checkout else None,
    )


def list_history(
    db: Session,
    account,
    *,
    employee_id: int | None,
    from_date: date,
    to_date: date,
    page: int,
    limit: int,
) -> AttendanceHistoryData:
    requester_id = account.employee.employee_id
    requester_role = account.role.value if hasattr(account.role, "value") else str(account.role)

    if requester_role == "employee":
        if employee_id is not None and employee_id != requester_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Employees can only view their own history", "details": {}},
            )
        employee_id = requester_id

    if employee_id is None:
        employee_id = requester_id

    emp = get_employee_with_dept(db, employee_id)
    if emp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "EMPLOYEE_NOT_FOUND", "message": "Employee not found", "details": {}},
        )

    records = get_history_records(db, employee_id, from_date, to_date)

    # Group records by local date
    days_map: dict[date, dict] = {}
    for rec in records:
        d = _to_local(rec.timestamp).date()
        if d not in days_map:
            days_map[d] = {"checkin": None, "checkout": None}
        if rec.type == AttendanceType.checkin and days_map[d]["checkin"] is None:
            days_map[d]["checkin"] = rec
        elif rec.type == AttendanceType.checkout and days_map[d]["checkout"] is None:
            days_map[d]["checkout"] = rec

    # Summary (across all days, before pagination)
    work_days = 0
    total_work_minutes = 0
    late_count = 0
    early_leave_count = 0
    rejected_count = 0
    for rec in records:
        if rec.status == AttendanceStatus.rejected:
            rejected_count += 1
        if rec.type == AttendanceType.checkin and rec.status in (AttendanceStatus.approved, AttendanceStatus.flagged):
            if rec.is_late:
                late_count += 1
        if rec.type == AttendanceType.checkout and rec.status in (AttendanceStatus.approved, AttendanceStatus.flagged):
            if rec.is_early_leave:
                early_leave_count += 1
            if rec.worked_minutes:
                total_work_minutes += rec.worked_minutes

    checkin_days = {
        _to_local(r.timestamp).date()
        for r in records
        if r.type == AttendanceType.checkin and r.status in (AttendanceStatus.approved, AttendanceStatus.flagged)
    }
    work_days = len(checkin_days)

    # Build sorted day records and paginate
    sorted_days = sorted(days_map.items())
    total_days = len(sorted_days)
    skip = (page - 1) * limit
    page_days = sorted_days[skip: skip + limit]

    day_records: list[AttendanceDayRecord] = []
    for d, pair in page_days:
        ci = pair["checkin"]
        co = pair["checkout"]
        building_name = floor_name = None
        if ci and ci.geofence_rule:
            cs = ci.geofence_rule.cell_space
            if cs:
                if cs.building:
                    building_name = cs.building.name
                if cs.floor:
                    floor_name = cs.floor.floor_name

        if ci and co:
            day_status = "completed"
        elif ci:
            day_status = "incomplete"
        else:
            day_status = "rejected"

        day_records.append(AttendanceDayRecord(
            date=d,
            checkin=HistoryDayCheckin(
                record_id=ci.record_id,
                timestamp=_to_local(ci.timestamp),
                status=ci.status.value,
                is_late=ci.is_late,
            ) if ci else None,
            checkout=HistoryDayCheckout(
                record_id=co.record_id,
                timestamp=_to_local(co.timestamp),
                status=co.status.value,
                is_early_leave=co.is_early_leave,
            ) if co else None,
            building_name=building_name,
            floor_name=floor_name,
            worked_minutes=co.worked_minutes if co else None,
            status=day_status,
        ))

    total_pages = max(1, (total_days + limit - 1) // limit)

    return AttendanceHistoryData(
        employee=HistoryEmployeeInfo(employee_id=emp.employee_id, full_name=emp.full_name),
        range={"from": str(from_date), "to": str(to_date)},
        summary=AttendanceSummary(
            work_days=work_days,
            total_work_minutes=total_work_minutes,
            late_count=late_count,
            early_leave_count=early_leave_count,
            rejected_count=rejected_count,
        ),
        days=day_records,
    ), total_days, page, limit, total_pages


def list_exceptions(
    db: Session,
    *,
    employee_id: int | None = None,
    department_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    status_filter: str | None = None,
    reason: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[ExceptionItem], int]:
    records, total = get_exception_records(
        db,
        employee_id=employee_id,
        department_id=department_id,
        from_date=from_date,
        to_date=to_date,
        status=status_filter,
        reason=reason,
        page=page,
        limit=limit,
    )
    items: list[ExceptionItem] = []
    for rec in records:
        emp = rec.employee
        dept = emp.department if hasattr(emp, "department") else None
        fraud = rec.fraud_detection
        items.append(ExceptionItem(
            record_id=rec.record_id,
            employee=ExceptionEmployeeInfo(
                employee_id=emp.employee_id,
                full_name=emp.full_name,
                department_name=dept.name if dept else None,
            ),
            type=rec.type.value if hasattr(rec.type, "value") else str(rec.type),
            timestamp=_to_local(rec.timestamp),
            status=rec.status.value if hasattr(rec.status, "value") else str(rec.status),
            rejection_reason=rec.rejection_reason,
            is_late=rec.is_late,
            is_early_leave=rec.is_early_leave,
            fraud_flags=ExceptionFraudFlags(
                mock_location_detected=fraud.mock_location_detected,
                gps_spoofing_detected=fraud.gps_spoofing_detected,
                buddy_punch_suspected=fraud.buddy_punch_suspected,
                unknown_device=fraud.unknown_device,
                face_mismatch_detected=fraud.face_mismatch_detected,
                liveness_failed=fraud.liveness_failed,
            ) if fraud else None,
        ))
    return items, total


def get_record_detail(db: Session, record_id: int) -> AttendanceRecordDetailData:
    record = get_record_by_id(db, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "RECORD_NOT_FOUND", "message": "Attendance record not found", "details": {}},
        )
    emp = record.employee
    dept = emp.department if hasattr(emp, "department") else None
    device = record.device
    shift = record.shift
    fraud = record.fraud_detection

    return AttendanceRecordDetailData(
        record_id=record.record_id,
        employee=RecordEmployeeInfo(
            employee_id=emp.employee_id,
            full_name=emp.full_name,
            department_id=dept.department_id if dept else None,
            department_name=dept.name if dept else None,
        ),
        device=RecordDeviceInfo(
            device_id=device.device_id,
            device_fingerprint=device.device_fingerprint,
            platform=device.platform.value if hasattr(device.platform, "value") else str(device.platform),
            model=device.model,
            is_trusted=device.is_trusted,
        ),
        shift=RecordShiftInfo(
            shift_id=shift.shift_id,
            name=shift.name,
            start_time=shift.start_time,
            end_time=shift.end_time,
        ) if shift else None,
        geofence_rule_id=record.geofence_rule_id,
        type=record.type.value if hasattr(record.type, "value") else str(record.type),
        timestamp=_to_local(record.timestamp),
        latitude=record.latitude,
        longitude=record.longitude,
        altitude=record.altitude,
        gps_accuracy=record.gps_accuracy,
        status=record.status.value if hasattr(record.status, "value") else str(record.status),
        rejection_reason=record.rejection_reason,
        is_late=record.is_late,
        is_early_leave=record.is_early_leave,
        fraud_detection=RecordFraudDetection(
            fraud_id=fraud.fraud_id,
            mock_location_detected=fraud.mock_location_detected,
            gps_spoofing_detected=fraud.gps_spoofing_detected,
            buddy_punch_suspected=fraud.buddy_punch_suspected,
            unknown_device=fraud.unknown_device,
            face_mismatch_detected=fraud.face_mismatch_detected,
            liveness_failed=fraud.liveness_failed,
            reason=fraud.reason,
            confidence_score=float(fraud.confidence_score) if fraud.confidence_score is not None else None,
            checked_at=_to_local(fraud.checked_at),
        ) if fraud else None,
    )


def approve_attendance_record(
    db: Session,
    record_id: int,
    *,
    account,
    ip_address: str | None,
) -> ApproveData:
    record = get_record_simple(db, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "RECORD_NOT_FOUND", "message": "Attendance record not found", "details": {}},
        )
    if record.status == AttendanceStatus.approved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "ALREADY_APPROVED", "message": "Record is already approved", "details": {}},
        )
    record = approve_record(db, record, account.account_id)
    create_audit_log(
        db,
        account_id=account.account_id,
        action_type=AuditActionType.approve,
        target_entity="ATTENDANCE_RECORD",
        target_id=record.record_id,
        ip_address=ip_address,
    )
    return ApproveData(
        record_id=record.record_id,
        status=record.status.value,
        rejection_reason=record.rejection_reason,
        approved_by_account_id=record.approved_by_account_id,
        approved_at=_to_local(record.approved_at),
    )

from __future__ import annotations

import math
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core import storage
from app.repositories.face_repository import get_face_reference
from app.repositories.fraud_repository import (
    get_device_by_fingerprint_and_employee,
    get_fraud_record_by_id,
    get_fraud_records,
    get_recent_device_records,
)
from app.schemas.fraud import (
    EvaluateFraudRequest,
    EvaluateFraudResult,
    FraudAttendanceInfo,
    FraudDeviceInfo,
    FraudEmployeeInfo,
    FraudRecordDetailData,
    FraudRecordItem,
)
from app.services.face_service import (
    _FACE_MATCH_THRESHOLD,
    _cosine_similarity,
    _extract_landmarks,
    _liveness_score,
)

_GPS_SPOOF_SPEED_THRESHOLD = 5.0  # m/s

_FLAG_DEDUCTIONS: dict[str, float] = {
    "mock_location": 40.0,
    "gps_spoofing": 35.0,
    "face_mismatch": 30.0,
    "liveness_failed": 25.0,
    "buddy_punch": 25.0,
    "unknown_device": 20.0,
}

_FLAG_PRIORITY = [
    "mock_location",
    "gps_spoofing",
    "face_mismatch",
    "liveness_failed",
    "buddy_punch",
    "unknown_device",
]


def _compute_confidence(flags: list[str]) -> float:
    score = 100.0
    for flag in flags:
        score -= _FLAG_DEDUCTIONS.get(flag, 0.0)
    return max(0.0, round(score, 1))


def evaluate_fraud(db: Session, payload: EvaluateFraudRequest) -> EvaluateFraudResult:
    flags: list[str] = []

    # 1. Mock location — direct OS flag
    mock_location_detected = payload.is_mock_location
    if mock_location_detected:
        flags.append("mock_location")

    # 2. GPS spoofing — speed anomaly
    gps_spoofing_detected = False
    if payload.raw_signals and payload.raw_signals.speed_mps is not None:
        gps_spoofing_detected = payload.raw_signals.speed_mps > _GPS_SPOOF_SPEED_THRESHOLD
    if gps_spoofing_detected:
        flags.append("gps_spoofing")

    # 3. Unknown device — not registered or not trusted for this employee
    device = get_device_by_fingerprint_and_employee(db, payload.device_fingerprint, payload.employee_id)
    unknown_device = device is None or not device.is_trusted
    if unknown_device:
        flags.append("unknown_device")

    # 4. Buddy punch — same device fingerprint used by a different employee in the last 24 h
    since = datetime.now(tz=timezone.utc) - timedelta(hours=24)
    recent = get_recent_device_records(db, payload.device_fingerprint, payload.employee_id, since)
    buddy_punch_suspected = len(recent) > 0
    if buddy_punch_suspected:
        flags.append("buddy_punch")

    # 5. Liveness check
    liveness_signals_dict = payload.liveness_signals.model_dump()
    _, liveness_passed = _liveness_score(liveness_signals_dict)
    liveness_failed = not liveness_passed
    if liveness_failed:
        flags.append("liveness_failed")

    # 6. Face comparison — download selfie from MinIO, compare against stored reference
    face_mismatch_detected = False
    face_ref = get_face_reference(db, payload.employee_id)
    if face_ref is None or payload.face_image_object_key is None:
        face_mismatch_detected = True
    else:
        try:
            reference_bytes = storage.download_file(face_ref.face_object_key)
            selfie_bytes = storage.download_file(payload.face_image_object_key)
            ref_landmarks = _extract_landmarks(reference_bytes)
            selfie_landmarks = _extract_landmarks(selfie_bytes)
            if ref_landmarks is None or selfie_landmarks is None:
                face_mismatch_detected = True
            else:
                raw_score = _cosine_similarity(ref_landmarks, selfie_landmarks)
                face_mismatch_detected = raw_score < _FACE_MATCH_THRESHOLD
        except Exception:
            face_mismatch_detected = True
    if face_mismatch_detected:
        flags.append("face_mismatch")

    confidence_score = _compute_confidence(flags)
    reason = next((f for f in _FLAG_PRIORITY if f in flags), None)

    return EvaluateFraudResult(
        mock_location_detected=mock_location_detected,
        gps_spoofing_detected=gps_spoofing_detected,
        buddy_punch_suspected=buddy_punch_suspected,
        unknown_device=unknown_device,
        face_mismatch_detected=face_mismatch_detected,
        liveness_failed=liveness_failed,
        confidence_score=confidence_score,
        reason=reason,
        flags=flags,
    )


def list_fraud_records(
    db: Session,
    *,
    employee_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    mock_location: bool | None = None,
    gps_spoofing: bool | None = None,
    buddy_punch: bool | None = None,
    unknown_device: bool | None = None,
    face_mismatch: bool | None = None,
    min_confidence_score: float | None = None,
    max_confidence_score: float | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[FraudRecordItem], int]:
    skip = (page - 1) * limit
    records, total = get_fraud_records(
        db,
        employee_id=employee_id,
        from_date=from_date,
        to_date=to_date,
        mock_location=mock_location,
        gps_spoofing=gps_spoofing,
        buddy_punch=buddy_punch,
        unknown_device=unknown_device,
        face_mismatch=face_mismatch,
        min_confidence_score=min_confidence_score,
        max_confidence_score=max_confidence_score,
        skip=skip,
        limit=limit,
    )

    items: list[FraudRecordItem] = []
    for fraud in records:
        rec = fraud.attendance_record
        emp = rec.employee
        dept = emp.department
        items.append(FraudRecordItem(
            fraud_id=fraud.fraud_id,
            record_id=fraud.record_id,
            employee=FraudEmployeeInfo(
                employee_id=emp.employee_id,
                full_name=emp.full_name,
                department_name=dept.name if dept else None,
            ),
            attendance_type=rec.type.value if hasattr(rec.type, "value") else str(rec.type),
            attendance_timestamp=rec.timestamp,
            mock_location_detected=fraud.mock_location_detected,
            gps_spoofing_detected=fraud.gps_spoofing_detected,
            buddy_punch_suspected=fraud.buddy_punch_suspected,
            unknown_device=fraud.unknown_device,
            face_mismatch_detected=fraud.face_mismatch_detected,
            liveness_failed=fraud.liveness_failed,
            confidence_score=float(fraud.confidence_score) if fraud.confidence_score is not None else None,
            reason=fraud.reason,
            checked_at=fraud.checked_at,
        ))
    return items, total


def get_fraud_record_detail(db: Session, fraud_id: int) -> FraudRecordDetailData:
    fraud = get_fraud_record_by_id(db, fraud_id)
    if fraud is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "FRAUD_NOT_FOUND", "message": "Fraud record not found", "details": {}},
        )
    rec = fraud.attendance_record
    emp = rec.employee
    dept = emp.department
    device = rec.device

    return FraudRecordDetailData(
        fraud_id=fraud.fraud_id,
        record_id=fraud.record_id,
        employee=FraudEmployeeInfo(
            employee_id=emp.employee_id,
            full_name=emp.full_name,
            department_name=dept.name if dept else None,
        ),
        attendance=FraudAttendanceInfo(
            type=rec.type.value if hasattr(rec.type, "value") else str(rec.type),
            timestamp=rec.timestamp,
            status=rec.status.value if hasattr(rec.status, "value") else str(rec.status),
            rejection_reason=rec.rejection_reason,
            latitude=rec.latitude,
            longitude=rec.longitude,
            altitude=rec.altitude,
            gps_accuracy=rec.gps_accuracy,
        ),
        device=FraudDeviceInfo(
            device_id=device.device_id,
            device_fingerprint=device.device_fingerprint,
            platform=device.platform.value if hasattr(device.platform, "value") else str(device.platform),
            model=device.model,
            is_trusted=device.is_trusted,
        ),
        mock_location_detected=fraud.mock_location_detected,
        gps_spoofing_detected=fraud.gps_spoofing_detected,
        buddy_punch_suspected=fraud.buddy_punch_suspected,
        unknown_device=fraud.unknown_device,
        face_mismatch_detected=fraud.face_mismatch_detected,
        liveness_failed=fraud.liveness_failed,
        confidence_score=float(fraud.confidence_score) if fraud.confidence_score is not None else None,
        reason=fraud.reason,
        checked_at=fraud.checked_at,
    )

from __future__ import annotations

from datetime import date, datetime, time as time_type, timezone

from sqlalchemy.orm import Session, contains_eager, joinedload

from app.models.business import (
    AttendanceRecord,
    Department,
    Device,
    Employee,
    FraudDetection,
)


def get_fraud_records(
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
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[FraudDetection], int]:
    q = (
        db.query(FraudDetection)
        .join(FraudDetection.attendance_record)
        .join(AttendanceRecord.employee)
        .outerjoin(Employee.department)
        .options(
            contains_eager(FraudDetection.attendance_record)
            .contains_eager(AttendanceRecord.employee)
            .contains_eager(Employee.department)
        )
    )
    if employee_id is not None:
        q = q.filter(AttendanceRecord.employee_id == employee_id)
    if from_date is not None:
        q = q.filter(
            AttendanceRecord.timestamp >= datetime.combine(from_date, time_type.min).replace(tzinfo=timezone.utc)
        )
    if to_date is not None:
        q = q.filter(
            AttendanceRecord.timestamp <= datetime.combine(to_date, time_type.max).replace(tzinfo=timezone.utc)
        )
    if mock_location is not None:
        q = q.filter(FraudDetection.mock_location_detected == mock_location)
    if gps_spoofing is not None:
        q = q.filter(FraudDetection.gps_spoofing_detected == gps_spoofing)
    if buddy_punch is not None:
        q = q.filter(FraudDetection.buddy_punch_suspected == buddy_punch)
    if unknown_device is not None:
        q = q.filter(FraudDetection.unknown_device == unknown_device)
    if face_mismatch is not None:
        q = q.filter(FraudDetection.face_mismatch_detected == face_mismatch)
    if min_confidence_score is not None:
        q = q.filter(FraudDetection.confidence_score >= min_confidence_score)
    if max_confidence_score is not None:
        q = q.filter(FraudDetection.confidence_score <= max_confidence_score)

    total = q.count()
    records = q.order_by(FraudDetection.checked_at.desc()).offset(skip).limit(limit).all()
    return records, total


def get_fraud_record_by_id(db: Session, fraud_id: int) -> FraudDetection | None:
    return (
        db.query(FraudDetection)
        .options(
            joinedload(FraudDetection.attendance_record)
            .joinedload(AttendanceRecord.employee)
            .joinedload(Employee.department),
            joinedload(FraudDetection.attendance_record)
            .joinedload(AttendanceRecord.device),
        )
        .filter(FraudDetection.fraud_id == fraud_id)
        .first()
    )


def get_recent_device_records(
    db: Session,
    device_fingerprint: str,
    exclude_employee_id: int,
    since: datetime,
) -> list[AttendanceRecord]:
    return (
        db.query(AttendanceRecord)
        .join(Device, AttendanceRecord.device_id == Device.device_id)
        .filter(
            Device.device_fingerprint == device_fingerprint,
            AttendanceRecord.employee_id != exclude_employee_id,
            AttendanceRecord.timestamp >= since,
        )
        .limit(1)
        .all()
    )


def get_device_by_fingerprint_and_employee(
    db: Session,
    device_fingerprint: str,
    employee_id: int,
) -> Device | None:
    return (
        db.query(Device)
        .filter(
            Device.device_fingerprint == device_fingerprint,
            Device.employee_id == employee_id,
        )
        .first()
    )

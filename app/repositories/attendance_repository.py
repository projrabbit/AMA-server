from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.business import (
    AttendanceRecord,
    AttendanceStatus,
    AttendanceType,
    Employee,
    FraudDetection,
    Shift,
)

_TZ_OFFSET = timezone(timedelta(hours=7))


def _today_utc_range() -> tuple[datetime, datetime]:
    now_local = datetime.now(tz=_TZ_OFFSET)
    day_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    return day_start.astimezone(timezone.utc), day_end.astimezone(timezone.utc)


def _date_utc_range(d: date) -> tuple[datetime, datetime]:
    start = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=_TZ_OFFSET).astimezone(timezone.utc)
    end = start + timedelta(days=1)
    return start, end


# ── Active check-in / check-out for today ────────────────────────────────────

_ACTIVE_STATUSES = (AttendanceStatus.approved, AttendanceStatus.flagged)


def get_today_active_checkin(db: Session, employee_id: int) -> AttendanceRecord | None:
    start, end = _today_utc_range()
    stmt = (
        select(AttendanceRecord)
        .where(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.type == AttendanceType.checkin,
            AttendanceRecord.status.in_(_ACTIVE_STATUSES),
            AttendanceRecord.timestamp >= start,
            AttendanceRecord.timestamp < end,
        )
        .order_by(AttendanceRecord.timestamp.desc())
        .limit(1)
    )
    return db.execute(stmt).scalars().first()


def get_today_active_checkout(db: Session, employee_id: int) -> AttendanceRecord | None:
    start, end = _today_utc_range()
    stmt = (
        select(AttendanceRecord)
        .where(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.type == AttendanceType.checkout,
            AttendanceRecord.status.in_(_ACTIVE_STATUSES),
            AttendanceRecord.timestamp >= start,
            AttendanceRecord.timestamp < end,
        )
        .order_by(AttendanceRecord.timestamp.desc())
        .limit(1)
    )
    return db.execute(stmt).scalars().first()


def get_latest_today_record(
    db: Session, employee_id: int, type_: AttendanceType
) -> AttendanceRecord | None:
    start, end = _today_utc_range()
    stmt = (
        select(AttendanceRecord)
        .where(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.type == type_,
            AttendanceRecord.timestamp >= start,
            AttendanceRecord.timestamp < end,
        )
        .order_by(AttendanceRecord.timestamp.desc())
        .limit(1)
    )
    return db.execute(stmt).scalars().first()


# ── Shift lookup ──────────────────────────────────────────────────────────────

def get_employee_shift(db: Session, employee_id: int, current_time: time | None = None) -> Shift | None:
    if current_time is not None:
        stmt = (
            select(Shift)
            .where(
                Shift.employee_id == employee_id,
                Shift.start_time <= current_time,
                Shift.end_time >= current_time,
            )
            .limit(1)
        )
        result = db.execute(stmt).scalars().first()
        if result:
            return result
    stmt2 = (
        select(Shift)
        .where(Shift.employee_id == employee_id)
        .order_by(Shift.shift_id.desc())
        .limit(1)
    )
    return db.execute(stmt2).scalars().first()


# ── Employee lookup ───────────────────────────────────────────────────────────

def get_employee_with_dept(db: Session, employee_id: int) -> Employee | None:
    stmt = (
        select(Employee)
        .where(Employee.employee_id == employee_id)
        .options(joinedload(Employee.department))
    )
    return db.execute(stmt).unique().scalars().first()


# ── Write attendance + fraud ──────────────────────────────────────────────────

def create_attendance_record(db: Session, **fields) -> AttendanceRecord:
    record = AttendanceRecord(**fields)
    db.add(record)
    db.flush()
    return record


def create_fraud_detection(db: Session, **fields) -> FraudDetection:
    fraud = FraudDetection(**fields)
    db.add(fraud)
    return fraud


# ── Single record detail ──────────────────────────────────────────────────────

def get_record_by_id(db: Session, record_id: int) -> AttendanceRecord | None:
    stmt = (
        select(AttendanceRecord)
        .where(AttendanceRecord.record_id == record_id)
        .options(
            joinedload(AttendanceRecord.employee).joinedload(Employee.department),
            joinedload(AttendanceRecord.device),
            joinedload(AttendanceRecord.shift),
            joinedload(AttendanceRecord.fraud_detection),
        )
    )
    return db.execute(stmt).unique().scalars().first()


# ── History ───────────────────────────────────────────────────────────────────

def get_history_records(
    db: Session,
    employee_id: int,
    from_date: date,
    to_date: date,
) -> list[AttendanceRecord]:
    start, _ = _date_utc_range(from_date)
    _, end = _date_utc_range(to_date)
    stmt = (
        select(AttendanceRecord)
        .where(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.timestamp >= start,
            AttendanceRecord.timestamp < end,
        )
        .options(
            joinedload(AttendanceRecord.geofence_rule),
        )
        .order_by(AttendanceRecord.timestamp.asc())
    )
    return list(db.execute(stmt).unique().scalars().all())


# ── Exceptions list ───────────────────────────────────────────────────────────

def get_exception_records(
    db: Session,
    *,
    employee_id: int | None = None,
    department_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    status: str | None = None,
    reason: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[AttendanceRecord], int]:
    skip = (page - 1) * limit
    base = (
        select(AttendanceRecord)
        .join(AttendanceRecord.employee)
        .options(
            joinedload(AttendanceRecord.employee).joinedload(Employee.department),
            joinedload(AttendanceRecord.fraud_detection),
        )
    )

    if status is not None:
        try:
            base = base.where(AttendanceRecord.status == AttendanceStatus(status))
        except ValueError:
            pass
    else:
        from sqlalchemy import or_
        base = base.where(
            or_(
                AttendanceRecord.status == AttendanceStatus.rejected,
                AttendanceRecord.status == AttendanceStatus.flagged,
                AttendanceRecord.is_late == True,  # noqa: E712
                AttendanceRecord.is_early_leave == True,  # noqa: E712
            )
        )

    if employee_id is not None:
        base = base.where(AttendanceRecord.employee_id == employee_id)
    if department_id is not None:
        base = base.where(Employee.department_id == department_id)
    if from_date is not None:
        start, _ = _date_utc_range(from_date)
        base = base.where(AttendanceRecord.timestamp >= start)
    if to_date is not None:
        _, end = _date_utc_range(to_date)
        base = base.where(AttendanceRecord.timestamp < end)
    if reason is not None:
        base = base.where(AttendanceRecord.rejection_reason == reason)

    total_stmt = select(func.count()).select_from(base.subquery())
    total = db.execute(total_stmt).scalar_one()

    rows_stmt = base.order_by(AttendanceRecord.timestamp.desc()).offset(skip).limit(limit)
    rows = list(db.execute(rows_stmt).unique().scalars().all())
    return rows, total


# ── Approve ───────────────────────────────────────────────────────────────────

def get_record_simple(db: Session, record_id: int) -> AttendanceRecord | None:
    return db.get(AttendanceRecord, record_id)


def approve_record(db: Session, record: AttendanceRecord, account_id: int) -> AttendanceRecord:
    now = datetime.now(tz=timezone.utc)
    record.status = AttendanceStatus.approved
    record.rejection_reason = None
    record.approved_by_account_id = account_id
    record.approved_at = now
    db.commit()
    db.refresh(record)
    return record

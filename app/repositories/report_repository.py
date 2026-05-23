from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.business import (
    AttendanceRecord,
    AttendanceStatus,
    AttendanceType,
    Employee,
    EmployeeStatus,
    Shift,
)
from app.models.gis import Building, CellSpace, Floor, GeofenceRule

_TZ = timezone(timedelta(hours=7))


def _day_bounds(target: date) -> tuple[datetime, datetime]:
    start = datetime.combine(target, time.min).replace(tzinfo=_TZ)
    end = datetime.combine(target, time.max).replace(tzinfo=_TZ)
    return start, end


def get_active_employee_count(db: Session) -> int:
    return db.execute(
        select(func.count()).select_from(Employee).where(Employee.status == EmployeeStatus.active)
    ).scalar_one()


def get_shift_holder_count(db: Session) -> int:
    return db.execute(
        select(func.count(func.distinct(Shift.employee_id)))
    ).scalar_one()


def get_dashboard_checkin_stats(db: Session, target_date: date) -> dict[str, int]:
    day_start, day_end = _day_bounds(target_date)
    _approved = [AttendanceStatus.approved, AttendanceStatus.flagged]

    base = and_(
        AttendanceRecord.type == AttendanceType.checkin,
        AttendanceRecord.status.in_(_approved),
        AttendanceRecord.timestamp >= day_start,
        AttendanceRecord.timestamp <= day_end,
    )

    checked_in = db.execute(
        select(func.count(func.distinct(AttendanceRecord.employee_id))).where(base)
    ).scalar_one()

    on_time = db.execute(
        select(func.count(func.distinct(AttendanceRecord.employee_id)))
        .where(base, AttendanceRecord.is_late.is_(False))
    ).scalar_one()

    late = db.execute(
        select(func.count(func.distinct(AttendanceRecord.employee_id)))
        .where(base, AttendanceRecord.is_late.is_(True))
    ).scalar_one()

    early_leave = db.execute(
        select(func.count(func.distinct(AttendanceRecord.employee_id))).where(
            AttendanceRecord.type == AttendanceType.checkout,
            AttendanceRecord.status.in_(_approved),
            AttendanceRecord.timestamp >= day_start,
            AttendanceRecord.timestamp <= day_end,
            AttendanceRecord.is_early_leave.is_(True),
        )
    ).scalar_one()

    return {
        "checked_in_today": checked_in,
        "on_time_count": on_time,
        "late_count": late,
        "early_leave_count": early_leave,
    }


def get_fraud_alert_count(db: Session, target_date: date) -> int:
    day_start, day_end = _day_bounds(target_date)
    return db.execute(
        select(func.count()).select_from(AttendanceRecord).where(
            AttendanceRecord.status == AttendanceStatus.flagged,
            AttendanceRecord.type == AttendanceType.checkin,
            AttendanceRecord.timestamp >= day_start,
            AttendanceRecord.timestamp <= day_end,
        )
    ).scalar_one()


def get_checked_in_shift_holders_count(db: Session, target_date: date) -> int:
    day_start, day_end = _day_bounds(target_date)
    shift_holder_subq = select(Shift.employee_id).distinct()
    return db.execute(
        select(func.count(func.distinct(AttendanceRecord.employee_id))).where(
            AttendanceRecord.type == AttendanceType.checkin,
            AttendanceRecord.status.in_([AttendanceStatus.approved, AttendanceStatus.flagged]),
            AttendanceRecord.timestamp >= day_start,
            AttendanceRecord.timestamp <= day_end,
            AttendanceRecord.employee_id.in_(shift_holder_subq),
        )
    ).scalar_one()


def _location_options():
    return [
        joinedload(AttendanceRecord.employee).joinedload(Employee.department),
        joinedload(AttendanceRecord.geofence_rule).options(
            joinedload(GeofenceRule.cell_space).options(
                joinedload(CellSpace.floor),
                joinedload(CellSpace.building),
            )
        ),
    ]


def get_active_locations(db: Session, target_date: date) -> list[AttendanceRecord]:
    day_start, day_end = _day_bounds(target_date)
    _approved = [AttendanceStatus.approved, AttendanceStatus.flagged]

    checkout_subq = select(AttendanceRecord.employee_id).where(
        AttendanceRecord.type == AttendanceType.checkout,
        AttendanceRecord.status.in_(_approved),
        AttendanceRecord.timestamp >= day_start,
        AttendanceRecord.timestamp <= day_end,
    )

    stmt = (
        select(AttendanceRecord)
        .where(
            AttendanceRecord.type == AttendanceType.checkin,
            AttendanceRecord.status.in_(_approved),
            AttendanceRecord.timestamp >= day_start,
            AttendanceRecord.timestamp <= day_end,
            AttendanceRecord.employee_id.not_in(checkout_subq),
        )
        .options(*_location_options())
    )
    return list(db.execute(stmt).unique().scalars().all())


def get_realtime_locations(
    db: Session,
    target_date: date,
    *,
    building_id: int | None = None,
    floor_id: int | None = None,
    department_id: int | None = None,
) -> list[AttendanceRecord]:
    day_start, day_end = _day_bounds(target_date)
    _approved = [AttendanceStatus.approved, AttendanceStatus.flagged]

    checkout_subq = select(AttendanceRecord.employee_id).where(
        AttendanceRecord.type == AttendanceType.checkout,
        AttendanceRecord.status.in_(_approved),
        AttendanceRecord.timestamp >= day_start,
        AttendanceRecord.timestamp <= day_end,
    )

    conditions: list = [
        AttendanceRecord.type == AttendanceType.checkin,
        AttendanceRecord.status.in_(_approved),
        AttendanceRecord.timestamp >= day_start,
        AttendanceRecord.timestamp <= day_end,
        AttendanceRecord.employee_id.not_in(checkout_subq),
    ]

    if building_id is not None or floor_id is not None:
        geo_subq = select(GeofenceRule.geofence_rule_id).join(
            CellSpace, GeofenceRule.cell_space_id == CellSpace.cell_space_id
        )
        if building_id is not None:
            geo_subq = geo_subq.where(CellSpace.building_id == building_id)
        if floor_id is not None:
            geo_subq = geo_subq.where(CellSpace.floor_id == floor_id)
        conditions.append(AttendanceRecord.geofence_rule_id.in_(geo_subq))

    if department_id is not None:
        dept_subq = select(Employee.employee_id).where(Employee.department_id == department_id)
        conditions.append(AttendanceRecord.employee_id.in_(dept_subq))

    stmt = (
        select(AttendanceRecord)
        .where(and_(*conditions))
        .options(*_location_options())
    )
    return list(db.execute(stmt).unique().scalars().all())


def get_report_records(
    db: Session,
    from_date: date,
    to_date: date,
    *,
    department_id: int | None = None,
    employee_id: int | None = None,
) -> list[AttendanceRecord]:
    from_dt = datetime.combine(from_date, time.min).replace(tzinfo=_TZ)
    to_dt = datetime.combine(to_date, time.max).replace(tzinfo=_TZ)

    conditions: list = [
        AttendanceRecord.timestamp >= from_dt,
        AttendanceRecord.timestamp <= to_dt,
    ]

    if employee_id is not None:
        conditions.append(AttendanceRecord.employee_id == employee_id)

    if department_id is not None:
        dept_subq = select(Employee.employee_id).where(Employee.department_id == department_id)
        conditions.append(AttendanceRecord.employee_id.in_(dept_subq))

    stmt = (
        select(AttendanceRecord)
        .where(and_(*conditions))
        .options(joinedload(AttendanceRecord.employee).joinedload(Employee.department))
    )
    return list(db.execute(stmt).unique().scalars().all())

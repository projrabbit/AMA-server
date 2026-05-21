from __future__ import annotations

from datetime import time

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.business import (
    Account,
    AccountRole,
    Department,
    Device,
    DevicePlatform,
    Employee,
    EmployeeStatus,
    FaceReference,
    Shift,
)


# ── Employee ──────────────────────────────────────────────────────────────────

def get_employees(
    db: Session,
    *,
    department_id: int | None = None,
    status: EmployeeStatus | None = None,
    q: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Employee], int]:
    base = (
        db.query(Employee)
        .options(joinedload(Employee.account), joinedload(Employee.department))
    )
    if department_id is not None:
        base = base.filter(Employee.department_id == department_id)
    if status is not None:
        base = base.filter(Employee.status == status)
    if q:
        pattern = f"%{q}%"
        base = base.filter(
            Employee.full_name.ilike(pattern)
            | Employee.email.ilike(pattern)
            | Employee.phone.ilike(pattern)
        )
    total = base.count()
    rows = base.offset(skip).limit(limit).all()
    return rows, total


def get_employee_by_id(db: Session, employee_id: int) -> Employee | None:
    return (
        db.query(Employee)
        .options(
            joinedload(Employee.account),
            joinedload(Employee.department),
            joinedload(Employee.devices),
            joinedload(Employee.shifts),
            joinedload(Employee.face_reference),
        )
        .filter(Employee.employee_id == employee_id)
        .first()
    )


def get_employee_by_email(db: Session, email: str) -> Employee | None:
    return db.query(Employee).filter(Employee.email == email).first()


def get_employee_by_phone(db: Session, phone: str) -> Employee | None:
    return db.query(Employee).filter(Employee.phone == phone).first()


def create_employee_and_account(
    db: Session,
    *,
    full_name: str,
    department_id: int,
    position: str,
    email: str,
    phone: str,
    hire_date,
    role: AccountRole,
    password_hash: str,
) -> tuple[Employee, Account]:
    employee = Employee(
        full_name=full_name,
        department_id=department_id,
        position=position,
        email=email,
        phone=phone,
        hire_date=hire_date,
        status=EmployeeStatus.active,
    )
    db.add(employee)
    db.flush()  # get employee_id without committing

    account = Account(
        employee_id=employee.employee_id,
        username=email,
        password_hash=password_hash,
        role=role,
        is_active=True,
    )
    db.add(account)
    db.commit()
    db.refresh(employee)
    db.refresh(account)
    return employee, account


def update_employee_fields(db: Session, employee: Employee, **fields) -> Employee:
    for key, value in fields.items():
        setattr(employee, key, value)
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def deactivate_employee(db: Session, employee: Employee, account: Account) -> Employee:
    employee.status = EmployeeStatus.inactive
    account.is_active = False
    db.add(employee)
    db.add(account)
    db.commit()
    db.refresh(employee)
    return employee


# ── Department ────────────────────────────────────────────────────────────────

def get_departments(
    db: Session,
    *,
    q: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[dict], int]:
    manager_alias = db.query(Employee).subquery()

    count_subq = (
        db.query(func.count(Employee.employee_id))
        .filter(Employee.department_id == Department.department_id)
        .correlate(Department)
        .scalar_subquery()
    )

    base = db.query(
        Department,
        Employee.full_name.label("manager_name"),
        count_subq.label("employee_count"),
    ).outerjoin(Employee, Employee.employee_id == Department.manager_id)

    if q:
        base = base.filter(Department.name.ilike(f"%{q}%"))

    total = db.query(func.count(Department.department_id)).scalar() or 0
    rows = base.offset(skip).limit(limit).all()

    results = []
    for dept, manager_name, employee_count in rows:
        results.append({
            "department_id": dept.department_id,
            "name": dept.name,
            "description": dept.description,
            "manager_id": dept.manager_id,
            "manager_name": manager_name,
            "employee_count": employee_count or 0,
            "created_at": dept.created_at,
        })
    return results, total


def get_department_by_id(db: Session, department_id: int) -> Department | None:
    return db.query(Department).filter(Department.department_id == department_id).first()


def get_department_by_name(db: Session, name: str) -> Department | None:
    return db.query(Department).filter(Department.name == name).first()


def create_department(
    db: Session,
    *,
    name: str,
    description: str | None,
    manager_id: int | None,
) -> Department:
    dept = Department(name=name, description=description, manager_id=manager_id)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


def update_department_fields(db: Session, department: Department, **fields) -> Department:
    for key, value in fields.items():
        setattr(department, key, value)
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


# ── Shift ─────────────────────────────────────────────────────────────────────

def get_shifts(
    db: Session,
    *,
    employee_id: int | None = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Shift], int]:
    base = db.query(Shift).options(joinedload(Shift.employee))
    if employee_id is not None:
        base = base.filter(Shift.employee_id == employee_id)
    total = base.count()
    rows = base.offset(skip).limit(limit).all()
    return rows, total


def get_shift_by_id(db: Session, shift_id: int) -> Shift | None:
    return (
        db.query(Shift)
        .options(joinedload(Shift.employee))
        .filter(Shift.shift_id == shift_id)
        .first()
    )


def has_shift_conflict(
    db: Session,
    employee_id: int,
    start_time: time,
    end_time: time,
    exclude_shift_id: int | None = None,
) -> bool:
    q = db.query(Shift).filter(
        Shift.employee_id == employee_id,
        Shift.start_time < end_time,
        Shift.end_time > start_time,
    )
    if exclude_shift_id is not None:
        q = q.filter(Shift.shift_id != exclude_shift_id)
    return db.query(q.exists()).scalar()


def create_shift(
    db: Session,
    *,
    employee_id: int,
    name: str,
    start_time: time,
    end_time: time,
    late_tolerance_min: int,
    early_leave_min: int,
    apply_to_weekends: bool,
) -> Shift:
    shift = Shift(
        employee_id=employee_id,
        name=name,
        start_time=start_time,
        end_time=end_time,
        late_tolerance_min=late_tolerance_min,
        early_leave_min=early_leave_min,
        apply_to_weekends=apply_to_weekends,
    )
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


def update_shift_fields(db: Session, shift: Shift, **fields) -> Shift:
    for key, value in fields.items():
        setattr(shift, key, value)
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


def assign_shift_to_employee(db: Session, shift: Shift, employee_id: int) -> Shift:
    shift.employee_id = employee_id
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


# ── Device ────────────────────────────────────────────────────────────────────

def get_devices(
    db: Session,
    *,
    employee_id: int | None = None,
    is_trusted: bool | None = None,
    platform: DevicePlatform | None = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Device], int]:
    base = (
        db.query(Device)
        .options(joinedload(Device.employee).joinedload(Employee.department))
    )
    if employee_id is not None:
        base = base.filter(Device.employee_id == employee_id)
    if is_trusted is not None:
        base = base.filter(Device.is_trusted == is_trusted)
    if platform is not None:
        base = base.filter(Device.platform == platform)
    total = base.count()
    rows = base.offset(skip).limit(limit).all()
    return rows, total


def get_device_by_id(db: Session, device_id: int) -> Device | None:
    return db.query(Device).filter(Device.device_id == device_id).first()


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


def get_devices_for_employee(db: Session, employee_id: int) -> list[Device]:
    return (
        db.query(Device)
        .filter(Device.employee_id == employee_id)
        .order_by(Device.registered_at.desc())
        .all()
    )


def create_device(
    db: Session,
    *,
    employee_id: int,
    device_fingerprint: str,
    platform: DevicePlatform,
    model: str | None,
    os_version: str | None,
    app_version: str | None,
) -> Device:
    device = Device(
        employee_id=employee_id,
        device_fingerprint=device_fingerprint,
        platform=platform,
        model=model,
        os_version=os_version,
        app_version=app_version,
        is_trusted=False,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def update_device_metadata(
    db: Session,
    device: Device,
    *,
    model: str | None,
    os_version: str | None,
    app_version: str | None,
) -> Device:
    device.model = model
    device.os_version = os_version
    device.app_version = app_version
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def update_device_trust(db: Session, device: Device, is_trusted: bool) -> Device:
    device.is_trusted = is_trusted
    db.add(device)
    db.commit()
    db.refresh(device)
    return device

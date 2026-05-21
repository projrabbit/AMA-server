from __future__ import annotations

import math

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.business import AuditActionType, DevicePlatform, EmployeeStatus
from app.repositories.admin_repository import (
    assign_shift_to_employee,
    create_department,
    create_device,
    create_employee_and_account,
    create_shift,
    deactivate_employee,
    get_department_by_id,
    get_department_by_name,
    get_departments,
    get_device_by_fingerprint_and_employee,
    get_device_by_id,
    get_devices,
    get_devices_for_employee,
    get_employee_by_email,
    get_employee_by_id,
    get_employee_by_phone,
    get_employees,
    get_shift_by_id,
    get_shifts,
    has_shift_conflict,
    update_department_fields,
    update_device_metadata,
    update_device_trust,
    update_employee_fields,
    update_shift_fields,
)
from app.repositories.auth_repository import create_audit_log
from app.schemas.admin import (
    AccountDetail,
    AccountSummary,
    AssignShiftData,
    CreateDepartmentData,
    CreateEmployeeData,
    CreateShiftData,
    DeactivateEmployeeData,
    DepartmentListItem,
    DeviceDetail,
    DeviceListItem,
    DeviceSummary,
    EmployeeDetailData,
    EmployeeInDevice,
    EmployeeListItem,
    RegisterDeviceData,
    ShiftListItem,
    ShiftSummary,
    TrustDeviceData,
    UpdateDepartmentData,
    UpdateEmployeeData,
    UpdateShiftData,
)


def _pagination_meta(page: int, limit: int, total: int) -> dict:
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": math.ceil(total / limit) if limit else 0,
    }


# ── Employee ──────────────────────────────────────────────────────────────────

def list_employees(
    db: Session,
    *,
    department_id: int | None,
    status: EmployeeStatus | None,
    q: str | None,
    page: int,
    limit: int,
) -> tuple[list[EmployeeListItem], dict]:
    skip = (page - 1) * limit
    rows, total = get_employees(db, department_id=department_id, status=status, q=q, skip=skip, limit=limit)
    items = [
        EmployeeListItem(
            employee_id=emp.employee_id,
            department_id=emp.department_id,
            department_name=emp.department.name if emp.department else "",
            full_name=emp.full_name,
            email=emp.email,
            phone=emp.phone,
            position=emp.position,
            hire_date=emp.hire_date,
            status=emp.status,
            account=AccountSummary.model_validate(emp.account) if emp.account else None,
        )
        for emp in rows
    ]
    return items, _pagination_meta(page, limit, total)


def create_employee(
    db: Session,
    actor_account_id: int,
    *,
    full_name: str,
    department_id: int,
    position: str,
    email: str,
    phone: str,
    hire_date,
    role,
    temporary_password: str,
    ip_address: str | None,
) -> CreateEmployeeData:
    if get_department_by_id(db, department_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DEPARTMENT_NOT_FOUND", "message": "Department not found", "details": {}},
        )
    if get_employee_by_email(db, email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "EMAIL_ALREADY_EXISTS", "message": "Email is already in use", "details": {}},
        )
    if get_employee_by_phone(db, phone) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "PHONE_ALREADY_EXISTS", "message": "Phone number is already registered", "details": {}},
        )

    password_hash = get_password_hash(temporary_password)
    employee, account = create_employee_and_account(
        db,
        full_name=full_name,
        department_id=department_id,
        position=position,
        email=email,
        phone=phone,
        hire_date=hire_date,
        role=role,
        password_hash=password_hash,
    )
    create_audit_log(
        db,
        account_id=actor_account_id,
        action_type=AuditActionType.create,
        target_entity="EMPLOYEE",
        target_id=employee.employee_id,
        ip_address=ip_address,
    )
    return CreateEmployeeData(
        employee_id=employee.employee_id,
        account_id=account.account_id,
        username=account.username,
        status=employee.status,
    )


def get_employee_detail(db: Session, employee_id: int) -> EmployeeDetailData:
    employee = get_employee_by_id(db, employee_id)
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "EMPLOYEE_NOT_FOUND", "message": "Employee not found", "details": {}},
        )
    latest_device = employee.devices[-1] if employee.devices else None
    latest_shift = employee.shifts[-1] if employee.shifts else None
    return EmployeeDetailData(
        employee_id=employee.employee_id,
        department_id=employee.department_id,
        department_name=employee.department.name if employee.department else "",
        full_name=employee.full_name,
        email=employee.email,
        phone=employee.phone,
        position=employee.position,
        hire_date=employee.hire_date,
        status=employee.status,
        face_registered=getattr(employee, "face_reference", None) is not None,
        account=AccountDetail.model_validate(employee.account) if employee.account else None,
        device=DeviceSummary.model_validate(latest_device) if latest_device else None,
        shift=ShiftSummary.model_validate(latest_shift) if latest_shift else None,
    )


def update_employee(
    db: Session,
    actor_account_id: int,
    employee_id: int,
    *,
    full_name: str | None,
    department_id: int | None,
    position: str | None,
    email: str | None,
    phone: str | None,
    hire_date,
    employee_status: EmployeeStatus | None,
    ip_address: str | None,
) -> UpdateEmployeeData:
    employee = get_employee_by_id(db, employee_id)
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "EMPLOYEE_NOT_FOUND", "message": "Employee not found", "details": {}},
        )
    if email is not None and email != employee.email:
        existing = get_employee_by_email(db, email)
        if existing is not None and existing.employee_id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "EMAIL_ALREADY_EXISTS", "message": "Email is already in use", "details": {}},
            )
    if phone is not None and phone != employee.phone:
        existing = get_employee_by_phone(db, phone)
        if existing is not None and existing.employee_id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "PHONE_ALREADY_EXISTS", "message": "Phone number is already registered", "details": {}},
            )
    if department_id is not None and department_id != employee.department_id:
        if get_department_by_id(db, department_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "DEPARTMENT_NOT_FOUND", "message": "Department not found", "details": {}},
            )

    fields = {k: v for k, v in {
        "full_name": full_name,
        "department_id": department_id,
        "position": position,
        "email": email,
        "phone": phone,
        "hire_date": hire_date,
        "status": employee_status,
    }.items() if v is not None}

    update_employee_fields(db, employee, **fields)
    create_audit_log(
        db,
        account_id=actor_account_id,
        action_type=AuditActionType.update,
        target_entity="EMPLOYEE",
        target_id=employee_id,
        ip_address=ip_address,
    )
    return UpdateEmployeeData(employee_id=employee_id)


def deactivate_employee_svc(
    db: Session,
    actor_account_id: int,
    employee_id: int,
    ip_address: str | None,
) -> DeactivateEmployeeData:
    employee = get_employee_by_id(db, employee_id)
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "EMPLOYEE_NOT_FOUND", "message": "Employee not found", "details": {}},
        )
    if employee.status == EmployeeStatus.inactive:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "ALREADY_INACTIVE", "message": "Employee is already inactive", "details": {}},
        )
    account = employee.account
    deactivate_employee(db, employee, account)

    create_audit_log(
        db,
        account_id=actor_account_id,
        action_type=AuditActionType.update,
        target_entity="EMPLOYEE",
        target_id=employee_id,
        ip_address=ip_address,
    )
    if account:
        create_audit_log(
            db,
            account_id=actor_account_id,
            action_type=AuditActionType.update,
            target_entity="ACCOUNT",
            target_id=account.account_id,
            ip_address=ip_address,
        )
    return DeactivateEmployeeData(
        employee_id=employee_id,
        status=EmployeeStatus.inactive,
        account_locked=True,
    )


def assign_shift_svc(
    db: Session,
    actor_account_id: int,
    employee_id: int,
    shift_id: int,
    ip_address: str | None,
) -> AssignShiftData:
    employee = get_employee_by_id(db, employee_id)
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "EMPLOYEE_NOT_FOUND", "message": "Employee not found", "details": {}},
        )
    shift = get_shift_by_id(db, shift_id)
    if shift is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SHIFT_NOT_FOUND", "message": "Shift not found", "details": {}},
        )
    assign_shift_to_employee(db, shift, employee_id)
    create_audit_log(
        db,
        account_id=actor_account_id,
        action_type=AuditActionType.update,
        target_entity="SHIFT",
        target_id=shift_id,
        ip_address=ip_address,
    )
    return AssignShiftData(employee_id=employee_id, shift_id=shift_id)


# ── Department ────────────────────────────────────────────────────────────────

def list_departments(
    db: Session,
    *,
    q: str | None,
    page: int,
    limit: int,
) -> tuple[list[DepartmentListItem], dict]:
    skip = (page - 1) * limit
    rows, total = get_departments(db, q=q, skip=skip, limit=limit)
    items = [DepartmentListItem(**row) for row in rows]
    return items, _pagination_meta(page, limit, total)


def create_department_svc(
    db: Session,
    *,
    name: str,
    description: str | None,
    manager_id: int | None,
) -> CreateDepartmentData:
    if manager_id is not None and get_employee_by_id(db, manager_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MANAGER_NOT_FOUND", "message": "Manager employee not found", "details": {}},
        )
    if get_department_by_name(db, name) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "DEPARTMENT_NAME_EXISTS", "message": "Department name already exists", "details": {}},
        )
    dept = create_department(db, name=name, description=description, manager_id=manager_id)
    return CreateDepartmentData(department_id=dept.department_id, name=dept.name)


def update_department_svc(
    db: Session,
    actor_account_id: int,
    department_id: int,
    *,
    name: str | None,
    description: str | None,
    manager_id: int | None,
    ip_address: str | None,
) -> UpdateDepartmentData:
    dept = get_department_by_id(db, department_id)
    if dept is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DEPARTMENT_NOT_FOUND", "message": "Department not found", "details": {}},
        )
    if name is not None and name != dept.name:
        existing = get_department_by_name(db, name)
        if existing is not None and existing.department_id != department_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "DEPARTMENT_NAME_EXISTS", "message": "Department name already exists", "details": {}},
            )

    fields = {k: v for k, v in {"name": name, "description": description, "manager_id": manager_id}.items() if v is not None}
    update_department_fields(db, dept, **fields)
    create_audit_log(
        db,
        account_id=actor_account_id,
        action_type=AuditActionType.update,
        target_entity="DEPARTMENT",
        target_id=department_id,
        ip_address=ip_address,
    )
    return UpdateDepartmentData(department_id=department_id)


# ── Shift ─────────────────────────────────────────────────────────────────────

def list_shifts(
    db: Session,
    *,
    employee_id: int | None,
    page: int,
    limit: int,
) -> tuple[list[ShiftListItem], dict]:
    skip = (page - 1) * limit
    rows, total = get_shifts(db, employee_id=employee_id, skip=skip, limit=limit)
    items = [
        ShiftListItem(
            shift_id=s.shift_id,
            employee_id=s.employee_id,
            employee_name=s.employee.full_name if s.employee else "",
            name=s.name,
            start_time=s.start_time,
            end_time=s.end_time,
            late_tolerance_min=s.late_tolerance_min,
            early_leave_min=s.early_leave_min,
            apply_to_weekends=s.apply_to_weekends,
        )
        for s in rows
    ]
    return items, _pagination_meta(page, limit, total)


def create_shift_svc(
    db: Session,
    actor_account_id: int,
    *,
    employee_id: int,
    name: str,
    start_time,
    end_time,
    late_tolerance_min: int,
    early_leave_min: int,
    apply_to_weekends: bool,
    ip_address: str | None,
) -> CreateShiftData:
    if get_employee_by_id(db, employee_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "EMPLOYEE_NOT_FOUND", "message": "Employee not found", "details": {}},
        )
    if has_shift_conflict(db, employee_id, start_time, end_time):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "SHIFT_TIME_CONFLICT", "message": "Shift time overlaps with an existing shift", "details": {}},
        )
    shift = create_shift(
        db,
        employee_id=employee_id,
        name=name,
        start_time=start_time,
        end_time=end_time,
        late_tolerance_min=late_tolerance_min,
        early_leave_min=early_leave_min,
        apply_to_weekends=apply_to_weekends,
    )
    create_audit_log(
        db,
        account_id=actor_account_id,
        action_type=AuditActionType.create,
        target_entity="SHIFT",
        target_id=shift.shift_id,
        ip_address=ip_address,
    )
    return CreateShiftData(shift_id=shift.shift_id, name=shift.name)


def update_shift_svc(
    db: Session,
    actor_account_id: int,
    shift_id: int,
    *,
    name: str | None,
    start_time,
    end_time,
    late_tolerance_min: int | None,
    early_leave_min: int | None,
    apply_to_weekends: bool | None,
    ip_address: str | None,
) -> UpdateShiftData:
    shift = get_shift_by_id(db, shift_id)
    if shift is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SHIFT_NOT_FOUND", "message": "Shift not found", "details": {}},
        )
    effective_start = start_time if start_time is not None else shift.start_time
    effective_end = end_time if end_time is not None else shift.end_time
    if has_shift_conflict(db, shift.employee_id, effective_start, effective_end, exclude_shift_id=shift_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "SHIFT_TIME_CONFLICT", "message": "Shift time overlaps with an existing shift", "details": {}},
        )
    fields = {k: v for k, v in {
        "name": name,
        "start_time": start_time,
        "end_time": end_time,
        "late_tolerance_min": late_tolerance_min,
        "early_leave_min": early_leave_min,
        "apply_to_weekends": apply_to_weekends,
    }.items() if v is not None}
    update_shift_fields(db, shift, **fields)
    create_audit_log(
        db,
        account_id=actor_account_id,
        action_type=AuditActionType.update,
        target_entity="SHIFT",
        target_id=shift_id,
        ip_address=ip_address,
    )
    return UpdateShiftData(shift_id=shift_id)


# ── Device ────────────────────────────────────────────────────────────────────

def register_device_svc(
    db: Session,
    employee_id: int,
    *,
    device_fingerprint: str,
    platform: DevicePlatform,
    model: str | None,
    os_version: str | None,
    app_version: str | None,
) -> RegisterDeviceData:
    existing = get_device_by_fingerprint_and_employee(db, device_fingerprint, employee_id)
    if existing is not None:
        device = update_device_metadata(db, existing, model=model, os_version=os_version, app_version=app_version)
    else:
        device = create_device(
            db,
            employee_id=employee_id,
            device_fingerprint=device_fingerprint,
            platform=platform,
            model=model,
            os_version=os_version,
            app_version=app_version,
        )
    return RegisterDeviceData(
        device_id=device.device_id,
        employee_id=device.employee_id,
        platform=device.platform,
        model=device.model,
        is_trusted=device.is_trusted,
        registered_at=device.registered_at,
    )


def get_my_devices_svc(db: Session, employee_id: int) -> list[DeviceDetail]:
    devices = get_devices_for_employee(db, employee_id)
    return [DeviceDetail.model_validate(d) for d in devices]


def list_devices_svc(
    db: Session,
    *,
    employee_id: int | None,
    is_trusted: bool | None,
    platform: DevicePlatform | None,
    page: int,
    limit: int,
) -> tuple[list[DeviceListItem], dict]:
    skip = (page - 1) * limit
    rows, total = get_devices(db, employee_id=employee_id, is_trusted=is_trusted, platform=platform, skip=skip, limit=limit)
    items = [
        DeviceListItem(
            device_id=d.device_id,
            employee=EmployeeInDevice(
                employee_id=d.employee.employee_id,
                full_name=d.employee.full_name,
                department_name=d.employee.department.name if d.employee.department else "",
            ),
            device_fingerprint=d.device_fingerprint,
            platform=d.platform,
            model=d.model,
            os_version=d.os_version,
            app_version=d.app_version,
            registered_at=d.registered_at,
            is_trusted=d.is_trusted,
        )
        for d in rows
    ]
    return items, _pagination_meta(page, limit, total)


def trust_device_svc(
    db: Session,
    actor_account_id: int,
    device_id: int,
    is_trusted: bool,
    ip_address: str | None,
) -> TrustDeviceData:
    device = get_device_by_id(db, device_id)
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DEVICE_NOT_FOUND", "message": "Device not found", "details": {}},
        )
    update_device_trust(db, device, is_trusted)
    create_audit_log(
        db,
        account_id=actor_account_id,
        action_type=AuditActionType.update,
        target_entity="DEVICE",
        target_id=device_id,
        ip_address=ip_address,
    )
    return TrustDeviceData(device_id=device_id, is_trusted=is_trusted)

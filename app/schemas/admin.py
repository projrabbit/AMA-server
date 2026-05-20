from __future__ import annotations

from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.models.business import AccountRole, DevicePlatform, EmployeeStatus


# ── Requests ─────────────────────────────────────────────────────────────────

class CreateEmployeeRequest(BaseModel):
    full_name: str
    department_id: int
    position: str
    email: EmailStr
    phone: str
    hire_date: date
    role: AccountRole
    temporary_password: str

    @field_validator("temporary_password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UpdateEmployeeRequest(BaseModel):
    full_name: str | None = None
    department_id: int | None = None
    position: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    hire_date: date | None = None
    status: EmployeeStatus | None = None


class DeactivateEmployeeRequest(BaseModel):
    reason: str | None = None


class AssignShiftRequest(BaseModel):
    shift_id: int


class CreateDepartmentRequest(BaseModel):
    name: str
    description: str | None = None
    manager_id: int | None = None


class UpdateDepartmentRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    manager_id: int | None = None


class CreateShiftRequest(BaseModel):
    employee_id: int
    name: str
    start_time: time
    end_time: time
    late_tolerance_min: int = 0
    early_leave_min: int = 0
    apply_to_weekends: bool = False


class UpdateShiftRequest(BaseModel):
    name: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    late_tolerance_min: int | None = None
    early_leave_min: int | None = None
    apply_to_weekends: bool | None = None


class RegisterDeviceRequest(BaseModel):
    device_fingerprint: str
    platform: DevicePlatform
    model: str | None = None
    os_version: str | None = None
    app_version: str | None = None


class TrustDeviceRequest(BaseModel):
    is_trusted: bool


# ── Sub-objects ───────────────────────────────────────────────────────────────

class AccountSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: int
    username: str
    role: AccountRole
    is_active: bool


class AccountDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: int
    username: str
    role: AccountRole
    last_login_at: datetime | None = None
    is_active: bool


class ShiftSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    shift_id: int
    name: str


class DeviceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: int
    platform: DevicePlatform
    model: str | None = None
    is_trusted: bool


class DeviceDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: int
    device_fingerprint: str
    platform: DevicePlatform
    model: str | None = None
    os_version: str | None = None
    app_version: str | None = None
    registered_at: datetime
    is_trusted: bool


class EmployeeInDevice(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: int
    full_name: str
    department_name: str


# ── Response data objects ─────────────────────────────────────────────────────

class EmployeeListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: int
    department_id: int
    department_name: str
    full_name: str
    email: str
    phone: str | None = None
    position: str | None = None
    hire_date: date | None = None
    status: EmployeeStatus
    account: AccountSummary | None = None


class CreateEmployeeData(BaseModel):
    employee_id: int
    account_id: int
    username: str
    status: EmployeeStatus


class EmployeeDetailData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: int
    department_id: int
    department_name: str
    full_name: str
    email: str
    phone: str | None = None
    position: str | None = None
    hire_date: date | None = None
    status: EmployeeStatus
    face_registered: bool = False
    account: AccountDetail | None = None
    device: DeviceSummary | None = None
    shift: ShiftSummary | None = None


class UpdateEmployeeData(BaseModel):
    employee_id: int
    updated: bool = True


class DeactivateEmployeeData(BaseModel):
    employee_id: int
    status: EmployeeStatus
    account_locked: bool


class AssignShiftData(BaseModel):
    employee_id: int
    shift_id: int
    assigned: bool = True


class DepartmentListItem(BaseModel):
    department_id: int
    name: str
    description: str | None = None
    manager_id: int | None = None
    manager_name: str | None = None
    employee_count: int
    created_at: datetime


class CreateDepartmentData(BaseModel):
    department_id: int
    name: str


class UpdateDepartmentData(BaseModel):
    department_id: int
    updated: bool = True


class ShiftListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    shift_id: int
    employee_id: int
    employee_name: str
    name: str
    start_time: time
    end_time: time
    late_tolerance_min: int
    early_leave_min: int
    apply_to_weekends: bool


class CreateShiftData(BaseModel):
    shift_id: int
    name: str


class UpdateShiftData(BaseModel):
    shift_id: int
    updated: bool = True


class RegisterDeviceData(BaseModel):
    device_id: int
    employee_id: int
    platform: DevicePlatform
    model: str | None = None
    is_trusted: bool
    registered_at: datetime


class TrustDeviceData(BaseModel):
    device_id: int
    is_trusted: bool
    updated: bool = True


class DeviceListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: int
    employee: EmployeeInDevice
    device_fingerprint: str
    platform: DevicePlatform
    model: str | None = None
    os_version: str | None = None
    app_version: str | None = None
    registered_at: datetime
    is_trusted: bool

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator

from app.models.business import AccountRole, EmployeeStatus


# ---------- requests ----------

class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


# ---------- shared sub-objects ----------

class AccountInfo(BaseModel):
    account_id: int
    username: str
    role: AccountRole
    is_active: bool
    last_login_at: datetime | None = None

    model_config = {"from_attributes": True}


class EmployeeInfo(BaseModel):
    employee_id: int
    full_name: str
    email: str
    phone: str | None = None
    position: str | None = None
    department_id: int
    status: EmployeeStatus

    model_config = {"from_attributes": True}


# ---------- response data objects ----------

class LoginData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    account: AccountInfo
    employee: EmployeeInfo


class RefreshData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class MeData(BaseModel):
    account: AccountInfo
    employee: EmployeeInfo


class MessageData(BaseModel):
    message: str

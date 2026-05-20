"""Shared fixtures and app client setup for all tests."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
)
from app.main import app
from app.models.business import AccountRole, EmployeeStatus

# ── shared mock DB session ──────────────────────────────────────────────────
mock_db = MagicMock()


def override_get_db():
    yield mock_db


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app, raise_server_exceptions=True)

# ── test constants ──────────────────────────────────────────────────────────
TEST_PASSWORD = "TestPass@123"
WRONG_PASSWORD = "WrongPassword@999"


# ── model factories (SimpleNamespace so Pydantic from_attributes=True works) -

def make_employee(
    employee_id: int = 1001,
    department_id: int = 1001,
    full_name: str = "Test User",
    email: str = "test@example.com",
    status: EmployeeStatus = EmployeeStatus.active,
) -> SimpleNamespace:
    return SimpleNamespace(
        employee_id=employee_id,
        department_id=department_id,
        full_name=full_name,
        email=email,
        phone="+84901000001",
        position="Developer",
        hire_date=None,
        status=status,
    )


def make_account(
    account_id: int = 1001,
    username: str = "admin@example.com",
    role: AccountRole = AccountRole.admin,
    password: str = TEST_PASSWORD,
    employee_id: int = 1001,
    is_active: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        account_id=account_id,
        employee_id=employee_id,
        username=username,
        password_hash=get_password_hash(password),
        role=role,
        is_active=is_active,
        last_login_at=None,
        audit_logs=[],
        employee=make_employee(employee_id=employee_id, email=username),
    )


# ── account fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def admin_account() -> SimpleNamespace:
    return make_account(
        account_id=1001,
        username="linh.tran@example.com",
        role=AccountRole.admin,
        employee_id=1001,
    )


@pytest.fixture
def employee_account() -> SimpleNamespace:
    return make_account(
        account_id=1002,
        username="minh.nguyen@example.com",
        role=AccountRole.employee,
        employee_id=1002,
    )


@pytest.fixture
def hr_account() -> SimpleNamespace:
    return make_account(
        account_id=1003,
        username="hoa.pham@example.com",
        role=AccountRole.hr,
        employee_id=1003,
    )


@pytest.fixture
def locked_account() -> SimpleNamespace:
    return make_account(
        account_id=1005,
        username="locked@example.com",
        role=AccountRole.employee,
        employee_id=1005,
        is_active=False,
    )


# ── token fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def admin_tokens(admin_account: SimpleNamespace) -> dict:
    data = {"sub": str(admin_account.account_id), "role": admin_account.role.value}
    access_token, access_jti = create_access_token(data)
    refresh_token, refresh_jti = create_refresh_token(data)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "access_jti": access_jti,
        "refresh_jti": refresh_jti,
    }


@pytest.fixture
def employee_tokens(employee_account: SimpleNamespace) -> dict:
    data = {"sub": str(employee_account.account_id), "role": employee_account.role.value}
    access_token, access_jti = create_access_token(data)
    refresh_token, refresh_jti = create_refresh_token(data)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "access_jti": access_jti,
        "refresh_jti": refresh_jti,
    }


@pytest.fixture
def admin_auth_headers(admin_tokens: dict) -> dict:
    return {"Authorization": f"Bearer {admin_tokens['access_token']}"}


@pytest.fixture
def employee_auth_headers(employee_tokens: dict) -> dict:
    return {"Authorization": f"Bearer {employee_tokens['access_token']}"}

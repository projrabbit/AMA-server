"""Fixtures shared across admin module tests."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, time, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.models.business import AccountRole, DevicePlatform, EmployeeStatus
from tests.conftest import make_account, make_employee


def make_department(
    department_id: int = 10,
    name: str = "Engineering",
    description: str | None = "Software engineering team",
    manager_id: int | None = None,
    manager_name: str | None = None,
    employee_count: int = 5,
) -> dict:
    return {
        "department_id": department_id,
        "name": name,
        "description": description,
        "manager_id": manager_id,
        "manager_name": manager_name,
        "employee_count": employee_count,
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }


def make_dept_orm(
    department_id: int = 10,
    name: str = "Engineering",
    description: str | None = None,
    manager_id: int | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        department_id=department_id,
        name=name,
        description=description,
        manager_id=manager_id,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def make_shift(
    shift_id: int = 20,
    employee_id: int = 1001,
    employee_name: str = "Test User",
    name: str = "Morning Shift",
    start_time: time = time(8, 0),
    end_time: time = time(17, 0),
    late_tolerance_min: int = 10,
    early_leave_min: int = 10,
    apply_to_weekends: bool = False,
) -> SimpleNamespace:
    emp = SimpleNamespace(employee_id=employee_id, full_name=employee_name)
    return SimpleNamespace(
        shift_id=shift_id,
        employee_id=employee_id,
        employee=emp,
        name=name,
        start_time=start_time,
        end_time=end_time,
        late_tolerance_min=late_tolerance_min,
        early_leave_min=early_leave_min,
        apply_to_weekends=apply_to_weekends,
    )


def make_device(
    device_id: int = 30,
    employee_id: int = 1001,
    device_fingerprint: str = "fp-abc-123",
    platform: DevicePlatform = DevicePlatform.android,
    model: str | None = "Pixel 8",
    os_version: str | None = "Android 15",
    app_version: str | None = "1.0.0",
    is_trusted: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        device_id=device_id,
        employee_id=employee_id,
        device_fingerprint=device_fingerprint,
        platform=platform,
        model=model,
        os_version=os_version,
        app_version=app_version,
        registered_at=datetime(2026, 5, 20, 7, 30, tzinfo=timezone.utc),
        is_trusted=is_trusted,
        employee=SimpleNamespace(
            employee_id=employee_id,
            full_name="Test User",
            department=SimpleNamespace(name="Engineering"),
        ),
    )


def make_employee_full(
    employee_id: int = 1001,
    department_id: int = 10,
    department_name: str = "Engineering",
    full_name: str = "Test User",
    email: str = "test@example.com",
    status: EmployeeStatus = EmployeeStatus.active,
    devices: list | None = None,
    shifts: list | None = None,
    account_id: int = 1001,
) -> SimpleNamespace:
    department = SimpleNamespace(department_id=department_id, name=department_name)
    account = make_account(account_id=account_id, username=email, employee_id=employee_id)
    employee = make_employee(employee_id=employee_id, department_id=department_id, email=email, status=status)
    employee.department = department
    employee.account = account
    employee.devices = devices if devices is not None else []
    employee.shifts = shifts if shifts is not None else []
    return employee


# ── Pytest fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def dept_dict() -> dict:
    return make_department()


@pytest.fixture
def dept_orm() -> SimpleNamespace:
    return make_dept_orm()


@pytest.fixture
def shift_ns() -> SimpleNamespace:
    return make_shift()


@pytest.fixture
def device_ns() -> SimpleNamespace:
    return make_device()


@pytest.fixture
def employee_full() -> SimpleNamespace:
    return make_employee_full()


@pytest.fixture
def hr_auth_headers(hr_account) -> dict:
    from app.core.security import create_access_token
    data = {"sub": str(hr_account.account_id), "role": hr_account.role.value}
    token, _ = create_access_token(data)
    return {"Authorization": f"Bearer {token}"}


# ── Role-aware auth fixtures (patch the dependency so role guard passes) ──────

_DEP_PATCH = "app.api.dependencies.get_account_by_id"


@pytest.fixture
def as_hr(hr_account, hr_auth_headers):
    """HR auth headers with dependency patched — use for success-path tests."""
    with patch(_DEP_PATCH, return_value=hr_account):
        yield hr_auth_headers


@pytest.fixture
def as_admin(admin_account, admin_auth_headers):
    """Admin auth headers with dependency patched — use for success-path tests."""
    with patch(_DEP_PATCH, return_value=admin_account):
        yield admin_auth_headers


@pytest.fixture
def as_employee(employee_account, employee_auth_headers):
    """Employee auth headers with dependency patched — use for success-path tests."""
    with patch(_DEP_PATCH, return_value=employee_account):
        yield employee_auth_headers

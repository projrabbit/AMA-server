"""Shared fixtures for face module tests."""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from tests.conftest import make_account, make_employee

_DEP_PATCH = "app.api.dependencies.get_account_by_id"


def make_face_reference(
    face_id: int = 1,
    employee_id: int = 1001,
    face_object_key: str = "faces/employee_1001/reference_2026-05-22.jpg",
    registered_at: datetime | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        face_id=face_id,
        employee_id=employee_id,
        face_object_key=face_object_key,
        registered_at=registered_at or datetime(2026, 5, 22, 9, 0, tzinfo=timezone.utc),
    )


def make_employee_with_face(
    employee_id: int = 1001,
    face_reference: SimpleNamespace | None = None,
) -> SimpleNamespace:
    emp = make_employee(employee_id=employee_id)
    emp.face_reference = face_reference
    return emp


@pytest.fixture
def face_ref() -> SimpleNamespace:
    return make_face_reference()


@pytest.fixture
def hr_auth_headers(hr_account) -> dict:
    from app.core.security import create_access_token
    data = {"sub": str(hr_account.account_id), "role": hr_account.role.value}
    token, _ = create_access_token(data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def as_hr(hr_account, hr_auth_headers):
    with patch(_DEP_PATCH, return_value=hr_account):
        yield hr_auth_headers


@pytest.fixture
def as_admin(admin_account, admin_auth_headers):
    with patch(_DEP_PATCH, return_value=admin_account):
        yield admin_auth_headers


@pytest.fixture
def as_employee(employee_account, employee_auth_headers):
    with patch(_DEP_PATCH, return_value=employee_account):
        yield employee_auth_headers

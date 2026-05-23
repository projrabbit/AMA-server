"""Shared fixtures for fraud detection module tests."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from tests.conftest import make_account, make_employee

_DEP_PATCH = "app.api.dependencies.get_account_by_id"


def make_department(department_id: int = 1001, name: str = "Engineering") -> SimpleNamespace:
    return SimpleNamespace(department_id=department_id, name=name)


def make_device(
    device_id: int = 501,
    employee_id: int = 1001,
    device_fingerprint: str = "abc-device-fp",
    platform: str = "android",
    model: str = "Pixel 8",
    is_trusted: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        device_id=device_id,
        employee_id=employee_id,
        device_fingerprint=device_fingerprint,
        platform=SimpleNamespace(value=platform),
        model=model,
        is_trusted=is_trusted,
    )


def make_attendance_record(
    record_id: int = 1001,
    employee_id: int = 1001,
    device_id: int = 501,
    type_: str = "checkin",
    status_: str = "rejected",
    rejection_reason: str | None = "mock_location",
    timestamp: datetime | None = None,
    latitude: Decimal = Decimal("10.772123"),
    longitude: Decimal = Decimal("106.657890"),
    altitude: Decimal = Decimal("12.5"),
    gps_accuracy: Decimal = Decimal("5.2"),
    employee: SimpleNamespace | None = None,
    device: SimpleNamespace | None = None,
) -> SimpleNamespace:
    emp = employee or make_employee_with_dept(employee_id=employee_id)
    dev = device or make_device(device_id=device_id, employee_id=employee_id)
    return SimpleNamespace(
        record_id=record_id,
        employee_id=employee_id,
        device_id=device_id,
        type=SimpleNamespace(value=type_),
        status=SimpleNamespace(value=status_),
        rejection_reason=rejection_reason,
        timestamp=timestamp or datetime(2026, 5, 20, 8, 5, tzinfo=timezone.utc),
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        gps_accuracy=gps_accuracy,
        employee=emp,
        device=dev,
    )


def make_employee_with_dept(
    employee_id: int = 1001,
    full_name: str = "Nguyen Van A",
    department: SimpleNamespace | None = None,
) -> SimpleNamespace:
    dept = department or make_department()
    emp = make_employee(employee_id=employee_id, full_name=full_name)
    emp.department = dept
    return emp


def make_fraud_record(
    fraud_id: int = 502,
    record_id: int = 1001,
    mock_location_detected: bool = True,
    gps_spoofing_detected: bool = False,
    buddy_punch_suspected: bool = False,
    unknown_device: bool = False,
    face_mismatch_detected: bool = False,
    liveness_failed: bool = False,
    confidence_score: Decimal = Decimal("60.0"),
    reason: str | None = "mock_location",
    checked_at: datetime | None = None,
    attendance_record: SimpleNamespace | None = None,
) -> SimpleNamespace:
    rec = attendance_record or make_attendance_record(record_id=record_id)
    return SimpleNamespace(
        fraud_id=fraud_id,
        record_id=record_id,
        mock_location_detected=mock_location_detected,
        gps_spoofing_detected=gps_spoofing_detected,
        buddy_punch_suspected=buddy_punch_suspected,
        unknown_device=unknown_device,
        face_mismatch_detected=face_mismatch_detected,
        liveness_failed=liveness_failed,
        confidence_score=confidence_score,
        reason=reason,
        checked_at=checked_at or datetime(2026, 5, 20, 8, 5, 1, tzinfo=timezone.utc),
        attendance_record=rec,
    )


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

"""Shared fixtures for attendance module tests."""
from __future__ import annotations

from datetime import date, datetime, time, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from tests.conftest import make_account

_DEP_PATCH = "app.api.dependencies.get_account_by_id"


# ── Model factories ────────────────────────────────────────────────────────────

def make_shift(
    shift_id: int = 10,
    employee_id: int = 1002,
    name: str = "Morning Shift",
    start_time: time = time(8, 0),
    end_time: time = time(17, 0),
    late_tolerance_min: int = 0,
    early_leave_min: int = 0,
) -> SimpleNamespace:
    return SimpleNamespace(
        shift_id=shift_id,
        employee_id=employee_id,
        name=name,
        start_time=start_time,
        end_time=end_time,
        late_tolerance_min=late_tolerance_min,
        early_leave_min=early_leave_min,
        apply_to_weekends=False,
    )


def make_device(
    device_id: int = 20,
    employee_id: int = 1002,
    device_fingerprint: str = "test-device-fp",
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
        os_version=None,
        app_version=None,
        is_trusted=is_trusted,
        registered_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def make_fraud_detection(
    fraud_id: int = 501,
    record_id: int = 1001,
    confidence_score: float = 96.5,
) -> SimpleNamespace:
    return SimpleNamespace(
        fraud_id=fraud_id,
        record_id=record_id,
        mock_location_detected=False,
        gps_spoofing_detected=False,
        buddy_punch_suspected=False,
        unknown_device=False,
        face_mismatch_detected=False,
        liveness_failed=False,
        confidence_score=Decimal(str(confidence_score)),
        reason=None,
        checked_at=datetime(2026, 5, 20, 1, 2, tzinfo=timezone.utc),
    )


def make_attendance_record(
    record_id: int = 1001,
    employee_id: int = 1002,
    type_: str = "checkin",
    status: str = "approved",
    is_late: bool = False,
    is_early_leave: bool = False,
    worked_minutes: int | None = None,
    rejection_reason: str | None = None,
    matched_checkin_record_id: int | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        record_id=record_id,
        employee_id=employee_id,
        device_id=20,
        shift_id=10,
        geofence_rule_id=7,
        type=SimpleNamespace(value=type_),
        timestamp=datetime(2026, 5, 20, 1, 2, 10, tzinfo=timezone.utc),
        latitude=Decimal("10.772123"),
        longitude=Decimal("106.657890"),
        altitude=Decimal("12.5"),
        gps_accuracy=Decimal("5.2"),
        status=SimpleNamespace(value=status),
        rejection_reason=rejection_reason,
        is_late=is_late,
        is_early_leave=is_early_leave,
        face_image_object_key="attendance/employee_1002/checkin_xxx.jpg",
        matched_checkin_record_id=matched_checkin_record_id,
        worked_minutes=worked_minutes,
        approved_by_account_id=None,
        approved_at=None,
    )


# ── Auth fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def hr_auth_headers(hr_account) -> dict:
    from app.core.security import create_access_token
    data = {"sub": str(hr_account.account_id), "role": hr_account.role.value}
    token, _ = create_access_token(data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def as_employee(employee_account, employee_auth_headers):
    with patch(_DEP_PATCH, return_value=employee_account):
        yield employee_auth_headers


@pytest.fixture
def as_hr(hr_account, hr_auth_headers):
    with patch(_DEP_PATCH, return_value=hr_account):
        yield hr_auth_headers


@pytest.fixture
def as_admin(admin_account, admin_auth_headers):
    with patch(_DEP_PATCH, return_value=admin_account):
        yield admin_auth_headers

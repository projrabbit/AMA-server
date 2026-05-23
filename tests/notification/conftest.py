"""Shared fixtures for notification module tests."""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from tests.conftest import make_account

_DEP_PATCH = "app.api.dependencies.get_account_by_id"


def make_notification(
    notification_id: int = 301,
    account_id: int = 1001,
    type_: str = "checkin_approved",
    title: str = "Check-in Approved",
    body: str = "Your check-in was approved.",
    is_read: bool = False,
    created_at: datetime | None = None,
    meta: dict | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        notification_id=notification_id,
        account_id=account_id,
        type=SimpleNamespace(value=type_),
        title=title,
        body=body,
        is_read=is_read,
        created_at=created_at or datetime(2026, 5, 20, 8, 2, 15, tzinfo=timezone.utc),
        meta=meta or {"record_id": 1001},
    )


def make_preference(
    preference_id: int = 1,
    account_id: int = 1001,
    push_enabled: bool = True,
    in_app_enabled: bool = True,
    notify_checkin_approved: bool = True,
    notify_checkin_rejected: bool = True,
    notify_checkout_approved: bool = True,
    notify_checkout_rejected: bool = True,
    notify_device_trusted: bool = True,
    notify_exception_flagged: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        preference_id=preference_id,
        account_id=account_id,
        push_enabled=push_enabled,
        in_app_enabled=in_app_enabled,
        notify_checkin_approved=notify_checkin_approved,
        notify_checkin_rejected=notify_checkin_rejected,
        notify_checkout_approved=notify_checkout_approved,
        notify_checkout_rejected=notify_checkout_rejected,
        notify_device_trusted=notify_device_trusted,
        notify_exception_flagged=notify_exception_flagged,
    )


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

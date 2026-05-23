"""Shared fixtures for report module tests."""
from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest

from tests.conftest import make_account
from app.models.business import AccountRole

_DEP_PATCH = "app.api.dependencies.get_account_by_id"


def make_active_location(employee_id: int = 10) -> "dict":
    from app.schemas.report import ActiveLocationItem
    return ActiveLocationItem(
        employee_id=employee_id,
        full_name="Nguyen Van A",
        department_name="Engineering",
        latitude=10.772123,
        longitude=106.657890,
        altitude=12.5,
        building_id=1,
        building_name="Main Office",
        floor_id=2,
        floor_name="Floor 2",
        last_checkin_at=datetime(2026, 5, 20, 8, 2, 10, tzinfo=timezone.utc),
    )


def make_realtime_location(employee_id: int = 10) -> "dict":
    from app.schemas.report import RealtimeLocationItem
    return RealtimeLocationItem(
        employee_id=employee_id,
        full_name="Nguyen Van A",
        department_id=2,
        department_name="Engineering",
        record_id=1001,
        latitude=10.772123,
        longitude=106.657890,
        altitude=12.5,
        gps_accuracy=5.2,
        building_id=1,
        building_name="Main Office",
        floor_id=2,
        floor_name="Floor 2",
        arcgis_layer_id="arcgis-layer-001",
        checked_in_at=datetime(2026, 5, 20, 8, 2, 10, tzinfo=timezone.utc),
    )


def make_report_data():
    from app.schemas.report import (
        AttendanceReportData,
        ReportDayDetail,
        ReportEmployeeSummary,
        ReportSummary,
    )
    return AttendanceReportData(
        range={"from": "2026-05-01", "to": "2026-05-20"},
        summary=ReportSummary(
            employee_count=1,
            total_work_days=14,
            total_work_minutes=6720,
            late_count=1,
            early_leave_count=0,
            absent_count=6,
            rejected_count=0,
        ),
        employees=[
            ReportEmployeeSummary(
                employee_id=10,
                full_name="Nguyen Van A",
                department_name="Engineering",
                work_days=14,
                total_work_minutes=6720,
                late_count=1,
                early_leave_count=0,
                absent_count=6,
                rejected_count=0,
            )
        ],
        details=[
            ReportDayDetail(
                date=date(2026, 5, 20),
                employee_id=10,
                full_name="Nguyen Van A",
                department_name="Engineering",
                checkin_at=datetime(2026, 5, 20, 8, 2, 10, tzinfo=timezone.utc),
                checkout_at=datetime(2026, 5, 20, 17, 1, 30, tzinfo=timezone.utc),
                worked_minutes=539,
                is_late=False,
                is_early_leave=False,
                status="completed",
            )
        ],
    )


# ── Auth fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def manager_account():
    return make_account(account_id=1004, username="mgr@example.com",
                        role=AccountRole.manager, employee_id=1004)


@pytest.fixture
def manager_auth_headers(manager_account):
    from app.core.security import create_access_token
    token, _ = create_access_token({"sub": str(manager_account.account_id),
                                    "role": manager_account.role.value})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def hr_auth_headers(hr_account):
    from app.core.security import create_access_token
    token, _ = create_access_token({"sub": str(hr_account.account_id),
                                    "role": hr_account.role.value})
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
def as_manager(manager_account, manager_auth_headers):
    with patch(_DEP_PATCH, return_value=manager_account):
        yield manager_auth_headers


@pytest.fixture
def as_employee(employee_account, employee_auth_headers):
    with patch(_DEP_PATCH, return_value=employee_account):
        yield employee_auth_headers

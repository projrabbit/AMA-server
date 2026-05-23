"""Tests for GET /dashboard/summary."""
from __future__ import annotations

from datetime import date
from unittest.mock import patch

from tests.conftest import client
from tests.report.conftest import make_active_location

_PATCH = "app.services.report_service.get_dashboard_summary"


def _make_summary(target_date: date = date(2026, 5, 20), locations=None):
    from app.schemas.report import DashboardSummaryData
    return DashboardSummaryData(
        date=target_date,
        total_employees=120,
        checked_in_today=96,
        on_time_count=88,
        late_count=8,
        early_leave_count=2,
        absent_count=24,
        fraud_alerts_today=3,
        on_time_rate=73.33,
        active_locations=locations or [],
    )


def _get(headers: dict, params: dict | None = None):
    return client.get("/api/v1/dashboard/summary", headers=headers, params=params or {})


class TestDashboardSuccess:
    def test_200_manager_role(self, as_manager):
        with patch(_PATCH, return_value=_make_summary()):
            resp = _get(as_manager)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_200_hr_role(self, as_hr):
        with patch(_PATCH, return_value=_make_summary()):
            resp = _get(as_hr)
        assert resp.status_code == 200

    def test_200_admin_role(self, as_admin):
        with patch(_PATCH, return_value=_make_summary()):
            resp = _get(as_admin)
        assert resp.status_code == 200

    def test_kpi_fields_present(self, as_hr):
        with patch(_PATCH, return_value=_make_summary()):
            resp = _get(as_hr)
        data = resp.json()["data"]
        assert data["total_employees"] == 120
        assert data["checked_in_today"] == 96
        assert data["on_time_count"] == 88
        assert data["late_count"] == 8
        assert data["absent_count"] == 24
        assert data["fraud_alerts_today"] == 3
        assert data["on_time_rate"] == 73.33

    def test_refresh_interval_in_meta(self, as_hr):
        with patch(_PATCH, return_value=_make_summary()):
            resp = _get(as_hr)
        assert resp.json()["meta"]["refresh_interval_seconds"] == 60

    def test_active_locations_list(self, as_hr):
        loc = make_active_location()
        with patch(_PATCH, return_value=_make_summary(locations=[loc])):
            resp = _get(as_hr)
        data = resp.json()["data"]
        assert len(data["active_locations"]) == 1
        assert data["active_locations"][0]["employee_id"] == 10
        assert data["active_locations"][0]["building_name"] == "Main Office"

    def test_date_param_forwarded(self, as_hr):
        with patch(_PATCH, return_value=_make_summary()) as mock_fn:
            _get(as_hr, params={"date": "2026-05-15"})
        mock_fn.assert_called_once()
        _, called_date = mock_fn.call_args.args
        assert called_date == date(2026, 5, 15)

    def test_defaults_to_today_when_no_date(self, as_hr):
        with patch(_PATCH, return_value=_make_summary()) as mock_fn:
            _get(as_hr)
        mock_fn.assert_called_once()


class TestDashboardAuth:
    def test_401_no_token(self):
        resp = _get({})
        assert resp.status_code == 401

    def test_403_employee_role(self, as_employee):
        resp = _get(as_employee)
        assert resp.status_code == 403

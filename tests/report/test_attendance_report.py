"""Tests for GET /reports/attendance."""
from __future__ import annotations

from unittest.mock import patch

from tests.conftest import client
from tests.report.conftest import make_report_data

_PATCH = "app.services.report_service.get_attendance_report"


def _get(headers: dict, params: dict | None = None):
    return client.get(
        "/api/v1/reports/attendance",
        headers=headers,
        params=params or {"from": "2026-05-01", "to": "2026-05-20"},
    )


class TestAttendanceReportSuccess:
    def test_200_manager_role(self, as_manager):
        with patch(_PATCH, return_value=make_report_data()):
            resp = _get(as_manager)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_200_hr_role(self, as_hr):
        with patch(_PATCH, return_value=make_report_data()):
            resp = _get(as_hr)
        assert resp.status_code == 200

    def test_range_in_response(self, as_hr):
        with patch(_PATCH, return_value=make_report_data()):
            resp = _get(as_hr)
        data = resp.json()["data"]
        assert data["range"]["from"] == "2026-05-01"
        assert data["range"]["to"] == "2026-05-20"

    def test_summary_fields_present(self, as_hr):
        with patch(_PATCH, return_value=make_report_data()):
            resp = _get(as_hr)
        summary = resp.json()["data"]["summary"]
        assert "employee_count" in summary
        assert "total_work_days" in summary
        assert "late_count" in summary
        assert "absent_count" in summary
        assert "rejected_count" in summary

    def test_employees_list_present(self, as_hr):
        with patch(_PATCH, return_value=make_report_data()):
            resp = _get(as_hr)
        employees = resp.json()["data"]["employees"]
        assert len(employees) == 1
        assert employees[0]["employee_id"] == 10
        assert employees[0]["department_name"] == "Engineering"

    def test_details_list_present(self, as_hr):
        with patch(_PATCH, return_value=make_report_data()):
            resp = _get(as_hr)
        details = resp.json()["data"]["details"]
        assert len(details) == 1
        assert details[0]["worked_minutes"] == 539
        assert details[0]["status"] == "completed"

    def test_filters_forwarded(self, as_hr):
        with patch(_PATCH, return_value=make_report_data()) as mock_fn:
            _get(as_hr, params={"from": "2026-05-01", "to": "2026-05-20",
                                "department_id": "2", "employee_id": "10"})
        kwargs = mock_fn.call_args.kwargs
        assert kwargs["department_id"] == 2
        assert kwargs["employee_id"] == 10


class TestAttendanceReportErrors:
    def test_422_missing_from_date(self, as_hr):
        resp = client.get("/api/v1/reports/attendance", headers=as_hr, params={"to": "2026-05-20"})
        assert resp.status_code == 422

    def test_422_missing_to_date(self, as_hr):
        resp = client.get("/api/v1/reports/attendance", headers=as_hr, params={"from": "2026-05-01"})
        assert resp.status_code == 422


class TestAttendanceReportAuth:
    def test_401_no_token(self):
        resp = _get({})
        assert resp.status_code == 401

    def test_403_employee_role(self, as_employee):
        resp = _get(as_employee)
        assert resp.status_code == 403

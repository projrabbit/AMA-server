"""Tests for GET /attendance/history."""
from __future__ import annotations

from unittest.mock import patch

from fastapi import HTTPException

from tests.conftest import client

_PATCH_HISTORY = "app.services.attendance_service.list_history"


def _get(headers: dict, params: dict | None = None):
    return client.get(
        "/api/v1/attendance/history",
        headers=headers,
        params=params or {"from": "2026-05-01", "to": "2026-05-20"},
    )


def _make_result(days=None, total=0):
    from app.schemas.attendance import AttendanceHistoryData, AttendanceSummary, HistoryEmployeeInfo
    data = AttendanceHistoryData(
        employee=HistoryEmployeeInfo(employee_id=1002, full_name="Nguyen Van A"),
        range={"from": "2026-05-01", "to": "2026-05-20"},
        summary=AttendanceSummary(
            work_days=total, total_work_minutes=total * 480,
            late_count=0, early_leave_count=0, rejected_count=0,
        ),
        days=days or [],
    )
    return data, total, 1, 20, max(1, (total + 19) // 20)


class TestHistorySuccess:
    def test_200_with_items(self, as_employee):
        from app.schemas.attendance import AttendanceDayRecord
        from datetime import date

        day = AttendanceDayRecord(
            date=date(2026, 5, 20), checkin=None, checkout=None,
            building_name="Main Office", floor_name="Floor 2",
            worked_minutes=539, status="completed",
        )
        result = _make_result(days=[day], total=1)
        with patch(_PATCH_HISTORY, return_value=result):
            resp = _get(as_employee)

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["employee"]["employee_id"] == 1002
        assert len(body["data"]["days"]) == 1
        assert body["meta"]["total"] == 1

    def test_200_empty_range(self, as_employee):
        with patch(_PATCH_HISTORY, return_value=_make_result()):
            resp = _get(as_employee)
        assert resp.status_code == 200
        assert resp.json()["data"]["days"] == []

    def test_hr_can_view_any_employee(self, as_hr):
        with patch(_PATCH_HISTORY, return_value=_make_result()):
            resp = _get(as_hr, params={"from": "2026-05-01", "to": "2026-05-20", "employee_id": 1002})
        assert resp.status_code == 200

    def test_pagination_params_forwarded(self, as_employee):
        with patch(_PATCH_HISTORY, return_value=_make_result()) as mock_hist:
            _get(as_employee, params={"from": "2026-05-01", "to": "2026-05-20", "page": "2", "limit": "10"})
        kwargs = mock_hist.call_args.kwargs
        assert kwargs["page"] == 2
        assert kwargs["limit"] == 10

    def test_summary_fields_present(self, as_employee):
        with patch(_PATCH_HISTORY, return_value=_make_result()):
            resp = _get(as_employee)
        summary = resp.json()["data"]["summary"]
        assert "work_days" in summary
        assert "late_count" in summary
        assert "rejected_count" in summary


class TestHistoryErrors:
    def test_403_employee_views_other(self, as_employee):
        with patch(
            _PATCH_HISTORY,
            side_effect=HTTPException(
                status_code=403,
                detail={"code": "FORBIDDEN", "message": "Employees can only view their own history", "details": {}},
            ),
        ):
            resp = _get(as_employee, params={"from": "2026-05-01", "to": "2026-05-20", "employee_id": 9999})
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    def test_404_employee_not_found(self, as_hr):
        with patch(
            _PATCH_HISTORY,
            side_effect=HTTPException(
                status_code=404,
                detail={"code": "EMPLOYEE_NOT_FOUND", "message": "Employee not found", "details": {}},
            ),
        ):
            resp = _get(as_hr, params={"from": "2026-05-01", "to": "2026-05-20", "employee_id": 9999})
        assert resp.status_code == 404

    def test_422_missing_from_date(self, as_employee):
        resp = client.get("/api/v1/attendance/history", headers=as_employee, params={"to": "2026-05-20"})
        assert resp.status_code == 422


class TestHistoryAuth:
    def test_401_when_no_token(self):
        resp = _get({})
        assert resp.status_code == 401

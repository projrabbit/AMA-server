"""Tests for GET /attendance/today-status."""
from __future__ import annotations

from unittest.mock import patch

from tests.conftest import client

_PATCH_TODAY = "app.services.attendance_service.get_today_status"


class TestTodayStatusSuccess:
    def test_200_no_checkin_yet(self, as_employee):
        from app.schemas.attendance import ShiftInfo, TodayStatusData
        from datetime import date, time

        result = TodayStatusData(
            date=date(2026, 5, 20),
            employee_id=1002,
            can_check_in=True,
            can_check_out=False,
            current_shift=ShiftInfo(shift_id=10, name="Morning Shift", start_time=time(8, 0), end_time=time(17, 0)),
            latest_checkin=None,
            latest_checkout=None,
        )
        with patch(_PATCH_TODAY, return_value=result):
            resp = client.get("/api/v1/attendance/today-status", headers=as_employee)

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["can_check_in"] is True
        assert data["can_check_out"] is False
        assert data["latest_checkin"] is None

    def test_200_checked_in_awaiting_checkout(self, as_employee):
        from app.schemas.attendance import TodayRecordInfo, TodayStatusData
        from datetime import datetime, timezone

        from datetime import date
        result = TodayStatusData(
            date=date(2026, 5, 20),
            employee_id=1002,
            can_check_in=False,
            can_check_out=True,
            current_shift=None,
            latest_checkin=TodayRecordInfo(
                record_id=1001,
                timestamp=datetime(2026, 5, 20, 1, 2, 10, tzinfo=timezone.utc),
                status="approved",
            ),
            latest_checkout=None,
        )
        with patch(_PATCH_TODAY, return_value=result):
            resp = client.get("/api/v1/attendance/today-status", headers=as_employee)

        data = resp.json()["data"]
        assert data["can_check_in"] is False
        assert data["can_check_out"] is True
        assert data["latest_checkin"]["record_id"] == 1001

    def test_200_shift_included(self, as_employee):
        from app.schemas.attendance import ShiftInfo, TodayStatusData
        from datetime import date, time

        result = TodayStatusData(
            date=date(2026, 5, 20),
            employee_id=1002,
            can_check_in=True,
            can_check_out=False,
            current_shift=ShiftInfo(shift_id=10, name="Night Shift", start_time=time(22, 0), end_time=time(6, 0)),
            latest_checkin=None,
            latest_checkout=None,
        )
        with patch(_PATCH_TODAY, return_value=result):
            resp = client.get("/api/v1/attendance/today-status", headers=as_employee)

        data = resp.json()["data"]
        assert data["current_shift"]["name"] == "Night Shift"


class TestTodayStatusAuth:
    def test_401_when_no_token(self):
        resp = client.get("/api/v1/attendance/today-status", headers={})
        assert resp.status_code == 401

    def test_403_when_hr_role(self, as_hr):
        resp = client.get("/api/v1/attendance/today-status", headers=as_hr)
        assert resp.status_code == 403

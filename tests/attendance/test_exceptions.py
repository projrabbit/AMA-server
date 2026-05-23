"""Tests for GET /attendance/exceptions."""
from __future__ import annotations

from unittest.mock import patch

from tests.conftest import client

_PATCH_EXCEPTIONS = "app.services.attendance_service.list_exceptions"


def _get(headers: dict, params: dict | None = None):
    return client.get("/api/v1/attendance/exceptions", headers=headers, params=params or {})


def _make_item(record_id: int = 1002):
    from app.schemas.attendance import ExceptionEmployeeInfo, ExceptionFraudFlags, ExceptionItem
    from datetime import datetime, timezone
    return ExceptionItem(
        record_id=record_id,
        employee=ExceptionEmployeeInfo(employee_id=1002, full_name="Nguyen Van A", department_name="Engineering"),
        type="checkin",
        timestamp=datetime(2026, 5, 20, 1, 5, tzinfo=timezone.utc),
        status="rejected",
        rejection_reason="outside_geofence",
        is_late=False,
        is_early_leave=False,
        fraud_flags=ExceptionFraudFlags(
            mock_location_detected=False, gps_spoofing_detected=False,
            buddy_punch_suspected=False, unknown_device=False,
            face_mismatch_detected=False, liveness_failed=False,
        ),
    )


class TestExceptionsSuccess:
    def test_200_with_items(self, as_hr):
        item = _make_item()
        with patch(_PATCH_EXCEPTIONS, return_value=([item], 1)):
            resp = _get(as_hr)

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert len(body["data"]) == 1
        assert body["data"][0]["record_id"] == 1002
        assert body["meta"]["total"] == 1

    def test_200_empty_list(self, as_admin):
        with patch(_PATCH_EXCEPTIONS, return_value=([], 0)):
            resp = _get(as_admin)
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_filters_forwarded(self, as_hr):
        with patch(_PATCH_EXCEPTIONS, return_value=([], 0)) as mock_exc:
            _get(as_hr, params={"status": "rejected", "department_id": "2", "page": "2"})
        kwargs = mock_exc.call_args.kwargs
        assert kwargs["status_filter"] == "rejected"
        assert kwargs["department_id"] == 2
        assert kwargs["page"] == 2

    def test_pagination_meta_present(self, as_hr):
        with patch(_PATCH_EXCEPTIONS, return_value=([], 0)):
            resp = _get(as_hr)
        meta = resp.json()["meta"]
        assert "total" in meta
        assert "total_pages" in meta


class TestExceptionsAuth:
    def test_401_when_no_token(self):
        resp = _get({})
        assert resp.status_code == 401

    def test_403_when_employee_role(self, as_employee):
        resp = _get(as_employee)
        assert resp.status_code == 403

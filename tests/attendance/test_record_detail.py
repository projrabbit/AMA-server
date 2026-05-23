"""Tests for GET /attendance/{record_id}."""
from __future__ import annotations

from unittest.mock import patch

from fastapi import HTTPException

from tests.conftest import client

_PATCH_DETAIL = "app.services.attendance_service.get_record_detail"


def _get(record_id: int, headers: dict):
    return client.get(f"/api/v1/attendance/{record_id}", headers=headers)


def _make_detail(record_id: int = 1002):
    from app.schemas.attendance import (
        AttendanceRecordDetailData,
        RecordDeviceInfo,
        RecordEmployeeInfo,
        RecordFraudDetection,
        RecordShiftInfo,
    )
    from datetime import datetime, time, timezone
    from decimal import Decimal
    return AttendanceRecordDetailData(
        record_id=record_id,
        employee=RecordEmployeeInfo(employee_id=1002, full_name="Nguyen Van A", department_id=2, department_name="Engineering"),
        device=RecordDeviceInfo(device_id=12, device_fingerprint="abc-fp", platform="android", model="Pixel 8", is_trusted=True),
        shift=RecordShiftInfo(shift_id=10, name="Morning Shift", start_time=time(8, 0), end_time=time(17, 0)),
        geofence_rule_id=None,
        type="checkin",
        timestamp=datetime(2026, 5, 20, 8, 5, tzinfo=timezone.utc),
        latitude=Decimal("10.700000"),
        longitude=Decimal("106.600000"),
        altitude=Decimal("10.0"),
        gps_accuracy=Decimal("4.8"),
        status="rejected",
        rejection_reason="outside_geofence",
        is_late=False,
        is_early_leave=False,
        fraud_detection=RecordFraudDetection(
            fraud_id=502, mock_location_detected=False, gps_spoofing_detected=False,
            buddy_punch_suspected=False, unknown_device=False, face_mismatch_detected=False,
            liveness_failed=False, reason=None, confidence_score=92.0,
            checked_at=datetime(2026, 5, 20, 8, 5, 1, tzinfo=timezone.utc),
        ),
    )


class TestRecordDetailSuccess:
    def test_200_with_full_data(self, as_hr):
        detail = _make_detail()
        with patch(_PATCH_DETAIL, return_value=detail):
            resp = _get(1002, as_hr)

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["record_id"] == 1002
        assert data["employee"]["full_name"] == "Nguyen Van A"
        assert data["device"]["platform"] == "android"
        assert data["fraud_detection"]["confidence_score"] == 92.0

    def test_admin_can_access(self, as_admin):
        with patch(_PATCH_DETAIL, return_value=_make_detail()):
            resp = _get(1002, as_admin)
        assert resp.status_code == 200


class TestRecordDetailErrors:
    def test_404_when_not_found(self, as_hr):
        with patch(
            _PATCH_DETAIL,
            side_effect=HTTPException(
                status_code=404,
                detail={"code": "RECORD_NOT_FOUND", "message": "Attendance record not found", "details": {}},
            ),
        ):
            resp = _get(9999, as_hr)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "RECORD_NOT_FOUND"


class TestRecordDetailAuth:
    def test_401_when_no_token(self):
        resp = _get(1001, {})
        assert resp.status_code == 401

    def test_403_when_employee_role(self, as_employee):
        resp = _get(1001, as_employee)
        assert resp.status_code == 403

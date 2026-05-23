"""Tests for POST /attendance/check-out."""
from __future__ import annotations

from unittest.mock import patch

from fastapi import HTTPException

from tests.conftest import client

_PATCH_CHECKOUT = "app.services.attendance_service.check_out"

_VALID_FORM = {
    "device_fingerprint": "test-device-fp",
    "platform": "android",
    "latitude": "10.772123",
    "longitude": "106.657890",
    "altitude": "12.4",
    "gps_accuracy": "5.0",
    "liveness_signals": '{"blink_detected": true, "head_pose_changed": true, "challenge_passed": true}',
}
_VALID_FILE = {"face_image": ("test.jpg", b"FAKE_IMAGE_BYTES", "image/jpeg")}


def _post(headers: dict):
    return client.post(
        "/api/v1/attendance/check-out",
        data=_VALID_FORM,
        files=_VALID_FILE,
        headers=headers,
    )


class TestCheckOutSuccess:
    def test_201_approved_with_worked_minutes(self, as_employee):
        from app.schemas.attendance import CheckInData, FraudResultInfo, LocationInfo, ShiftInfo
        from datetime import datetime, time, timezone

        result = CheckInData(
            record_id=1010, employee_id=1002, type="checkout", status="approved",
            rejection_reason=None, message="Check-out approved",
            timestamp=datetime(2026, 5, 20, 10, 1, 30, tzinfo=timezone.utc),
            is_late=False, is_early_leave=False,
            matched_checkin_record_id=1001, worked_minutes=539,
            shift=ShiftInfo(shift_id=10, name="Morning Shift", start_time=time(8, 0), end_time=time(17, 0)),
            location=LocationInfo(
                latitude="10.772123", longitude="106.657890", altitude="12.4",
                gps_accuracy="5.0", building_id=1, building_name="Main Office",
                floor_id=2, floor_name="Floor 2", geofence_rule_id=7,
            ),
            fraud_result=FraudResultInfo(
                fraud_id=510, mock_location_detected=False, gps_spoofing_detected=False,
                buddy_punch_suspected=False, unknown_device=False,
                face_mismatch_detected=False, liveness_failed=False, confidence_score=95.0,
            ),
        )
        with patch(_PATCH_CHECKOUT, return_value=result):
            resp = _post(as_employee)

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["type"] == "checkout"
        assert data["matched_checkin_record_id"] == 1001
        assert data["worked_minutes"] == 539

    def test_409_when_no_active_checkin(self, as_employee):
        with patch(
            _PATCH_CHECKOUT,
            side_effect=HTTPException(
                status_code=409,
                detail={"code": "FAILED_NO_CHECKIN", "message": "No approved check-in found for today", "details": {}},
            ),
        ):
            resp = _post(as_employee)
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "FAILED_NO_CHECKIN"

    def test_400_gps_accuracy_too_low(self, as_employee):
        with patch(
            _PATCH_CHECKOUT,
            side_effect=HTTPException(
                status_code=400,
                detail={"code": "GPS_ACCURACY_TOO_LOW", "message": "GPS accuracy exceeds the allowed threshold", "details": {}},
            ),
        ):
            resp = _post(as_employee)
        assert resp.status_code == 400


class TestCheckOutAuth:
    def test_401_when_no_token(self):
        resp = _post({})
        assert resp.status_code == 401

    def test_403_when_hr_role(self, as_hr):
        resp = _post(as_hr)
        assert resp.status_code == 403

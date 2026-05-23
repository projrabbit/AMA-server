"""Tests for POST /attendance/check-in."""
from __future__ import annotations

from unittest.mock import patch

from fastapi import HTTPException

from tests.conftest import client

_PATCH_CHECKIN = "app.services.attendance_service.check_in"

_VALID_FORM = {
    "device_fingerprint": "test-device-fp",
    "platform": "android",
    "latitude": "10.772123",
    "longitude": "106.657890",
    "altitude": "12.5",
    "gps_accuracy": "5.2",
    "liveness_signals": '{"blink_detected": true, "head_pose_changed": true, "challenge_passed": true}',
}
_VALID_FILE = {"face_image": ("test.jpg", b"FAKE_IMAGE_BYTES", "image/jpeg")}


def _post(headers: dict, form: dict | None = None, files: dict | None = None):
    return client.post(
        "/api/v1/attendance/check-in",
        data=form if form is not None else _VALID_FORM,
        files=files if files is not None else _VALID_FILE,
        headers=headers,
    )


class TestCheckInSuccess:
    def test_201_approved(self, as_employee):
        from app.schemas.attendance import CheckInData, FraudResultInfo, LocationInfo, ShiftInfo
        from datetime import datetime, time, timezone

        result = CheckInData(
            record_id=1001,
            employee_id=1002,
            type="checkin",
            status="approved",
            rejection_reason=None,
            message="Check-in approved",
            timestamp=datetime(2026, 5, 20, 8, 2, 10, tzinfo=timezone.utc),
            is_late=False,
            is_early_leave=False,
            shift=ShiftInfo(shift_id=10, name="Morning Shift", start_time=time(8, 0), end_time=time(17, 0)),
            location=LocationInfo(
                latitude="10.772123", longitude="106.657890", altitude="12.5",
                gps_accuracy="5.2", building_id=1, building_name="Main Office",
                floor_id=2, floor_name="Floor 2", geofence_rule_id=7,
            ),
            fraud_result=FraudResultInfo(
                fraud_id=501, mock_location_detected=False, gps_spoofing_detected=False,
                buddy_punch_suspected=False, unknown_device=False,
                face_mismatch_detected=False, liveness_failed=False, confidence_score=96.5,
            ),
        )
        with patch(_PATCH_CHECKIN, return_value=result):
            resp = _post(as_employee)

        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["record_id"] == 1001
        assert body["data"]["status"] == "approved"
        assert body["data"]["fraud_result"]["fraud_id"] == 501

    def test_201_rejected_outside_geofence(self, as_employee):
        from app.schemas.attendance import CheckInData, FraudResultInfo, LocationInfo
        from datetime import datetime, timezone

        result = CheckInData(
            record_id=1002, employee_id=1002, type="checkin", status="rejected",
            rejection_reason="outside_geofence",
            message="Check-in rejected: outside_geofence",
            timestamp=datetime(2026, 5, 20, 8, 5, tzinfo=timezone.utc),
            is_late=False, is_early_leave=False, shift=None,
            location=LocationInfo(
                latitude="10.700000", longitude="106.600000", altitude="10.0",
                gps_accuracy="4.8", building_id=None, building_name=None,
                floor_id=None, floor_name=None, geofence_rule_id=None,
            ),
            fraud_result=FraudResultInfo(
                fraud_id=502, mock_location_detected=False, gps_spoofing_detected=False,
                buddy_punch_suspected=False, unknown_device=False,
                face_mismatch_detected=False, liveness_failed=False, confidence_score=92.0,
            ),
        )
        with patch(_PATCH_CHECKIN, return_value=result):
            resp = _post(as_employee)

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["status"] == "rejected"
        assert data["rejection_reason"] == "outside_geofence"

    def test_service_receives_form_fields(self, as_employee):
        from app.schemas.attendance import CheckInData, FraudResultInfo, LocationInfo
        from datetime import datetime, timezone

        result = CheckInData(
            record_id=1001, employee_id=1002, type="checkin", status="approved",
            rejection_reason=None, message="Check-in approved",
            timestamp=datetime(2026, 5, 20, 8, 2, tzinfo=timezone.utc),
            is_late=False, is_early_leave=False, shift=None,
            location=LocationInfo(
                latitude="10.77", longitude="106.65", altitude="12.0",
                gps_accuracy="5.0", building_id=None, building_name=None,
                floor_id=None, floor_name=None, geofence_rule_id=None,
            ),
            fraud_result=FraudResultInfo(
                fraud_id=501, mock_location_detected=False, gps_spoofing_detected=False,
                buddy_punch_suspected=False, unknown_device=False,
                face_mismatch_detected=False, liveness_failed=False, confidence_score=100.0,
            ),
        )
        with patch(_PATCH_CHECKIN, return_value=result) as mock_ci:
            _post(as_employee)

        kwargs = mock_ci.call_args.kwargs
        assert kwargs["device_fingerprint"] == "test-device-fp"
        assert kwargs["platform_str"] == "android"
        assert kwargs["latitude"] == 10.772123
        assert kwargs["gps_accuracy"] == 5.2


class TestCheckInErrors:
    def test_400_gps_accuracy_too_low(self, as_employee):
        with patch(
            _PATCH_CHECKIN,
            side_effect=HTTPException(
                status_code=400,
                detail={"code": "GPS_ACCURACY_TOO_LOW", "message": "GPS accuracy exceeds the allowed threshold", "details": {}},
            ),
        ):
            resp = _post(as_employee)
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "GPS_ACCURACY_TOO_LOW"

    def test_403_employee_mismatch(self, as_employee):
        with patch(
            _PATCH_CHECKIN,
            side_effect=HTTPException(
                status_code=403,
                detail={"code": "EMPLOYEE_MISMATCH", "message": "Provided employee_id does not match the token", "details": {}},
            ),
        ):
            resp = _post(as_employee)
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "EMPLOYEE_MISMATCH"

    def test_409_already_checked_in(self, as_employee):
        with patch(
            _PATCH_CHECKIN,
            side_effect=HTTPException(
                status_code=409,
                detail={"code": "ALREADY_CHECKED_IN", "message": "Employee already has an active check-in today", "details": {}},
            ),
        ):
            resp = _post(as_employee)
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "ALREADY_CHECKED_IN"

    def test_422_missing_required_field(self, as_employee):
        incomplete = {k: v for k, v in _VALID_FORM.items() if k != "device_fingerprint"}
        resp = _post(as_employee, form=incomplete)
        assert resp.status_code == 422

    def test_422_missing_face_image(self, as_employee):
        resp = client.post(
            "/api/v1/attendance/check-in",
            data=_VALID_FORM,
            headers=as_employee,
        )
        assert resp.status_code == 422


class TestCheckInAuth:
    def test_401_when_no_token(self):
        resp = _post({})
        assert resp.status_code == 401

    def test_403_when_hr_role(self, as_hr):
        resp = _post(as_hr)
        assert resp.status_code == 403

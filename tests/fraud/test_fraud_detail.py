"""Tests for GET /fraud/records/{fraud_id}."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

from fastapi import HTTPException

from tests.conftest import client
from tests.fraud.conftest import (
    make_attendance_record,
    make_department,
    make_device,
    make_employee_with_dept,
    make_fraud_record,
)

_PATCH_DETAIL = "app.services.fraud_service.get_fraud_record_detail"


def _get(fraud_id: int, headers: dict):
    return client.get(f"/api/v1/fraud/records/{fraud_id}", headers=headers)


def _make_detail_data():
    from app.schemas.fraud import (
        FraudAttendanceInfo,
        FraudDeviceInfo,
        FraudEmployeeInfo,
        FraudRecordDetailData,
    )

    return FraudRecordDetailData(
        fraud_id=502,
        record_id=1001,
        employee=FraudEmployeeInfo(employee_id=1001, full_name="Nguyen Van A", department_name="Engineering"),
        attendance=FraudAttendanceInfo(
            type="checkin",
            timestamp=datetime(2026, 5, 20, 8, 5, tzinfo=timezone.utc),
            status="rejected",
            rejection_reason="mock_location",
            latitude=Decimal("10.700000"),
            longitude=Decimal("106.600000"),
            altitude=Decimal("10.0"),
            gps_accuracy=Decimal("4.8"),
        ),
        device=FraudDeviceInfo(
            device_id=501,
            device_fingerprint="abc-device-fp",
            platform="android",
            model="Pixel 8",
            is_trusted=True,
        ),
        mock_location_detected=True,
        gps_spoofing_detected=False,
        buddy_punch_suspected=False,
        unknown_device=False,
        face_mismatch_detected=False,
        liveness_failed=False,
        confidence_score=60.0,
        reason="mock_location",
        checked_at=datetime(2026, 5, 20, 8, 5, 1, tzinfo=timezone.utc),
    )


class TestFraudRecordDetailSuccess:
    def test_hr_gets_200_with_full_detail(self, as_hr):
        detail = _make_detail_data()
        with patch(_PATCH_DETAIL, return_value=detail):
            resp = _get(502, as_hr)

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["fraud_id"] == 502
        assert data["record_id"] == 1001
        assert data["employee"]["full_name"] == "Nguyen Van A"
        assert data["employee"]["department_name"] == "Engineering"
        assert data["attendance"]["type"] == "checkin"
        assert data["attendance"]["status"] == "rejected"
        assert data["device"]["platform"] == "android"
        assert data["mock_location_detected"] is True
        assert data["confidence_score"] == 60.0
        assert data["reason"] == "mock_location"

    def test_admin_gets_200(self, as_admin):
        detail = _make_detail_data()
        with patch(_PATCH_DETAIL, return_value=detail):
            resp = _get(502, as_admin)

        assert resp.status_code == 200

    def test_correct_fraud_id_passed_to_service(self, as_hr):
        detail = _make_detail_data()
        with patch(_PATCH_DETAIL, return_value=detail) as mock_detail:
            _get(999, as_hr)
        mock_detail.assert_called_once()
        assert mock_detail.call_args.kwargs["fraud_id"] == 999


class TestFraudRecordDetailErrors:
    def test_404_when_fraud_record_not_found(self, as_hr):
        with patch(
            _PATCH_DETAIL,
            side_effect=HTTPException(
                status_code=404,
                detail={"code": "FRAUD_NOT_FOUND", "message": "Fraud record not found", "details": {}},
            ),
        ):
            resp = _get(9999, as_hr)

        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "FRAUD_NOT_FOUND"


class TestFraudRecordDetailAuth:
    def test_401_when_no_token(self):
        resp = _get(502, {})
        assert resp.status_code == 401

    def test_403_when_employee_role(self, as_employee):
        resp = _get(502, as_employee)
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

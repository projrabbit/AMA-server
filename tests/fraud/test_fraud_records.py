"""Tests for GET /fraud/records."""
from __future__ import annotations

from unittest.mock import patch

from tests.conftest import client
from tests.fraud.conftest import make_fraud_record

_PATCH_LIST = "app.services.fraud_service.list_fraud_records"


def _get(headers: dict, params: dict | None = None):
    return client.get("/api/v1/fraud/records", headers=headers, params=params or {})


class TestListFraudRecordsSuccess:
    def test_hr_gets_200_with_records(self, as_hr):
        from app.schemas.fraud import FraudEmployeeInfo, FraudRecordItem
        from datetime import datetime, timezone
        from decimal import Decimal

        item = FraudRecordItem(
            fraud_id=502,
            record_id=1001,
            employee=FraudEmployeeInfo(employee_id=1001, full_name="Nguyen Van A", department_name="Engineering"),
            attendance_type="checkin",
            attendance_timestamp=datetime(2026, 5, 20, 8, 5, tzinfo=timezone.utc),
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
        with patch(_PATCH_LIST, return_value=([item], 1)):
            resp = _get(as_hr)

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert len(body["data"]) == 1
        assert body["data"][0]["fraud_id"] == 502
        assert body["data"][0]["mock_location_detected"] is True
        assert body["meta"]["total"] == 1

    def test_admin_gets_200(self, as_admin):
        with patch(_PATCH_LIST, return_value=([], 0)):
            resp = _get(as_admin)

        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_pagination_meta_is_present(self, as_hr):
        with patch(_PATCH_LIST, return_value=([], 45)):
            resp = _get(as_hr, params={"page": 2, "limit": 20})

        meta = resp.json()["meta"]
        assert meta["page"] == 2
        assert meta["limit"] == 20
        assert meta["total"] == 45
        assert meta["total_pages"] == 3

    def test_filter_by_employee_id_passed_to_service(self, as_hr):
        with patch(_PATCH_LIST, return_value=([], 0)) as mock_list:
            _get(as_hr, params={"employee_id": 99})
        call_kwargs = mock_list.call_args.kwargs
        assert call_kwargs["employee_id"] == 99

    def test_filter_by_mock_location_passed_to_service(self, as_hr):
        with patch(_PATCH_LIST, return_value=([], 0)) as mock_list:
            _get(as_hr, params={"mock_location": "true"})
        call_kwargs = mock_list.call_args.kwargs
        assert call_kwargs["mock_location"] is True

    def test_filter_by_confidence_score_range(self, as_hr):
        with patch(_PATCH_LIST, return_value=([], 0)) as mock_list:
            _get(as_hr, params={"min_confidence_score": 40.0, "max_confidence_score": 80.0})
        call_kwargs = mock_list.call_args.kwargs
        assert call_kwargs["min_confidence_score"] == 40.0
        assert call_kwargs["max_confidence_score"] == 80.0


class TestListFraudRecordsAuth:
    def test_401_when_no_token(self):
        resp = _get({})
        assert resp.status_code == 401

    def test_403_when_employee_role(self, as_employee):
        resp = _get(as_employee)
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

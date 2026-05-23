"""Tests for PUT /attendance/{record_id}/approve."""
from __future__ import annotations

from unittest.mock import patch

from fastapi import HTTPException

from tests.conftest import client

_PATCH_APPROVE = "app.services.attendance_service.approve_attendance_record"


def _put(record_id: int, headers: dict, body: dict | None = None):
    return client.put(
        f"/api/v1/attendance/{record_id}/approve",
        headers=headers,
        json=body if body is not None else {},
    )


def _make_approve_data(record_id: int = 1002):
    from app.schemas.attendance import ApproveData
    from datetime import datetime, timezone
    return ApproveData(
        record_id=record_id,
        status="approved",
        rejection_reason=None,
        approved_by_account_id=1001,
        approved_at=datetime(2026, 5, 20, 9, 0, tzinfo=timezone.utc),
    )


class TestApproveSuccess:
    def test_200_with_approve_data(self, as_hr):
        result = _make_approve_data()
        with patch(_PATCH_APPROVE, return_value=result):
            resp = _put(1002, as_hr)

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["record_id"] == 1002
        assert data["status"] == "approved"
        assert data["rejection_reason"] is None
        assert data["approved_by_account_id"] == 1001

    def test_admin_can_approve(self, as_admin):
        with patch(_PATCH_APPROVE, return_value=_make_approve_data()):
            resp = _put(1002, as_admin)
        assert resp.status_code == 200

    def test_note_accepted_in_body(self, as_hr):
        with patch(_PATCH_APPROVE, return_value=_make_approve_data()) as mock_appr:
            _put(1002, as_hr, body={"note": "Verified by HR"})
        assert mock_appr.called


class TestApproveErrors:
    def test_404_when_not_found(self, as_hr):
        with patch(
            _PATCH_APPROVE,
            side_effect=HTTPException(
                status_code=404,
                detail={"code": "RECORD_NOT_FOUND", "message": "Attendance record not found", "details": {}},
            ),
        ):
            resp = _put(9999, as_hr)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "RECORD_NOT_FOUND"

    def test_409_already_approved(self, as_hr):
        with patch(
            _PATCH_APPROVE,
            side_effect=HTTPException(
                status_code=409,
                detail={"code": "ALREADY_APPROVED", "message": "Record is already approved", "details": {}},
            ),
        ):
            resp = _put(1001, as_hr)
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "ALREADY_APPROVED"


class TestApproveAuth:
    def test_401_when_no_token(self):
        resp = _put(1002, {})
        assert resp.status_code == 401

    def test_403_when_employee_role(self, as_employee):
        resp = _put(1002, as_employee)
        assert resp.status_code == 403

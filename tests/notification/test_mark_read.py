"""Tests for PUT /notifications/{notification_id}/read."""
from __future__ import annotations

from unittest.mock import patch

from fastapi import HTTPException

from tests.conftest import client

_PATCH_MARK = "app.services.notification_service.mark_read"


def _put(notification_id: int, headers: dict):
    return client.put(f"/api/v1/notifications/{notification_id}/read", headers=headers)


class TestMarkReadSuccess:
    def test_returns_200_with_is_read_true(self, as_employee):
        from app.schemas.notification import MarkReadData

        result = MarkReadData(notification_id=301, is_read=True)
        with patch(_PATCH_MARK, return_value=result):
            resp = _put(301, as_employee)

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["notification_id"] == 301
        assert body["data"]["is_read"] is True

    def test_correct_id_passed_to_service(self, as_hr):
        from app.schemas.notification import MarkReadData

        result = MarkReadData(notification_id=999, is_read=True)
        with patch(_PATCH_MARK, return_value=result) as mock_mark:
            _put(999, as_hr)
        assert mock_mark.call_args.kwargs["notification_id"] == 999

    def test_hr_can_mark_own_notification(self, as_hr):
        from app.schemas.notification import MarkReadData

        result = MarkReadData(notification_id=301, is_read=True)
        with patch(_PATCH_MARK, return_value=result):
            resp = _put(301, as_hr)
        assert resp.status_code == 200


class TestMarkReadErrors:
    def test_404_when_notification_not_found(self, as_employee):
        with patch(
            _PATCH_MARK,
            side_effect=HTTPException(
                status_code=404,
                detail={"code": "NOTIFICATION_NOT_FOUND", "message": "Notification not found", "details": {}},
            ),
        ):
            resp = _put(9999, as_employee)

        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NOTIFICATION_NOT_FOUND"

    def test_403_when_wrong_owner(self, as_employee):
        with patch(
            _PATCH_MARK,
            side_effect=HTTPException(
                status_code=403,
                detail={"code": "FORBIDDEN", "message": "Notification belongs to a different account", "details": {}},
            ),
        ):
            resp = _put(302, as_employee)

        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"


class TestMarkReadAuth:
    def test_401_when_no_token(self):
        resp = _put(301, {})
        assert resp.status_code == 401

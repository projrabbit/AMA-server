"""Tests for PUT /notifications/read-all."""
from __future__ import annotations

from unittest.mock import patch

from tests.conftest import client

_PATCH_MARK_ALL = "app.services.notification_service.mark_all_notifications_read"


def _put(headers: dict):
    return client.put("/api/v1/notifications/read-all", headers=headers)


class TestMarkAllReadSuccess:
    def test_returns_200_with_marked_count(self, as_employee):
        from app.schemas.notification import MarkAllReadData

        result = MarkAllReadData(marked_count=5)
        with patch(_PATCH_MARK_ALL, return_value=result):
            resp = _put(as_employee)

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["marked_count"] == 5

    def test_returns_zero_when_nothing_unread(self, as_hr):
        from app.schemas.notification import MarkAllReadData

        result = MarkAllReadData(marked_count=0)
        with patch(_PATCH_MARK_ALL, return_value=result):
            resp = _put(as_hr)

        assert resp.status_code == 200
        assert resp.json()["data"]["marked_count"] == 0

    def test_account_id_passed_to_service(self, as_employee, employee_account):
        from app.schemas.notification import MarkAllReadData

        result = MarkAllReadData(marked_count=2)
        with patch(_PATCH_MARK_ALL, return_value=result) as mock_mark:
            _put(as_employee)
        assert mock_mark.call_args.kwargs["account_id"] == employee_account.account_id


class TestMarkAllReadAuth:
    def test_401_when_no_token(self):
        resp = _put({})
        assert resp.status_code == 401

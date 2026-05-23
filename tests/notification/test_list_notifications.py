"""Tests for GET /notifications."""
from __future__ import annotations

from unittest.mock import patch

from tests.conftest import client
from tests.notification.conftest import make_notification

_PATCH_LIST = "app.services.notification_service.list_notifications"

_NOTIF_1 = make_notification(notification_id=301, is_read=False)
_NOTIF_2 = make_notification(notification_id=302, is_read=True, type_="checkin_rejected")


def _get(headers: dict, params: dict | None = None):
    return client.get("/api/v1/notifications", headers=headers, params=params or {})


class TestListNotificationsSuccess:
    def test_employee_gets_200_with_items(self, as_employee):
        from app.schemas.notification import NotificationItem
        from datetime import datetime, timezone

        item = NotificationItem(
            notification_id=301,
            type="checkin_approved",
            title="Check-in Approved",
            body="Approved.",
            is_read=False,
            created_at=datetime(2026, 5, 20, 8, 2, tzinfo=timezone.utc),
            meta={"record_id": 1001},
        )
        with patch(_PATCH_LIST, return_value=([item], 1, 1)):
            resp = _get(as_employee)

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert len(body["data"]) == 1
        assert body["data"][0]["notification_id"] == 301
        assert body["data"][0]["is_read"] is False

    def test_meta_includes_unread_count(self, as_hr):
        from app.schemas.notification import NotificationItem
        from datetime import datetime, timezone

        item = NotificationItem(
            notification_id=301,
            type="checkin_approved",
            title="T",
            body="B",
            is_read=False,
            created_at=datetime(2026, 5, 20, 8, 0, tzinfo=timezone.utc),
            meta=None,
        )
        with patch(_PATCH_LIST, return_value=([item], 5, 3)):
            resp = _get(as_hr)

        meta = resp.json()["meta"]
        assert meta["total"] == 5
        assert meta["unread_count"] == 3
        assert meta["total_pages"] == 1

    def test_admin_gets_200(self, as_admin):
        with patch(_PATCH_LIST, return_value=([], 0, 0)):
            resp = _get(as_admin)
        assert resp.status_code == 200

    def test_pagination_params_forwarded(self, as_employee):
        with patch(_PATCH_LIST, return_value=([], 0, 0)) as mock_list:
            _get(as_employee, params={"page": 2, "limit": 10})
        kwargs = mock_list.call_args.kwargs
        assert kwargs["page"] == 2
        assert kwargs["limit"] == 10

    def test_is_read_filter_forwarded(self, as_employee):
        with patch(_PATCH_LIST, return_value=([], 0, 0)) as mock_list:
            _get(as_employee, params={"is_read": "false"})
        kwargs = mock_list.call_args.kwargs
        assert kwargs["is_read"] is False

    def test_type_filter_forwarded(self, as_employee):
        with patch(_PATCH_LIST, return_value=([], 0, 0)) as mock_list:
            _get(as_employee, params={"type": "checkin_approved"})
        kwargs = mock_list.call_args.kwargs
        assert kwargs["type_"].value == "checkin_approved"

    def test_empty_list_returns_200(self, as_employee):
        with patch(_PATCH_LIST, return_value=([], 0, 0)):
            resp = _get(as_employee)
        assert resp.status_code == 200
        assert resp.json()["data"] == []


class TestListNotificationsAuth:
    def test_401_when_no_token(self):
        resp = _get({})
        assert resp.status_code == 401

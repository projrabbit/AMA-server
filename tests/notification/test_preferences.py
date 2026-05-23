"""Tests for GET /notifications/preferences and PUT /notifications/preferences."""
from __future__ import annotations

from unittest.mock import patch

from tests.conftest import client
from tests.notification.conftest import make_preference

_PATCH_GET = "app.services.notification_service.get_preferences"
_PATCH_UPDATE = "app.services.notification_service.update_notification_preferences"

_DEFAULT_PREFS_BODY = {
    "push_enabled": True,
    "in_app_enabled": True,
    "notify_checkin_approved": True,
    "notify_checkin_rejected": True,
    "notify_checkout_approved": False,
    "notify_checkout_rejected": True,
    "notify_device_trusted": True,
    "notify_exception_flagged": False,
}


class TestGetPreferencesSuccess:
    def test_returns_200_with_all_fields(self, as_employee):
        from app.schemas.notification import NotificationPreferenceData

        result = NotificationPreferenceData(
            account_id=1002,
            push_enabled=True,
            in_app_enabled=True,
            notify_checkin_approved=True,
            notify_checkin_rejected=True,
            notify_checkout_approved=True,
            notify_checkout_rejected=True,
            notify_device_trusted=True,
            notify_exception_flagged=True,
        )
        with patch(_PATCH_GET, return_value=result):
            resp = client.get("/api/v1/notifications/preferences", headers=as_employee)

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["account_id"] == 1002
        assert data["push_enabled"] is True
        assert "notify_checkin_approved" in data

    def test_admin_gets_200(self, as_admin):
        from app.schemas.notification import NotificationPreferenceData

        result = NotificationPreferenceData(
            account_id=1001, push_enabled=True, in_app_enabled=True,
            notify_checkin_approved=True, notify_checkin_rejected=True,
            notify_checkout_approved=True, notify_checkout_rejected=True,
            notify_device_trusted=True, notify_exception_flagged=True,
        )
        with patch(_PATCH_GET, return_value=result):
            resp = client.get("/api/v1/notifications/preferences", headers=as_admin)
        assert resp.status_code == 200


class TestGetPreferencesAuth:
    def test_401_when_no_token(self):
        resp = client.get("/api/v1/notifications/preferences", headers={})
        assert resp.status_code == 401


class TestUpdatePreferencesSuccess:
    def test_returns_200_updated_true(self, as_employee):
        from app.schemas.notification import UpdatePreferencesData

        result = UpdatePreferencesData(updated=True)
        with patch(_PATCH_UPDATE, return_value=result):
            resp = client.put(
                "/api/v1/notifications/preferences",
                headers=as_employee,
                json=_DEFAULT_PREFS_BODY,
            )

        assert resp.status_code == 200
        assert resp.json()["data"]["updated"] is True

    def test_request_body_forwarded_to_service(self, as_employee):
        from app.schemas.notification import UpdatePreferencesData

        result = UpdatePreferencesData(updated=True)
        with patch(_PATCH_UPDATE, return_value=result) as mock_upd:
            client.put(
                "/api/v1/notifications/preferences",
                headers=as_employee,
                json=_DEFAULT_PREFS_BODY,
            )
        data_arg = mock_upd.call_args.kwargs["data"]
        assert data_arg.push_enabled is True
        assert data_arg.notify_checkout_approved is False
        assert data_arg.notify_exception_flagged is False

    def test_422_when_missing_required_field(self, as_employee):
        incomplete = {k: v for k, v in _DEFAULT_PREFS_BODY.items() if k != "push_enabled"}
        resp = client.put(
            "/api/v1/notifications/preferences",
            headers=as_employee,
            json=incomplete,
        )
        assert resp.status_code == 422


class TestUpdatePreferencesAuth:
    def test_401_when_no_token(self):
        resp = client.put(
            "/api/v1/notifications/preferences",
            headers={},
            json=_DEFAULT_PREFS_BODY,
        )
        assert resp.status_code == 401

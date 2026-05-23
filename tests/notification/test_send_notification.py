"""Tests for POST /internal/notifications/send."""
from __future__ import annotations

from unittest.mock import patch

from tests.conftest import client

_PATCH_SEND = "app.services.notification_service.send_notifications"

_VALID_PAYLOAD = {
    "account_ids": [1001, 1002],
    "type": "checkin_approved",
    "title": "Check-in Approved",
    "body": "Your check-in was approved.",
    "meta": {"record_id": 1001},
}


def _post(payload: dict):
    return client.post("/api/v1/internal/notifications/send", json=payload)


class TestSendNotificationSuccess:
    def test_returns_200_with_sent_and_failed_counts(self):
        from app.schemas.notification import SendNotificationData

        result = SendNotificationData(sent_count=2, failed_count=0)
        with patch(_PATCH_SEND, return_value=result):
            resp = _post(_VALID_PAYLOAD)

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["sent_count"] == 2
        assert body["data"]["failed_count"] == 0

    def test_failed_count_reflects_unknown_accounts(self):
        from app.schemas.notification import SendNotificationData

        result = SendNotificationData(sent_count=1, failed_count=1)
        with patch(_PATCH_SEND, return_value=result):
            resp = _post(_VALID_PAYLOAD)

        assert resp.status_code == 200
        assert resp.json()["data"]["failed_count"] == 1

    def test_no_auth_required(self):
        from app.schemas.notification import SendNotificationData

        result = SendNotificationData(sent_count=1, failed_count=0)
        with patch(_PATCH_SEND, return_value=result):
            resp = _post({**_VALID_PAYLOAD, "account_ids": [1001]})
        assert resp.status_code == 200

    def test_payload_forwarded_to_service(self):
        from app.schemas.notification import SendNotificationData

        result = SendNotificationData(sent_count=2, failed_count=0)
        with patch(_PATCH_SEND, return_value=result) as mock_send:
            _post(_VALID_PAYLOAD)

        payload_arg = mock_send.call_args.kwargs["payload"]
        assert payload_arg.account_ids == [1001, 1002]
        assert payload_arg.type.value == "checkin_approved"
        assert payload_arg.title == "Check-in Approved"


class TestSendNotificationValidation:
    def test_422_when_invalid_type(self):
        bad = {**_VALID_PAYLOAD, "type": "nonexistent_type"}
        resp = _post(bad)
        assert resp.status_code == 422

    def test_422_when_missing_required_fields(self):
        resp = _post({"account_ids": [1001]})
        assert resp.status_code == 422

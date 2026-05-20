"""Tests for POST /auth/login."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import TEST_PASSWORD, WRONG_PASSWORD, client

LOGIN_URL = "/api/v1/auth/login"

_PATCHES = (
    "app.services.auth_service.get_account_by_username",
    "app.services.auth_service.update_last_login",
    "app.services.auth_service.create_audit_log",
)


# ── helpers ─────────────────────────────────────────────────────────────────

def _login(username: str, password: str):
    return client.post(LOGIN_URL, json={"username": username, "password": password})


# ── success cases ────────────────────────────────────────────────────────────

class TestLoginSuccess:
    def test_admin_login_returns_200(self, admin_account):
        with patch(_PATCHES[0], return_value=admin_account), \
             patch(_PATCHES[1]), patch(_PATCHES[2], return_value=MagicMock()):
            resp = _login(admin_account.username, TEST_PASSWORD)

        assert resp.status_code == 200

    def test_response_shape(self, admin_account):
        with patch(_PATCHES[0], return_value=admin_account), \
             patch(_PATCHES[1]), patch(_PATCHES[2], return_value=MagicMock()):
            body = _login(admin_account.username, TEST_PASSWORD).json()

        assert body["success"] is True
        data = body["data"]
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["expires_in"], int)
        assert data["expires_in"] > 0

    def test_account_block_in_response(self, admin_account):
        with patch(_PATCHES[0], return_value=admin_account), \
             patch(_PATCHES[1]), patch(_PATCHES[2], return_value=MagicMock()):
            data = _login(admin_account.username, TEST_PASSWORD).json()["data"]

        acc = data["account"]
        assert acc["account_id"] == admin_account.account_id
        assert acc["username"] == admin_account.username
        assert acc["role"] == "admin"
        assert acc["is_active"] is True

    def test_employee_block_in_response(self, admin_account):
        with patch(_PATCHES[0], return_value=admin_account), \
             patch(_PATCHES[1]), patch(_PATCHES[2], return_value=MagicMock()):
            data = _login(admin_account.username, TEST_PASSWORD).json()["data"]

        emp = data["employee"]
        assert emp["employee_id"] == admin_account.employee.employee_id
        assert emp["email"] == admin_account.username

    def test_employee_role_login(self, employee_account):
        with patch(_PATCHES[0], return_value=employee_account), \
             patch(_PATCHES[1]), patch(_PATCHES[2], return_value=MagicMock()):
            data = _login(employee_account.username, TEST_PASSWORD).json()["data"]

        assert data["account"]["role"] == "employee"

    def test_tokens_are_non_empty_strings(self, admin_account):
        with patch(_PATCHES[0], return_value=admin_account), \
             patch(_PATCHES[1]), patch(_PATCHES[2], return_value=MagicMock()):
            data = _login(admin_account.username, TEST_PASSWORD).json()["data"]

        assert isinstance(data["access_token"], str) and len(data["access_token"]) > 20
        assert isinstance(data["refresh_token"], str) and len(data["refresh_token"]) > 20

    def test_access_and_refresh_tokens_differ(self, admin_account):
        with patch(_PATCHES[0], return_value=admin_account), \
             patch(_PATCHES[1]), patch(_PATCHES[2], return_value=MagicMock()):
            data = _login(admin_account.username, TEST_PASSWORD).json()["data"]

        assert data["access_token"] != data["refresh_token"]

    def test_audit_log_is_written(self, admin_account):
        mock_audit = MagicMock(return_value=MagicMock())
        with patch(_PATCHES[0], return_value=admin_account), \
             patch(_PATCHES[1]), patch(_PATCHES[2], mock_audit):
            _login(admin_account.username, TEST_PASSWORD)

        mock_audit.assert_called_once()
        call_kwargs = mock_audit.call_args
        assert call_kwargs.kwargs.get("action_type").value == "login" or \
               (call_kwargs.args and hasattr(call_kwargs.args[1], "value") and call_kwargs.args[1].value == "login")


# ── error cases ──────────────────────────────────────────────────────────────

class TestLoginErrors:
    def test_wrong_password_returns_401(self, admin_account):
        with patch(_PATCHES[0], return_value=admin_account):
            resp = _login(admin_account.username, WRONG_PASSWORD)

        assert resp.status_code == 401
        err = resp.json()["error"]
        assert err["code"] == "INVALID_CREDENTIALS"

    def test_unknown_username_returns_401(self):
        with patch(_PATCHES[0], return_value=None):
            resp = _login("nobody@example.com", TEST_PASSWORD)

        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"

    def test_locked_account_returns_401(self, locked_account):
        with patch(_PATCHES[0], return_value=locked_account):
            resp = _login(locked_account.username, TEST_PASSWORD)

        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "ACCOUNT_LOCKED"

    def test_missing_username_returns_422(self):
        resp = client.post(LOGIN_URL, json={"password": TEST_PASSWORD})
        assert resp.status_code == 422

    def test_missing_password_returns_422(self):
        resp = client.post(LOGIN_URL, json={"username": "user@example.com"})
        assert resp.status_code == 422

    def test_empty_body_returns_422(self):
        resp = client.post(LOGIN_URL, json={})
        assert resp.status_code == 422

    def test_success_false_on_error(self, admin_account):
        with patch(_PATCHES[0], return_value=admin_account):
            resp = _login(admin_account.username, WRONG_PASSWORD)

        assert resp.json()["success"] is False

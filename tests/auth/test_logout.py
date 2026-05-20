"""Tests for POST /auth/logout."""
from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from app.core.security import is_blacklisted, decode_token
from tests.conftest import client

LOGOUT_URL = "/api/v1/auth/logout"

_GET_ACCOUNT_BY_ID = "app.api.dependencies.get_account_by_id"
_CREATE_AUDIT_LOG = "app.services.auth_service.create_audit_log"


# ── success cases ─────────────────────────────────────────────────────────

class TestLogoutSuccess:
    def test_logout_returns_200(self, admin_account, admin_tokens):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account), \
             patch(_CREATE_AUDIT_LOG, return_value=None):
            resp = client.post(
                LOGOUT_URL,
                json={"refresh_token": admin_tokens["refresh_token"]},
                headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
            )

        assert resp.status_code == 200

    def test_response_message(self, admin_account, admin_tokens):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account), \
             patch(_CREATE_AUDIT_LOG, return_value=None):
            body = client.post(
                LOGOUT_URL,
                json={"refresh_token": admin_tokens["refresh_token"]},
                headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
            ).json()

        assert body["success"] is True
        assert "logged out" in body["data"]["message"].lower()

    def test_access_token_is_blacklisted_after_logout(self, admin_account, admin_tokens):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account), \
             patch(_CREATE_AUDIT_LOG, return_value=None):
            client.post(
                LOGOUT_URL,
                json={"refresh_token": admin_tokens["refresh_token"]},
                headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
            )

        access_jti = decode_token(admin_tokens["access_token"])["jti"]
        assert is_blacklisted(access_jti)

    def test_refresh_token_is_blacklisted_after_logout(self, admin_account, admin_tokens):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account), \
             patch(_CREATE_AUDIT_LOG, return_value=None):
            client.post(
                LOGOUT_URL,
                json={"refresh_token": admin_tokens["refresh_token"]},
                headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
            )

        refresh_jti = decode_token(admin_tokens["refresh_token"])["jti"]
        assert is_blacklisted(refresh_jti)

    def test_me_returns_401_after_logout(self, admin_account, admin_tokens):
        from tests.auth.test_me import ME_URL
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account), \
             patch(_CREATE_AUDIT_LOG, return_value=None):
            client.post(
                LOGOUT_URL,
                json={"refresh_token": admin_tokens["refresh_token"]},
                headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
            )

        # access token is now blacklisted — /me must reject it
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account):
            resp = client.get(ME_URL, headers={"Authorization": f"Bearer {admin_tokens['access_token']}"})

        assert resp.status_code == 401

    def test_logout_without_refresh_token_body_returns_200(self, admin_account, admin_tokens):
        """Logout should succeed even without refresh token in body."""
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account), \
             patch(_CREATE_AUDIT_LOG, return_value=None):
            resp = client.post(
                LOGOUT_URL,
                headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
            )

        assert resp.status_code == 200

    def test_audit_log_written_on_logout(self, admin_account, admin_tokens):
        mock_audit = patch(_CREATE_AUDIT_LOG, return_value=None)
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account), mock_audit as m:
            client.post(
                LOGOUT_URL,
                json={"refresh_token": admin_tokens["refresh_token"]},
                headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
            )

        m.assert_called_once()


# ── error cases ────────────────────────────────────────────────────────────

class TestLogoutErrors:
    def test_no_token_returns_401(self):
        resp = client.post(LOGOUT_URL)
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self):
        resp = client.post(
            LOGOUT_URL,
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert resp.status_code == 401

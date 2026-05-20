"""Tests for POST /auth/refresh."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from jose import jwt

from app.core.security import (
    ALGORITHM,
    create_access_token,
    create_refresh_token,
    get_secret_key,
    blacklist_jti,
)
from tests.conftest import client

REFRESH_URL = "/api/v1/auth/refresh"

_GET_ACCOUNT_BY_ID = "app.repositories.auth_repository.get_account_by_id"


def _post(refresh_token: str):
    return client.post(REFRESH_URL, json={"refresh_token": refresh_token})


# ── success cases ─────────────────────────────────────────────────────────

class TestRefreshSuccess:
    def test_valid_refresh_token_returns_200(self, admin_account, admin_tokens):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account):
            resp = _post(admin_tokens["refresh_token"])

        assert resp.status_code == 200

    def test_response_shape(self, admin_account, admin_tokens):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account):
            body = _post(admin_tokens["refresh_token"]).json()

        assert body["success"] is True
        data = body["data"]
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["expires_in"], int) and data["expires_in"] > 0

    def test_new_access_token_differs_from_original(self, admin_account, admin_tokens):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account):
            data = _post(admin_tokens["refresh_token"]).json()["data"]

        assert data["access_token"] != admin_tokens["access_token"]

    def test_new_access_token_is_valid_jwt(self, admin_account, admin_tokens):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account):
            data = _post(admin_tokens["refresh_token"]).json()["data"]

        payload = jwt.decode(data["access_token"], get_secret_key(), algorithms=[ALGORITHM])
        assert payload["type"] == "access"
        assert payload["sub"] == str(admin_account.account_id)

    def test_new_token_has_fresh_jti(self, admin_account, admin_tokens):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account):
            data = _post(admin_tokens["refresh_token"]).json()["data"]

        new_payload = jwt.decode(data["access_token"], get_secret_key(), algorithms=[ALGORITHM])
        assert new_payload["jti"] != admin_tokens["access_jti"]

    def test_employee_refresh_works(self, employee_account, employee_tokens):
        with patch(_GET_ACCOUNT_BY_ID, return_value=employee_account):
            resp = _post(employee_tokens["refresh_token"])

        assert resp.status_code == 200


# ── error cases ────────────────────────────────────────────────────────────

class TestRefreshErrors:
    def test_invalid_token_string_returns_401(self):
        resp = _post("not.a.valid.jwt.token")
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"

    def test_access_token_used_as_refresh_returns_401(self, admin_tokens):
        # access tokens have type="access"; must be rejected
        resp = _post(admin_tokens["access_token"])
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"

    def test_blacklisted_refresh_token_returns_401(self, admin_account, admin_tokens):
        import time
        blacklist_jti(admin_tokens["refresh_jti"], time.time() + 3600)
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account):
            resp = _post(admin_tokens["refresh_token"])

        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"

    def test_locked_account_refresh_returns_401(self, locked_account):
        data = {"sub": str(locked_account.account_id), "role": locked_account.role.value}
        refresh_token, _ = create_refresh_token(data)
        with patch(_GET_ACCOUNT_BY_ID, return_value=locked_account):
            resp = _post(refresh_token)

        assert resp.status_code == 401

    def test_missing_refresh_token_field_returns_422(self):
        resp = client.post(REFRESH_URL, json={})
        assert resp.status_code == 422

    def test_empty_string_token_returns_401(self):
        # JWT decode will fail on empty string
        resp = _post("")
        assert resp.status_code == 401

    def test_success_false_on_error(self):
        resp = _post("garbage.token.value")
        assert resp.json()["success"] is False

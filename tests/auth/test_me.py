"""Tests for GET /auth/me."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from tests.conftest import client

ME_URL = "/api/v1/auth/me"

_GET_ACCOUNT_BY_ID = "app.api.dependencies.get_account_by_id"


# ── success cases ─────────────────────────────────────────────────────────

class TestMeSuccess:
    def test_returns_200_with_valid_token(self, admin_account, admin_auth_headers):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account):
            resp = client.get(ME_URL, headers=admin_auth_headers)

        assert resp.status_code == 200

    def test_response_shape(self, admin_account, admin_auth_headers):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account):
            body = client.get(ME_URL, headers=admin_auth_headers).json()

        assert body["success"] is True
        assert "account" in body["data"]
        assert "employee" in body["data"]

    def test_account_fields(self, admin_account, admin_auth_headers):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account):
            data = client.get(ME_URL, headers=admin_auth_headers).json()["data"]

        acc = data["account"]
        assert acc["account_id"] == admin_account.account_id
        assert acc["username"] == admin_account.username
        assert acc["role"] == "admin"
        assert acc["is_active"] is True

    def test_employee_fields(self, admin_account, admin_auth_headers):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account):
            data = client.get(ME_URL, headers=admin_auth_headers).json()["data"]

        emp = data["employee"]
        assert emp["employee_id"] == admin_account.employee.employee_id
        assert emp["email"] == admin_account.username
        assert emp["department_id"] == admin_account.employee.department_id

    def test_employee_role_account(self, employee_account, employee_auth_headers):
        with patch(_GET_ACCOUNT_BY_ID, return_value=employee_account):
            data = client.get(ME_URL, headers=employee_auth_headers).json()["data"]

        assert data["account"]["role"] == "employee"

    def test_no_sensitive_data_in_response(self, admin_account, admin_auth_headers):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account):
            body = client.get(ME_URL, headers=admin_auth_headers).json()

        body_str = str(body)
        assert "password" not in body_str.lower()
        assert "password_hash" not in body_str


# ── error cases ────────────────────────────────────────────────────────────

class TestMeErrors:
    def test_no_token_returns_401(self):
        resp = client.get(ME_URL)
        assert resp.status_code == 401

    def test_malformed_token_returns_401(self):
        resp = client.get(ME_URL, headers={"Authorization": "Bearer not.a.real.token"})
        assert resp.status_code == 401

    def test_wrong_scheme_returns_401(self):
        resp = client.get(ME_URL, headers={"Authorization": "Basic somebase64value"})
        assert resp.status_code == 401

    def test_refresh_token_as_bearer_returns_401(self, admin_tokens):
        # refresh token has type="refresh"; dependency must reject it
        headers = {"Authorization": f"Bearer {admin_tokens['refresh_token']}"}
        resp = client.get(ME_URL, headers=headers)
        assert resp.status_code == 401

    def test_blacklisted_access_token_returns_401(self, admin_account, admin_tokens):
        import time
        from app.core.security import blacklist_jti
        blacklist_jti(admin_tokens["access_jti"], time.time() + 3600)

        headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account):
            resp = client.get(ME_URL, headers=headers)

        assert resp.status_code == 401

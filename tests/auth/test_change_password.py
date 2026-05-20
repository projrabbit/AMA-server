"""Tests for PUT /auth/change-password."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.security import verify_password
from tests.conftest import TEST_PASSWORD, client

CHANGE_PWD_URL = "/api/v1/auth/change-password"

_GET_ACCOUNT_BY_ID = "app.api.dependencies.get_account_by_id"
_CREATE_AUDIT_LOG = "app.services.auth_service.create_audit_log"

NEW_VALID_PASSWORD = "NewSecure@456"
WEAK_PASSWORD = "weak"


def _change(
    auth_headers: dict,
    current: str = TEST_PASSWORD,
    new: str = NEW_VALID_PASSWORD,
    confirm: str = NEW_VALID_PASSWORD,
):
    return client.put(
        CHANGE_PWD_URL,
        json={
            "current_password": current,
            "new_password": new,
            "confirm_password": confirm,
        },
        headers=auth_headers,
    )


# ── success cases ─────────────────────────────────────────────────────────

class TestChangePasswordSuccess:
    def test_returns_200(self, admin_account, admin_auth_headers):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account), \
             patch(_CREATE_AUDIT_LOG, return_value=None):
            resp = _change(admin_auth_headers)

        assert resp.status_code == 200

    def test_response_shape(self, admin_account, admin_auth_headers):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account), \
             patch(_CREATE_AUDIT_LOG, return_value=None):
            body = _change(admin_auth_headers).json()

        assert body["success"] is True
        assert "message" in body["data"]

    def test_password_hash_updated_on_account_object(self, admin_account, admin_auth_headers):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account), \
             patch(_CREATE_AUDIT_LOG, return_value=None):
            _change(admin_auth_headers)

        # The service mutates the account object in memory
        assert verify_password(NEW_VALID_PASSWORD, admin_account.password_hash)
        assert not verify_password(TEST_PASSWORD, admin_account.password_hash)

    def test_audit_log_written(self, admin_account, admin_auth_headers):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account):
            with patch(_CREATE_AUDIT_LOG, return_value=None) as mock_audit:
                _change(admin_auth_headers)

        mock_audit.assert_called_once()

    def test_employee_can_change_own_password(self, employee_account, employee_auth_headers):
        with patch(_GET_ACCOUNT_BY_ID, return_value=employee_account), \
             patch(_CREATE_AUDIT_LOG, return_value=None):
            resp = _change(employee_auth_headers)

        assert resp.status_code == 200


# ── error cases ────────────────────────────────────────────────────────────

class TestChangePasswordErrors:
    def test_wrong_current_password_returns_400(self, admin_account, admin_auth_headers):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account):
            resp = _change(admin_auth_headers, current="WrongOld@999")

        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "WRONG_CURRENT_PASSWORD"

    def test_mismatched_new_passwords_returns_400(self, admin_account, admin_auth_headers):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account):
            resp = _change(
                admin_auth_headers,
                new=NEW_VALID_PASSWORD,
                confirm="Different@789",
            )

        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "PASSWORD_MISMATCH"

    def test_weak_new_password_too_short_returns_422(self, admin_account, admin_auth_headers):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account):
            resp = _change(admin_auth_headers, new="Ab1!", confirm="Ab1!")

        assert resp.status_code == 422

    def test_weak_password_no_uppercase_returns_422(self, admin_account, admin_auth_headers):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account):
            resp = _change(admin_auth_headers, new="nouppercase1!", confirm="nouppercase1!")

        assert resp.status_code == 422

    def test_weak_password_no_digit_returns_422(self, admin_account, admin_auth_headers):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account):
            resp = _change(admin_auth_headers, new="NoDigitPass!", confirm="NoDigitPass!")

        assert resp.status_code == 422

    def test_weak_password_no_lowercase_returns_422(self, admin_account, admin_auth_headers):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account):
            resp = _change(admin_auth_headers, new="NOLOWER123!", confirm="NOLOWER123!")

        assert resp.status_code == 422

    def test_no_auth_returns_401(self):
        resp = client.put(
            CHANGE_PWD_URL,
            json={
                "current_password": TEST_PASSWORD,
                "new_password": NEW_VALID_PASSWORD,
                "confirm_password": NEW_VALID_PASSWORD,
            },
        )
        assert resp.status_code == 401

    def test_missing_current_password_returns_422(self, admin_auth_headers):
        resp = client.put(
            CHANGE_PWD_URL,
            json={"new_password": NEW_VALID_PASSWORD, "confirm_password": NEW_VALID_PASSWORD},
            headers=admin_auth_headers,
        )
        assert resp.status_code == 422

    def test_empty_body_returns_422(self, admin_auth_headers):
        resp = client.put(CHANGE_PWD_URL, json={}, headers=admin_auth_headers)
        assert resp.status_code == 422

    def test_success_false_on_error(self, admin_account, admin_auth_headers):
        with patch(_GET_ACCOUNT_BY_ID, return_value=admin_account):
            resp = _change(admin_auth_headers, current="WrongOld@999")

        assert resp.json()["success"] is False

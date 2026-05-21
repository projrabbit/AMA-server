"""Tests for Module 8 audit log read endpoints."""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.core.security import create_access_token
from app.models.business import AuditActionType
from tests.conftest import client


BASE = "/api/v1/audit-logs"

_SVC = "app.services.audit_service"
_LIST_REPO = f"{_SVC}.list_audit_logs"
_GET_REPO = f"{_SVC}.get_audit_log_by_id"

_DEP_PATCH = "app.api.dependencies.get_account_by_id"


def make_audit_log(
    log_id: int = 501,
    account_id: int = 1001,
    action_type: AuditActionType = AuditActionType.login,
    target_entity: str = "ACCOUNT",
    target_id: int | None = 1001,
    ip_address: str | None = "127.0.0.1",
) -> SimpleNamespace:
    return SimpleNamespace(
        log_id=log_id,
        account_id=account_id,
        action_type=action_type,
        target_entity=target_entity,
        target_id=target_id,
        payload=None,
        ip_address=ip_address,
        created_at=datetime(2026, 5, 21, 9, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def hr_headers(hr_account):
    data = {"sub": str(hr_account.account_id), "role": hr_account.role.value}
    token, _ = create_access_token(data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def as_hr(hr_account, hr_headers):
    with patch(_DEP_PATCH, return_value=hr_account):
        yield hr_headers


@pytest.fixture
def as_admin(admin_account, admin_auth_headers):
    with patch(_DEP_PATCH, return_value=admin_account):
        yield admin_auth_headers


# ── GET /audit-logs ──────────────────────────────────────────────────────────

class TestListAuditLogs:
    def test_returns_200_with_items_and_total(self, as_hr):
        logs = [make_audit_log(log_id=501), make_audit_log(log_id=502, action_type=AuditActionType.create)]
        with patch(_LIST_REPO, return_value=(logs, 2)):
            resp = client.get(BASE, headers=as_hr)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["total"] == 2
        assert data["limit"] == 20  # default
        assert data["offset"] == 0
        assert len(data["items"]) == 2
        assert data["items"][0]["log_id"] == 501

    def test_default_limit_is_20(self, as_hr):
        with patch(_LIST_REPO, return_value=([], 0)) as mock_repo:
            client.get(BASE, headers=as_hr)
        kwargs = mock_repo.call_args.kwargs
        assert kwargs["limit"] == 20
        assert kwargs["offset"] == 0

    def test_limit_is_capped_at_100(self, as_hr):
        with patch(_LIST_REPO, return_value=([], 0)) as mock_repo:
            client.get(f"{BASE}/?limit=500", headers=as_hr)
        assert mock_repo.call_args.kwargs["limit"] == 100

    def test_filter_by_account_id_passes_kwarg(self, as_hr):
        with patch(_LIST_REPO, return_value=([], 0)) as mock_repo:
            client.get(f"{BASE}/?account_id=1001", headers=as_hr)
        assert mock_repo.call_args.kwargs["account_id"] == 1001

    def test_filter_by_action_type_passes_enum(self, as_hr):
        with patch(_LIST_REPO, return_value=([], 0)) as mock_repo:
            client.get(f"{BASE}/?action_type=login", headers=as_hr)
        assert mock_repo.call_args.kwargs["action_type"] == AuditActionType.login

    def test_offset_is_passed_through(self, as_hr):
        with patch(_LIST_REPO, return_value=([], 0)) as mock_repo:
            client.get(f"{BASE}/?offset=40&limit=10", headers=as_hr)
        kwargs = mock_repo.call_args.kwargs
        assert kwargs["offset"] == 40
        assert kwargs["limit"] == 10

    def test_401_no_token(self):
        resp = client.get(BASE)
        assert resp.status_code == 401

    def test_403_employee_role(self, employee_auth_headers):
        resp = client.get(BASE, headers=employee_auth_headers)
        assert resp.status_code == 403


# ── GET /audit-logs/{log_id} ─────────────────────────────────────────────────

class TestGetAuditLog:
    def test_returns_200(self, as_hr):
        with patch(_GET_REPO, return_value=make_audit_log(log_id=777)):
            resp = client.get(f"{BASE}/777", headers=as_hr)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["log_id"] == 777
        assert data["action_type"] == "login"

    def test_404_when_missing(self, as_hr):
        with patch(_GET_REPO, return_value=None):
            resp = client.get(f"{BASE}/99999", headers=as_hr)
        assert resp.status_code == 404
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "LOG_NOT_FOUND"

    def test_401_no_token(self):
        resp = client.get(f"{BASE}/1")
        assert resp.status_code == 401

    def test_403_employee_role(self, employee_auth_headers):
        resp = client.get(f"{BASE}/1", headers=employee_auth_headers)
        assert resp.status_code == 403

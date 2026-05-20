"""Tests for Module 9 device endpoints."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import client
from tests.admin.conftest import make_device

BASE_DEVICES = "/api/v1/devices"

_SVC = "app.services.admin_service"
_AUDIT = f"{_SVC}.create_audit_log"
_GET_FP_EMP = f"{_SVC}.get_device_by_fingerprint_and_employee"
_CREATE_DEV = f"{_SVC}.create_device"
_UPDATE_META = f"{_SVC}.update_device_metadata"
_GET_DEVS_EMP = f"{_SVC}.get_devices_for_employee"
_GET_DEVS = f"{_SVC}.get_devices"
_GET_DEV = f"{_SVC}.get_device_by_id"
_TRUST_DEV = f"{_SVC}.update_device_trust"


# ── POST /devices/register ────────────────────────────────────────────────────

class TestRegisterDevice:
    _PAYLOAD = {
        "device_fingerprint": "fp-abc-123",
        "platform": "android",
        "model": "Pixel 8",
        "os_version": "Android 15",
        "app_version": "1.0.0",
    }

    def test_returns_201_new_device(self, as_employee, device_ns):
        with patch(_GET_FP_EMP, return_value=None), \
             patch(_CREATE_DEV, return_value=device_ns):
            resp = client.post(f"{BASE_DEVICES}/register", json=self._PAYLOAD, headers=as_employee)
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["is_trusted"] is False

    def test_returns_201_update_existing(self, as_employee, device_ns):
        with patch(_GET_FP_EMP, return_value=device_ns), \
             patch(_UPDATE_META, return_value=device_ns):
            resp = client.post(f"{BASE_DEVICES}/register", json=self._PAYLOAD, headers=as_employee)
        assert resp.status_code == 201

    def test_response_has_registered_at(self, as_employee, device_ns):
        with patch(_GET_FP_EMP, return_value=None), \
             patch(_CREATE_DEV, return_value=device_ns):
            data = client.post(f"{BASE_DEVICES}/register", json=self._PAYLOAD, headers=as_employee).json()["data"]
        assert "registered_at" in data

    def test_401_no_token(self):
        resp = client.post(f"{BASE_DEVICES}/register", json=self._PAYLOAD)
        assert resp.status_code == 401

    def test_403_hr_role(self, hr_auth_headers):
        resp = client.post(f"{BASE_DEVICES}/register", json=self._PAYLOAD, headers=hr_auth_headers)
        assert resp.status_code == 403

    def test_422_missing_fingerprint(self, as_employee):
        payload = {k: v for k, v in self._PAYLOAD.items() if k != "device_fingerprint"}
        resp = client.post(f"{BASE_DEVICES}/register", json=payload, headers=as_employee)
        assert resp.status_code == 422


# ── GET /devices/me ───────────────────────────────────────────────────────────

class TestGetMyDevices:
    def test_returns_200_with_list(self, as_employee, device_ns):
        with patch(_GET_DEVS_EMP, return_value=[device_ns]):
            resp = client.get(f"{BASE_DEVICES}/me", headers=as_employee)
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)
        assert len(resp.json()["data"]) == 1

    def test_returns_empty_list_when_no_devices(self, as_employee):
        with patch(_GET_DEVS_EMP, return_value=[]):
            resp = client.get(f"{BASE_DEVICES}/me", headers=as_employee)
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_device_fields(self, as_employee, device_ns):
        with patch(_GET_DEVS_EMP, return_value=[device_ns]):
            data = client.get(f"{BASE_DEVICES}/me", headers=as_employee).json()["data"]
        device = data[0]
        assert "device_id" in device
        assert "is_trusted" in device
        assert "registered_at" in device

    def test_401_no_token(self):
        resp = client.get(f"{BASE_DEVICES}/me")
        assert resp.status_code == 401

    def test_403_hr_role(self, hr_auth_headers):
        resp = client.get(f"{BASE_DEVICES}/me", headers=hr_auth_headers)
        assert resp.status_code == 403


# ── GET /devices ──────────────────────────────────────────────────────────────

class TestListDevices:
    def test_returns_200(self, as_admin, device_ns):
        with patch(_GET_DEVS, return_value=([device_ns], 1)):
            resp = client.get(BASE_DEVICES, headers=as_admin)
        assert resp.status_code == 200
        assert resp.json()["meta"]["total"] == 1

    def test_401_no_token(self):
        resp = client.get(BASE_DEVICES)
        assert resp.status_code == 401

    def test_403_hr_role(self, hr_auth_headers):
        resp = client.get(BASE_DEVICES, headers=hr_auth_headers)
        assert resp.status_code == 403

    def test_403_employee_role(self, employee_auth_headers):
        resp = client.get(BASE_DEVICES, headers=employee_auth_headers)
        assert resp.status_code == 403


# ── PUT /devices/{id}/trust ───────────────────────────────────────────────────

class TestTrustDevice:
    def test_trust_device_200(self, as_admin, device_ns):
        with patch(_GET_DEV, return_value=device_ns), \
             patch(_TRUST_DEV, return_value=device_ns), \
             patch(_AUDIT, return_value=MagicMock()):
            resp = client.put(f"{BASE_DEVICES}/30/trust", json={"is_trusted": True}, headers=as_admin)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["is_trusted"] is True
        assert data["updated"] is True

    def test_untrust_device_200(self, as_admin, device_ns):
        device_ns.is_trusted = True
        with patch(_GET_DEV, return_value=device_ns), \
             patch(_TRUST_DEV, return_value=device_ns), \
             patch(_AUDIT, return_value=MagicMock()):
            resp = client.put(f"{BASE_DEVICES}/30/trust", json={"is_trusted": False}, headers=as_admin)
        assert resp.status_code == 200

    def test_404_device_not_found(self, as_admin):
        with patch(_GET_DEV, return_value=None):
            resp = client.put(f"{BASE_DEVICES}/9999/trust", json={"is_trusted": True}, headers=as_admin)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "DEVICE_NOT_FOUND"

    def test_401_no_token(self):
        resp = client.put(f"{BASE_DEVICES}/30/trust", json={"is_trusted": True})
        assert resp.status_code == 401

    def test_403_hr_role(self, hr_auth_headers):
        resp = client.put(f"{BASE_DEVICES}/30/trust", json={"is_trusted": True}, headers=hr_auth_headers)
        assert resp.status_code == 403

    def test_422_missing_is_trusted(self, as_admin):
        with patch(_GET_DEV, return_value=MagicMock()):
            resp = client.put(f"{BASE_DEVICES}/30/trust", json={}, headers=as_admin)
        assert resp.status_code == 422

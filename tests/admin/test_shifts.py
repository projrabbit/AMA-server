"""Tests for Module 9 shift endpoints."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import client
from tests.admin.conftest import make_shift

BASE = "/api/v1/shifts"

_SVC = "app.services.admin_service"
_AUDIT = f"{_SVC}.create_audit_log"
_LIST_SHIFTS = f"{_SVC}.get_shifts"
_GET_SHIFT = f"{_SVC}.get_shift_by_id"
_GET_EMP = f"{_SVC}.get_employee_by_id"
_CONFLICT = f"{_SVC}.has_shift_conflict"
_CREATE_SHIFT = f"{_SVC}.create_shift"
_UPDATE_SHIFT = f"{_SVC}.update_shift_fields"


# ── GET /shifts ───────────────────────────────────────────────────────────────

class TestListShifts:
    def test_returns_200(self, as_hr, shift_ns):
        with patch(_LIST_SHIFTS, return_value=([shift_ns], 1)):
            resp = client.get(BASE, headers=as_hr)
        assert resp.status_code == 200

    def test_response_shape(self, as_hr, shift_ns):
        with patch(_LIST_SHIFTS, return_value=([shift_ns], 1)):
            body = client.get(BASE, headers=as_hr).json()
        assert body["success"] is True
        assert body["data"][0]["name"] == "Morning Shift"
        assert body["meta"]["total"] == 1

    def test_401_no_token(self):
        resp = client.get(BASE)
        assert resp.status_code == 401

    def test_403_employee_role(self, employee_auth_headers):
        resp = client.get(BASE, headers=employee_auth_headers)
        assert resp.status_code == 403


# ── POST /shifts ──────────────────────────────────────────────────────────────

class TestCreateShift:
    _PAYLOAD = {
        "employee_id": 1001,
        "name": "Morning Shift",
        "start_time": "08:00:00",
        "end_time": "17:00:00",
        "late_tolerance_min": 10,
        "early_leave_min": 10,
        "apply_to_weekends": False,
    }

    def test_returns_201(self, as_hr, shift_ns):
        with patch(_GET_EMP, return_value=MagicMock()), \
             patch(_CONFLICT, return_value=False), \
             patch(_CREATE_SHIFT, return_value=shift_ns), \
             patch(_AUDIT, return_value=MagicMock()):
            resp = client.post(BASE, json=self._PAYLOAD, headers=as_hr)
        assert resp.status_code == 201
        assert resp.json()["data"]["name"] == "Morning Shift"

    def test_404_employee_not_found(self, as_hr):
        with patch(_GET_EMP, return_value=None):
            resp = client.post(BASE, json=self._PAYLOAD, headers=as_hr)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "EMPLOYEE_NOT_FOUND"

    def test_409_shift_conflict(self, as_hr):
        with patch(_GET_EMP, return_value=MagicMock()), \
             patch(_CONFLICT, return_value=True):
            resp = client.post(BASE, json=self._PAYLOAD, headers=as_hr)
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "SHIFT_TIME_CONFLICT"

    def test_422_missing_times(self, as_hr):
        payload = {k: v for k, v in self._PAYLOAD.items() if k not in ("start_time", "end_time")}
        resp = client.post(BASE, json=payload, headers=as_hr)
        assert resp.status_code == 422

    def test_401_no_token(self):
        resp = client.post(BASE, json=self._PAYLOAD)
        assert resp.status_code == 401


# ── PUT /shifts/{id} ──────────────────────────────────────────────────────────

class TestUpdateShift:
    _PAYLOAD = {"end_time": "17:30:00"}

    def test_returns_200(self, as_hr, shift_ns):
        with patch(_GET_SHIFT, return_value=shift_ns), \
             patch(_CONFLICT, return_value=False), \
             patch(_UPDATE_SHIFT, return_value=shift_ns), \
             patch(_AUDIT, return_value=MagicMock()):
            resp = client.put(f"{BASE}/20", json=self._PAYLOAD, headers=as_hr)
        assert resp.status_code == 200
        assert resp.json()["data"]["updated"] is True

    def test_404_not_found(self, as_hr):
        with patch(_GET_SHIFT, return_value=None):
            resp = client.put(f"{BASE}/9999", json=self._PAYLOAD, headers=as_hr)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "SHIFT_NOT_FOUND"

    def test_409_time_conflict(self, as_hr, shift_ns):
        with patch(_GET_SHIFT, return_value=shift_ns), \
             patch(_CONFLICT, return_value=True):
            resp = client.put(f"{BASE}/20", json={"start_time": "07:00:00", "end_time": "16:00:00"}, headers=as_hr)
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "SHIFT_TIME_CONFLICT"

    def test_401_no_token(self):
        resp = client.put(f"{BASE}/20", json=self._PAYLOAD)
        assert resp.status_code == 401

    def test_403_employee_role(self, employee_auth_headers):
        resp = client.put(f"{BASE}/20", json=self._PAYLOAD, headers=employee_auth_headers)
        assert resp.status_code == 403

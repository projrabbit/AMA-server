"""Tests for Module 9 employee endpoints."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.models.business import EmployeeStatus
from tests.conftest import client
from tests.admin.conftest import make_employee_full, make_shift

BASE = "/api/v1/employees"

_SVC = "app.services.admin_service"
_AUDIT = f"{_SVC}.create_audit_log"
_LIST_EMP = f"{_SVC}.get_employees"
_GET_EMP = f"{_SVC}.get_employee_by_id"
_GET_EMAIL = f"{_SVC}.get_employee_by_email"
_GET_PHONE = f"{_SVC}.get_employee_by_phone"
_GET_DEPT = f"{_SVC}.get_department_by_id"
_CREATE_EA = f"{_SVC}.create_employee_and_account"
_UPDATE_EMP = f"{_SVC}.update_employee_fields"
_DEACTIVATE = f"{_SVC}.deactivate_employee"
_GET_SHIFT = f"{_SVC}.get_shift_by_id"
_ASSIGN_SHIFT = f"{_SVC}.assign_shift_to_employee"


# ── GET /employees ────────────────────────────────────────────────────────────

class TestListEmployees:
    def test_returns_200(self, as_hr, employee_full):
        with patch(_LIST_EMP, return_value=([employee_full], 1)):
            resp = client.get(BASE, headers=as_hr)
        assert resp.status_code == 200

    def test_response_shape(self, as_hr, employee_full):
        with patch(_LIST_EMP, return_value=([employee_full], 1)):
            body = client.get(BASE, headers=as_hr).json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
        assert body["meta"]["total"] == 1

    def test_401_without_token(self):
        resp = client.get(BASE)
        assert resp.status_code == 401

    def test_403_employee_role(self, employee_auth_headers):
        resp = client.get(BASE, headers=employee_auth_headers)
        assert resp.status_code == 403


# ── POST /employees ───────────────────────────────────────────────────────────

class TestCreateEmployee:
    _PAYLOAD = {
        "full_name": "Jane Doe",
        "department_id": 10,
        "position": "Developer",
        "email": "jane@example.com",
        "phone": "0901000002",
        "hire_date": "2025-01-15",
        "role": "employee",
        "temporary_password": "Temp@1234",
    }

    def _post(self, headers, payload=None):
        return client.post(BASE, json=payload or self._PAYLOAD, headers=headers)

    def test_returns_201(self, as_hr):
        emp = MagicMock(employee_id=10, status=EmployeeStatus.active)
        acc = MagicMock(account_id=1, username="jane@example.com")
        with patch(_GET_DEPT, return_value=MagicMock()), \
             patch(_GET_EMAIL, return_value=None), \
             patch(_GET_PHONE, return_value=None), \
             patch(_CREATE_EA, return_value=(emp, acc)), \
             patch(_AUDIT, return_value=MagicMock()):
            resp = self._post(as_hr)
        assert resp.status_code == 201

    def test_response_has_employee_id(self, as_hr):
        emp = MagicMock(employee_id=10, status=EmployeeStatus.active)
        acc = MagicMock(account_id=1, username="jane@example.com")
        with patch(_GET_DEPT, return_value=MagicMock()), \
             patch(_GET_EMAIL, return_value=None), \
             patch(_GET_PHONE, return_value=None), \
             patch(_CREATE_EA, return_value=(emp, acc)), \
             patch(_AUDIT, return_value=MagicMock()):
            body = self._post(as_hr).json()
        assert body["data"]["employee_id"] == 10

    def test_409_email_conflict(self, as_hr, employee_full):
        with patch(_GET_DEPT, return_value=MagicMock()), \
             patch(_GET_EMAIL, return_value=employee_full):
            resp = self._post(as_hr)
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"

    def test_409_phone_conflict(self, as_hr, employee_full):
        with patch(_GET_DEPT, return_value=MagicMock()), \
             patch(_GET_EMAIL, return_value=None), \
             patch(_GET_PHONE, return_value=employee_full):
            resp = self._post(as_hr)
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "PHONE_ALREADY_EXISTS"

    def test_404_department_not_found(self, as_hr):
        with patch(_GET_DEPT, return_value=None):
            resp = self._post(as_hr)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "DEPARTMENT_NOT_FOUND"

    def test_422_missing_field(self, as_hr):
        payload = {k: v for k, v in self._PAYLOAD.items() if k != "email"}
        resp = self._post(as_hr, payload)
        assert resp.status_code == 422

    def test_422_weak_password(self, as_hr):
        payload = {**self._PAYLOAD, "temporary_password": "weak"}
        resp = self._post(as_hr, payload)
        assert resp.status_code == 422

    def test_401_no_token(self):
        resp = client.post(BASE, json=self._PAYLOAD)
        assert resp.status_code == 401


# ── GET /employees/{id} ───────────────────────────────────────────────────────

class TestGetEmployeeDetail:
    def test_returns_200(self, as_hr, employee_full):
        with patch(_GET_EMP, return_value=employee_full):
            resp = client.get(f"{BASE}/1001", headers=as_hr)
        assert resp.status_code == 200

    def test_response_has_fields(self, as_hr, employee_full):
        with patch(_GET_EMP, return_value=employee_full):
            data = client.get(f"{BASE}/1001", headers=as_hr).json()["data"]
        assert data["employee_id"] == employee_full.employee_id
        assert "face_registered" in data

    def test_404_not_found(self, as_hr):
        with patch(_GET_EMP, return_value=None):
            resp = client.get(f"{BASE}/9999", headers=as_hr)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "EMPLOYEE_NOT_FOUND"

    def test_401_no_token(self):
        resp = client.get(f"{BASE}/1001")
        assert resp.status_code == 401


# ── PUT /employees/{id} ───────────────────────────────────────────────────────

class TestUpdateEmployee:
    _PAYLOAD = {"full_name": "Updated Name", "position": "Senior Developer"}

    def test_returns_200(self, as_hr, employee_full):
        with patch(_GET_EMP, return_value=employee_full), \
             patch(_GET_EMAIL, return_value=None), \
             patch(_GET_PHONE, return_value=None), \
             patch(_GET_DEPT, return_value=MagicMock()), \
             patch(_UPDATE_EMP, return_value=employee_full), \
             patch(_AUDIT, return_value=MagicMock()):
            resp = client.put(f"{BASE}/1001", json=self._PAYLOAD, headers=as_hr)
        assert resp.status_code == 200
        assert resp.json()["data"]["updated"] is True

    def test_404_employee_not_found(self, as_hr):
        with patch(_GET_EMP, return_value=None):
            resp = client.put(f"{BASE}/9999", json=self._PAYLOAD, headers=as_hr)
        assert resp.status_code == 404

    def test_409_email_conflict(self, as_hr, employee_full):
        other = MagicMock(employee_id=9999)
        with patch(_GET_EMP, return_value=employee_full), \
             patch(_GET_EMAIL, return_value=other):
            resp = client.put(f"{BASE}/1001", json={"email": "taken@example.com"}, headers=as_hr)
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"


# ── PUT /employees/{id}/deactivate ────────────────────────────────────────────

class TestDeactivateEmployee:
    def test_returns_200(self, as_hr, employee_full):
        with patch(_GET_EMP, return_value=employee_full), \
             patch(_DEACTIVATE, return_value=employee_full), \
             patch(_AUDIT, return_value=MagicMock()):
            resp = client.put(f"{BASE}/1001/deactivate", json={}, headers=as_hr)
        assert resp.status_code == 200
        assert resp.json()["data"]["account_locked"] is True

    def test_404_not_found(self, as_hr):
        with patch(_GET_EMP, return_value=None):
            resp = client.put(f"{BASE}/9999/deactivate", json={}, headers=as_hr)
        assert resp.status_code == 404

    def test_409_already_inactive(self, as_hr, employee_full):
        employee_full.status = EmployeeStatus.inactive
        with patch(_GET_EMP, return_value=employee_full):
            resp = client.put(f"{BASE}/1001/deactivate", json={}, headers=as_hr)
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "ALREADY_INACTIVE"

    def test_403_employee_role(self, employee_auth_headers):
        resp = client.put(f"{BASE}/1001/deactivate", json={}, headers=employee_auth_headers)
        assert resp.status_code == 403


# ── PUT /employees/{id}/shift ─────────────────────────────────────────────────

class TestAssignShift:
    def test_returns_200(self, as_hr, employee_full, shift_ns):
        with patch(_GET_EMP, return_value=employee_full), \
             patch(_GET_SHIFT, return_value=shift_ns), \
             patch(_ASSIGN_SHIFT, return_value=shift_ns), \
             patch(_AUDIT, return_value=MagicMock()):
            resp = client.put(f"{BASE}/1001/shift", json={"shift_id": 20}, headers=as_hr)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["assigned"] is True
        assert data["shift_id"] == 20

    def test_404_employee_not_found(self, as_hr):
        with patch(_GET_EMP, return_value=None):
            resp = client.put(f"{BASE}/9999/shift", json={"shift_id": 20}, headers=as_hr)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "EMPLOYEE_NOT_FOUND"

    def test_404_shift_not_found(self, as_hr, employee_full):
        with patch(_GET_EMP, return_value=employee_full), \
             patch(_GET_SHIFT, return_value=None):
            resp = client.put(f"{BASE}/1001/shift", json={"shift_id": 99}, headers=as_hr)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "SHIFT_NOT_FOUND"

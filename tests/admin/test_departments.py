"""Tests for Module 9 department endpoints."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import client
from tests.admin.conftest import make_department, make_dept_orm

BASE = "/api/v1/departments"

_SVC = "app.services.admin_service"
_AUDIT = f"{_SVC}.create_audit_log"
_LIST_DEPTS = f"{_SVC}.get_departments"
_GET_DEPT = f"{_SVC}.get_department_by_id"
_GET_DEPT_NAME = f"{_SVC}.get_department_by_name"
_GET_EMP = f"{_SVC}.get_employee_by_id"
_CREATE_DEPT = f"{_SVC}.create_department"
_UPDATE_DEPT = f"{_SVC}.update_department_fields"


# ── GET /departments ──────────────────────────────────────────────────────────

class TestListDepartments:
    def test_returns_200(self, as_hr):
        dept = make_department()
        with patch(_LIST_DEPTS, return_value=([dept], 1)):
            resp = client.get(BASE, headers=as_hr)
        assert resp.status_code == 200

    def test_response_shape(self, as_hr):
        dept = make_department()
        with patch(_LIST_DEPTS, return_value=([dept], 1)):
            body = client.get(BASE, headers=as_hr).json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
        assert body["data"][0]["name"] == "Engineering"
        assert body["meta"]["total"] == 1

    def test_401_no_token(self):
        resp = client.get(BASE)
        assert resp.status_code == 401

    def test_403_employee_role(self, employee_auth_headers):
        resp = client.get(BASE, headers=employee_auth_headers)
        assert resp.status_code == 403


# ── POST /departments ─────────────────────────────────────────────────────────

class TestCreateDepartment:
    _PAYLOAD = {"name": "Engineering", "description": "Dev team"}

    def test_returns_201(self, as_hr):
        created = make_dept_orm(department_id=10, name="Engineering")
        with patch(_GET_EMP, return_value=None), \
             patch(_GET_DEPT_NAME, return_value=None), \
             patch(_CREATE_DEPT, return_value=created):
            resp = client.post(BASE, json=self._PAYLOAD, headers=as_hr)
        assert resp.status_code == 201
        assert resp.json()["data"]["name"] == "Engineering"

    def test_409_name_exists(self, as_hr, dept_orm):
        with patch(_GET_EMP, return_value=None), \
             patch(_GET_DEPT_NAME, return_value=dept_orm):
            resp = client.post(BASE, json=self._PAYLOAD, headers=as_hr)
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "DEPARTMENT_NAME_EXISTS"

    def test_404_manager_not_found(self, as_hr):
        payload = {**self._PAYLOAD, "manager_id": 9999}
        with patch(_GET_EMP, return_value=None):
            resp = client.post(BASE, json=payload, headers=as_hr)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "MANAGER_NOT_FOUND"

    def test_422_missing_name(self, as_hr):
        resp = client.post(BASE, json={"description": "No name"}, headers=as_hr)
        assert resp.status_code == 422

    def test_401_no_token(self):
        resp = client.post(BASE, json=self._PAYLOAD)
        assert resp.status_code == 401


# ── PUT /departments/{id} ─────────────────────────────────────────────────────

class TestUpdateDepartment:
    _PAYLOAD = {"name": "Updated Engineering"}

    def test_returns_200(self, as_hr, dept_orm):
        with patch(_GET_DEPT, return_value=dept_orm), \
             patch(_GET_DEPT_NAME, return_value=None), \
             patch(_UPDATE_DEPT, return_value=dept_orm), \
             patch(_AUDIT, return_value=MagicMock()):
            resp = client.put(f"{BASE}/10", json=self._PAYLOAD, headers=as_hr)
        assert resp.status_code == 200
        assert resp.json()["data"]["updated"] is True

    def test_404_not_found(self, as_hr):
        with patch(_GET_DEPT, return_value=None):
            resp = client.put(f"{BASE}/9999", json=self._PAYLOAD, headers=as_hr)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "DEPARTMENT_NOT_FOUND"

    def test_409_name_conflict(self, as_hr, dept_orm):
        other = MagicMock(department_id=9999)
        with patch(_GET_DEPT, return_value=dept_orm), \
             patch(_GET_DEPT_NAME, return_value=other):
            resp = client.put(f"{BASE}/10", json={"name": "Other Dept"}, headers=as_hr)
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "DEPARTMENT_NAME_EXISTS"

    def test_401_no_token(self):
        resp = client.put(f"{BASE}/10", json=self._PAYLOAD)
        assert resp.status_code == 401

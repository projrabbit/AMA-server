"""Tests for Module 3 building and floor endpoints."""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import client
from tests.geofence.conftest import make_building, make_floor

BASE = "/api/v1/buildings"

_SVC = "app.services.geofence_service"
_AUDIT = f"{_SVC}.create_audit_log"
_LIST_BUILDINGS = f"{_SVC}.get_buildings"
_GET_BUILDING = f"{_SVC}.get_building_by_id"
_GET_BUILDING_NAME = f"{_SVC}.get_building_by_name"
_CREATE_BUILDING = f"{_SVC}.create_building"
_UPDATE_BUILDING = f"{_SVC}.update_building_fields"
_GET_FLOORS = f"{_SVC}.get_floors_for_building"
_GET_FLOOR_NUM = f"{_SVC}.get_floor_by_number_and_building"
_CREATE_FLOOR = f"{_SVC}.create_floor"


# ── GET /buildings ────────────────────────────────────────────────────────────

class TestListBuildings:
    def test_returns_200(self, as_hr, building_ns):
        with patch(_LIST_BUILDINGS, return_value=[building_ns]):
            resp = client.get(BASE, headers=as_hr)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
        assert len(body["data"]) == 1

    def test_floors_none_without_include_floors(self, as_hr, building_ns):
        with patch(_LIST_BUILDINGS, return_value=[building_ns]):
            body = client.get(BASE, headers=as_hr).json()
        assert body["data"][0]["floors"] is None

    def test_floors_populated_with_include_floors(self, as_hr):
        floor = make_floor()
        building = make_building(floors=[floor])
        with patch(_LIST_BUILDINGS, return_value=[building]):
            body = client.get(f"{BASE}?include_floors=true", headers=as_hr).json()
        assert body["data"][0]["floors"] is not None
        assert len(body["data"][0]["floors"]) == 1

    def test_401_no_token(self):
        resp = client.get(BASE)
        assert resp.status_code == 401

    def test_403_employee_role(self, employee_auth_headers):
        resp = client.get(BASE, headers=employee_auth_headers)
        assert resp.status_code == 403


# ── POST /buildings ───────────────────────────────────────────────────────────

class TestCreateBuilding:
    _PAYLOAD = {
        "name": "Main Office",
        "address": "123 Main St",
        "center_lat": "10.772123",
        "center_lng": "106.657890",
        "total_floors": 5,
        "arcgis_layer_id": "arcgis-layer-001",
    }

    def test_returns_201(self, as_admin, building_ns):
        with patch(_GET_BUILDING_NAME, return_value=None), \
             patch(_CREATE_BUILDING, return_value=building_ns), \
             patch(_AUDIT, return_value=MagicMock()):
            resp = client.post(BASE, json=self._PAYLOAD, headers=as_admin)
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["building_id"] == 1
        assert data["arcgis_layer_valid"] is True

    def test_400_invalid_arcgis_layer(self, as_admin):
        payload = {**self._PAYLOAD, "arcgis_layer_id": ""}
        resp = client.post(BASE, json=payload, headers=as_admin)
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_ARCGIS_LAYER"

    def test_409_name_exists(self, as_admin, building_ns):
        with patch(_GET_BUILDING_NAME, return_value=building_ns):
            resp = client.post(BASE, json=self._PAYLOAD, headers=as_admin)
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "BUILDING_NAME_EXISTS"

    def test_422_missing_name(self, as_admin):
        payload = {k: v for k, v in self._PAYLOAD.items() if k != "name"}
        resp = client.post(BASE, json=payload, headers=as_admin)
        assert resp.status_code == 422

    def test_401_no_token(self):
        resp = client.post(BASE, json=self._PAYLOAD)
        assert resp.status_code == 401

    def test_403_hr_role(self, hr_auth_headers):
        resp = client.post(BASE, json=self._PAYLOAD, headers=hr_auth_headers)
        assert resp.status_code == 403


# ── PUT /buildings/{id} ───────────────────────────────────────────────────────

class TestUpdateBuilding:
    _PAYLOAD = {"name": "Updated Office", "address": "456 New St"}

    def test_returns_200(self, as_admin, building_ns):
        with patch(_GET_BUILDING, return_value=building_ns), \
             patch(_UPDATE_BUILDING, return_value=building_ns):
            resp = client.put(f"{BASE}/1", json=self._PAYLOAD, headers=as_admin)
        assert resp.status_code == 200
        assert resp.json()["data"]["updated"] is True

    def test_404_not_found(self, as_admin):
        with patch(_GET_BUILDING, return_value=None):
            resp = client.put(f"{BASE}/9999", json=self._PAYLOAD, headers=as_admin)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "BUILDING_NOT_FOUND"

    def test_400_invalid_arcgis_layer(self, as_admin, building_ns):
        with patch(_GET_BUILDING, return_value=building_ns):
            resp = client.put(f"{BASE}/1", json={"arcgis_layer_id": ""}, headers=as_admin)
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_ARCGIS_LAYER"

    def test_401_no_token(self):
        resp = client.put(f"{BASE}/1", json=self._PAYLOAD)
        assert resp.status_code == 401

    def test_403_hr_role(self, hr_auth_headers):
        resp = client.put(f"{BASE}/1", json=self._PAYLOAD, headers=hr_auth_headers)
        assert resp.status_code == 403


# ── GET /buildings/{id}/floors ────────────────────────────────────────────────

class TestListFloors:
    def test_returns_200(self, as_hr, building_ns, floor_ns):
        with patch(_GET_BUILDING, return_value=building_ns), \
             patch(_GET_FLOORS, return_value=[floor_ns]):
            resp = client.get(f"{BASE}/1/floors", headers=as_hr)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
        assert data[0]["floor_id"] == 2
        assert data[0]["building_id"] == 1

    def test_404_building_not_found(self, as_hr):
        with patch(_GET_BUILDING, return_value=None):
            resp = client.get(f"{BASE}/9999/floors", headers=as_hr)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "BUILDING_NOT_FOUND"

    def test_401_no_token(self):
        resp = client.get(f"{BASE}/1/floors")
        assert resp.status_code == 401


# ── POST /buildings/{id}/floors ───────────────────────────────────────────────

class TestCreateFloor:
    _PAYLOAD = {
        "floor_number": 2,
        "floor_name": "Floor 2",
        "altitude_min": "10.0",
        "altitude_max": "15.0",
    }

    def test_returns_201(self, as_admin, building_ns, floor_ns):
        with patch(_GET_BUILDING, return_value=building_ns), \
             patch(_GET_FLOOR_NUM, return_value=None), \
             patch(_CREATE_FLOOR, return_value=floor_ns), \
             patch(_AUDIT, return_value=MagicMock()):
            resp = client.post(f"{BASE}/1/floors", json=self._PAYLOAD, headers=as_admin)
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["floor_id"] == 2
        assert data["building_id"] == 1
        assert data["floor_name"] == "Floor 2"

    def test_404_building_not_found(self, as_admin):
        with patch(_GET_BUILDING, return_value=None):
            resp = client.post(f"{BASE}/9999/floors", json=self._PAYLOAD, headers=as_admin)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "BUILDING_NOT_FOUND"

    def test_400_invalid_altitude(self, as_admin, building_ns):
        payload = {**self._PAYLOAD, "altitude_min": "15.0", "altitude_max": "10.0"}
        with patch(_GET_BUILDING, return_value=building_ns):
            resp = client.post(f"{BASE}/1/floors", json=payload, headers=as_admin)
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_ALTITUDE_RANGE"

    def test_400_equal_altitude(self, as_admin, building_ns):
        payload = {**self._PAYLOAD, "altitude_min": "10.0", "altitude_max": "10.0"}
        with patch(_GET_BUILDING, return_value=building_ns):
            resp = client.post(f"{BASE}/1/floors", json=payload, headers=as_admin)
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_ALTITUDE_RANGE"

    def test_409_floor_number_exists(self, as_admin, building_ns, floor_ns):
        with patch(_GET_BUILDING, return_value=building_ns), \
             patch(_GET_FLOOR_NUM, return_value=floor_ns):
            resp = client.post(f"{BASE}/1/floors", json=self._PAYLOAD, headers=as_admin)
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "FLOOR_NUMBER_EXISTS"

    def test_422_missing_field(self, as_admin):
        payload = {k: v for k, v in self._PAYLOAD.items() if k != "floor_number"}
        resp = client.post(f"{BASE}/1/floors", json=payload, headers=as_admin)
        assert resp.status_code == 422

    def test_401_no_token(self):
        resp = client.post(f"{BASE}/1/floors", json=self._PAYLOAD)
        assert resp.status_code == 401

    def test_403_hr_role(self, hr_auth_headers):
        resp = client.post(f"{BASE}/1/floors", json=self._PAYLOAD, headers=hr_auth_headers)
        assert resp.status_code == 403

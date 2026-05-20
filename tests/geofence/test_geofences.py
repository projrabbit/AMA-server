"""Tests for Module 3 geofence endpoints."""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import client
from tests.geofence.conftest import make_geofence

BASE = "/api/v1/geofences"

_SVC = "app.services.geofence_service"
_AUDIT = f"{_SVC}.create_audit_log"
_LIST_GEOFENCES = f"{_SVC}.get_geofences"
_GET_GEOFENCE = f"{_SVC}.get_geofence_by_id"
_GET_FLOOR = f"{_SVC}.get_floor_by_id"
_CREATE_GEOFENCE = f"{_SVC}.create_geofence"
_UPDATE_GEOFENCE = f"{_SVC}.update_geofence_fields"
_DISABLE_GEOFENCE = f"{_SVC}.disable_geofence"
_OVERLAP = f"{_SVC}.get_active_geofences_for_floor"


# ── GET /geofences ────────────────────────────────────────────────────────────

class TestListGeofences:
    def test_returns_200(self, as_hr, geofence_ns):
        with patch(_LIST_GEOFENCES, return_value=[geofence_ns]):
            resp = client.get(BASE, headers=as_hr)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        item = body["data"][0]
        assert item["geofence_id"] == 7
        assert item["geofence_rule_id"] == 7
        assert item["name"] == "Floor 2 Working Area"
        assert item["is_active"] is True

    def test_returns_empty_list(self, as_hr):
        with patch(_LIST_GEOFENCES, return_value=[]):
            resp = client.get(BASE, headers=as_hr)
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_401_no_token(self):
        resp = client.get(BASE)
        assert resp.status_code == 401

    def test_403_employee_role(self, employee_auth_headers):
        resp = client.get(BASE, headers=employee_auth_headers)
        assert resp.status_code == 403


# ── POST /geofences ───────────────────────────────────────────────────────────

class TestCreateGeofence:
    _PAYLOAD = {
        "floor_id": 2,
        "name": "Floor 2 Working Area",
        "center_lat": "10.772123",
        "center_lng": "106.657890",
        "radius_meters": "50.0",
        "altitude_min": "10.0",
        "altitude_max": "15.0",
        "allow_checkin": True,
        "allow_checkout": True,
    }

    def test_returns_201(self, as_hr, floor_ns, geofence_ns):
        with patch(_GET_FLOOR, return_value=floor_ns), \
             patch(_OVERLAP, return_value=[]), \
             patch(_CREATE_GEOFENCE, return_value=geofence_ns), \
             patch(_AUDIT, return_value=MagicMock()):
            resp = client.post(BASE, json=self._PAYLOAD, headers=as_hr)
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["geofence_id"] == 7
        assert data["geofence_rule_id"] == 7
        assert data["is_active"] is True

    def test_404_floor_not_found(self, as_hr):
        with patch(_GET_FLOOR, return_value=None):
            resp = client.post(BASE, json=self._PAYLOAD, headers=as_hr)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "FLOOR_NOT_FOUND"

    def test_400_invalid_altitude(self, as_hr, floor_ns):
        payload = {**self._PAYLOAD, "altitude_min": "15.0", "altitude_max": "10.0"}
        with patch(_GET_FLOOR, return_value=floor_ns):
            resp = client.post(BASE, json=payload, headers=as_hr)
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_ALTITUDE_RANGE"

    def test_409_overlap(self, as_hr, floor_ns, geofence_ns):
        # geofence_ns shares the same center as the payload → distance=0 < 50+50
        with patch(_GET_FLOOR, return_value=floor_ns), \
             patch(_OVERLAP, return_value=[geofence_ns]):
            resp = client.post(BASE, json=self._PAYLOAD, headers=as_hr)
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "GEOFENCE_OVERLAP"

    def test_422_missing_field(self, as_hr):
        payload = {k: v for k, v in self._PAYLOAD.items() if k != "floor_id"}
        resp = client.post(BASE, json=payload, headers=as_hr)
        assert resp.status_code == 422

    def test_401_no_token(self):
        resp = client.post(BASE, json=self._PAYLOAD)
        assert resp.status_code == 401


# ── PUT /geofences/{id} ───────────────────────────────────────────────────────

class TestUpdateGeofence:
    _PAYLOAD = {"radius_meters": "55.0"}

    def test_returns_200(self, as_hr, geofence_ns):
        with patch(_GET_GEOFENCE, return_value=geofence_ns), \
             patch(_OVERLAP, return_value=[]), \
             patch(_UPDATE_GEOFENCE, return_value=geofence_ns), \
             patch(_AUDIT, return_value=MagicMock()):
            resp = client.put(f"{BASE}/7", json=self._PAYLOAD, headers=as_hr)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["geofence_id"] == 7
        assert data["updated"] is True

    def test_404_not_found(self, as_hr):
        with patch(_GET_GEOFENCE, return_value=None):
            resp = client.put(f"{BASE}/9999", json=self._PAYLOAD, headers=as_hr)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "GEOFENCE_NOT_FOUND"

    def test_409_overlap(self, as_hr, geofence_ns):
        other = make_geofence(geofence_rule_id=8)  # same center → always overlaps
        with patch(_GET_GEOFENCE, return_value=geofence_ns), \
             patch(_OVERLAP, return_value=[other]):
            resp = client.put(f"{BASE}/7", json={"radius_meters": "100.0"}, headers=as_hr)
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "GEOFENCE_OVERLAP"

    def test_401_no_token(self):
        resp = client.put(f"{BASE}/7", json=self._PAYLOAD)
        assert resp.status_code == 401

    def test_403_employee_role(self, employee_auth_headers):
        resp = client.put(f"{BASE}/7", json=self._PAYLOAD, headers=employee_auth_headers)
        assert resp.status_code == 403


# ── DELETE /geofences/{id} ────────────────────────────────────────────────────

class TestDisableGeofence:
    def test_returns_200(self, as_hr, geofence_ns):
        with patch(_GET_GEOFENCE, return_value=geofence_ns), \
             patch(_DISABLE_GEOFENCE, return_value=geofence_ns), \
             patch(_AUDIT, return_value=MagicMock()):
            resp = client.delete(f"{BASE}/7", headers=as_hr)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["geofence_id"] == 7
        assert data["is_active"] is False

    def test_404_not_found(self, as_hr):
        with patch(_GET_GEOFENCE, return_value=None):
            resp = client.delete(f"{BASE}/9999", headers=as_hr)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "GEOFENCE_NOT_FOUND"

    def test_409_already_disabled(self, as_hr, geofence_ns):
        geofence_ns.is_active = False
        with patch(_GET_GEOFENCE, return_value=geofence_ns):
            resp = client.delete(f"{BASE}/7", headers=as_hr)
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "ALREADY_DISABLED"

    def test_401_no_token(self):
        resp = client.delete(f"{BASE}/7")
        assert resp.status_code == 401

    def test_403_employee_role(self, employee_auth_headers):
        resp = client.delete(f"{BASE}/7", headers=employee_auth_headers)
        assert resp.status_code == 403

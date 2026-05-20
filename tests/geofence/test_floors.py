"""Tests for Module 3 floor update endpoint."""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

import pytest

from tests.conftest import client

BASE = "/api/v1/floors"

_SVC = "app.services.geofence_service"
_GET_FLOOR = f"{_SVC}.get_floor_by_id"
_UPDATE_FLOOR = f"{_SVC}.update_floor_fields"


# ── PUT /floors/{id} ──────────────────────────────────────────────────────────

class TestUpdateFloor:
    _PAYLOAD = {"floor_name": "Updated Floor 2", "altitude_max": "16.0"}

    def test_returns_200(self, as_admin, floor_ns):
        with patch(_GET_FLOOR, return_value=floor_ns), \
             patch(_UPDATE_FLOOR, return_value=floor_ns):
            resp = client.put(f"{BASE}/2", json=self._PAYLOAD, headers=as_admin)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["floor_id"] == 2
        assert data["updated"] is True

    def test_404_not_found(self, as_admin):
        with patch(_GET_FLOOR, return_value=None):
            resp = client.put(f"{BASE}/9999", json=self._PAYLOAD, headers=as_admin)
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "FLOOR_NOT_FOUND"

    def test_400_invalid_altitude(self, as_admin, floor_ns):
        # Provide new altitude_min > existing altitude_max
        with patch(_GET_FLOOR, return_value=floor_ns):
            resp = client.put(f"{BASE}/2", json={"altitude_min": "20.0", "altitude_max": "15.0"}, headers=as_admin)
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_ALTITUDE_RANGE"

    def test_400_merged_altitude_invalid(self, as_admin, floor_ns):
        # New altitude_min > existing altitude_max (floor_ns.altitude_max=15.0)
        with patch(_GET_FLOOR, return_value=floor_ns):
            resp = client.put(f"{BASE}/2", json={"altitude_min": "20.0"}, headers=as_admin)
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_ALTITUDE_RANGE"

    def test_401_no_token(self):
        resp = client.put(f"{BASE}/2", json=self._PAYLOAD)
        assert resp.status_code == 401

    def test_403_hr_role(self, hr_auth_headers):
        resp = client.put(f"{BASE}/2", json=self._PAYLOAD, headers=hr_auth_headers)
        assert resp.status_code == 403

"""Tests for GET /realtime/employees-location."""
from __future__ import annotations

from unittest.mock import patch

from tests.conftest import client
from tests.report.conftest import make_realtime_location

_PATCH = "app.services.report_service.get_realtime_locations"


def _get(headers: dict, params: dict | None = None):
    return client.get("/api/v1/realtime/employees-location", headers=headers, params=params or {})


class TestRealtimeSuccess:
    def test_200_with_items(self, as_hr):
        loc = make_realtime_location()
        with patch(_PATCH, return_value=[loc]):
            resp = _get(as_hr)

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert len(body["data"]) == 1
        item = body["data"][0]
        assert item["employee_id"] == 10
        assert item["arcgis_layer_id"] == "arcgis-layer-001"
        assert item["gps_accuracy"] == 5.2

    def test_200_empty_list(self, as_admin):
        with patch(_PATCH, return_value=[]):
            resp = _get(as_admin)
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_refresh_interval_in_meta(self, as_hr):
        with patch(_PATCH, return_value=[]):
            resp = _get(as_hr)
        assert resp.json()["meta"]["refresh_interval_seconds"] == 30

    def test_filters_forwarded(self, as_hr):
        with patch(_PATCH, return_value=[]) as mock_fn:
            _get(as_hr, params={"building_id": "1", "floor_id": "2", "department_id": "3"})
        kwargs = mock_fn.call_args.kwargs
        assert kwargs["building_id"] == 1
        assert kwargs["floor_id"] == 2
        assert kwargs["department_id"] == 3

    def test_location_fields_present(self, as_hr):
        loc = make_realtime_location()
        with patch(_PATCH, return_value=[loc]):
            resp = _get(as_hr)
        item = resp.json()["data"][0]
        assert "latitude" in item
        assert "longitude" in item
        assert "floor_name" in item
        assert "building_name" in item
        assert "checked_in_at" in item


class TestRealtimeAuth:
    def test_401_no_token(self):
        resp = _get({})
        assert resp.status_code == 401

    def test_403_employee_role(self, as_employee):
        resp = _get(as_employee)
        assert resp.status_code == 403

    def test_403_manager_role(self, as_manager):
        resp = _get(as_manager)
        assert resp.status_code == 403

"""Fixtures shared across geofence module tests."""
from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.models.business import AccountRole
from tests.conftest import make_account


def make_building(
    building_id: int = 1,
    name: str = "Main Office",
    address: str = "123 Main St",
    center_lat: Decimal = Decimal("10.772123"),
    center_lng: Decimal = Decimal("106.657890"),
    total_floors: int = 5,
    arcgis_layer_id: str = "arcgis-layer-001",
    floors: list | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        building_id=building_id,
        name=name,
        address=address,
        center_lat=center_lat,
        center_lng=center_lng,
        total_floors=total_floors,
        arcgis_layer_id=arcgis_layer_id,
        floors=floors if floors is not None else [],
    )


def make_floor(
    floor_id: int = 2,
    building_id: int = 1,
    floor_number: int = 2,
    floor_name: str = "Floor 2",
    altitude_min: Decimal = Decimal("10.0"),
    altitude_max: Decimal = Decimal("15.0"),
) -> SimpleNamespace:
    return SimpleNamespace(
        floor_id=floor_id,
        building_id=building_id,
        floor_number=floor_number,
        floor_name=floor_name,
        altitude_min=altitude_min,
        altitude_max=altitude_max,
    )


def make_geofence(
    geofence_rule_id: int = 7,
    floor_id: int = 2,
    building_id: int = 1,
    name: str = "Floor 2 Working Area",
    center_lat: Decimal = Decimal("10.772123"),
    center_lng: Decimal = Decimal("106.657890"),
    allowed_radius_m: Decimal = Decimal("50.0"),
    altitude_min: Decimal = Decimal("10.0"),
    altitude_max: Decimal = Decimal("15.0"),
    allow_checkin: bool = True,
    allow_checkout: bool = True,
    is_active: bool = True,
    created_by_account_id: int = 1001,
) -> SimpleNamespace:
    cell_space = SimpleNamespace(
        cell_space_id=100,
        floor_id=floor_id,
        building_id=building_id,
        name=name,
        center_lat=center_lat,
        center_lng=center_lng,
        floor=SimpleNamespace(
            floor_id=floor_id,
            floor_name="Floor 2",
            building=SimpleNamespace(building_id=building_id, name="Main Office"),
        ),
    )
    return SimpleNamespace(
        geofence_rule_id=geofence_rule_id,
        cell_space_id=100,
        allowed_radius_m=allowed_radius_m,
        altitude_min=altitude_min,
        altitude_max=altitude_max,
        allow_checkin=allow_checkin,
        allow_checkout=allow_checkout,
        is_active=is_active,
        created_by_account_id=created_by_account_id,
        cell_space=cell_space,
    )


# ── Pytest fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def building_ns() -> SimpleNamespace:
    return make_building()


@pytest.fixture
def floor_ns() -> SimpleNamespace:
    return make_floor()


@pytest.fixture
def geofence_ns() -> SimpleNamespace:
    return make_geofence()


@pytest.fixture
def hr_auth_headers(hr_account) -> dict:
    from app.core.security import create_access_token
    data = {"sub": str(hr_account.account_id), "role": hr_account.role.value}
    token, _ = create_access_token(data)
    return {"Authorization": f"Bearer {token}"}


# ── Role-aware auth fixtures ──────────────────────────────────────────────────

_DEP_PATCH = "app.api.dependencies.get_account_by_id"


@pytest.fixture
def as_hr(hr_account, hr_auth_headers):
    with patch(_DEP_PATCH, return_value=hr_account):
        yield hr_auth_headers


@pytest.fixture
def as_admin(admin_account, admin_auth_headers):
    with patch(_DEP_PATCH, return_value=admin_account):
        yield admin_auth_headers

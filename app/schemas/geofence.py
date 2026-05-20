from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


# ── Requests ──────────────────────────────────────────────────────────────────

class CreateBuildingRequest(BaseModel):
    name: str
    address: str
    center_lat: Decimal
    center_lng: Decimal
    total_floors: int
    arcgis_layer_id: str


class UpdateBuildingRequest(BaseModel):
    name: str | None = None
    address: str | None = None
    center_lat: Decimal | None = None
    center_lng: Decimal | None = None
    total_floors: int | None = None
    arcgis_layer_id: str | None = None


class CreateFloorRequest(BaseModel):
    floor_number: int
    floor_name: str
    altitude_min: Decimal
    altitude_max: Decimal


class UpdateFloorRequest(BaseModel):
    floor_number: int | None = None
    floor_name: str | None = None
    altitude_min: Decimal | None = None
    altitude_max: Decimal | None = None


class CreateGeofenceRequest(BaseModel):
    floor_id: int
    name: str
    center_lat: Decimal
    center_lng: Decimal
    radius_meters: Decimal
    altitude_min: Decimal
    altitude_max: Decimal
    allow_checkin: bool
    allow_checkout: bool


class UpdateGeofenceRequest(BaseModel):
    name: str | None = None
    center_lat: Decimal | None = None
    center_lng: Decimal | None = None
    radius_meters: Decimal | None = None
    altitude_min: Decimal | None = None
    altitude_max: Decimal | None = None
    allow_checkin: bool | None = None
    allow_checkout: bool | None = None
    is_active: bool | None = None


# ── Sub-objects ───────────────────────────────────────────────────────────────

class FloorSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    floor_id: int
    floor_number: int | None
    floor_name: str | None
    altitude_min: Decimal | None
    altitude_max: Decimal | None


class BuildingListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    building_id: int
    name: str | None
    address: str | None
    center_lat: Decimal | None
    center_lng: Decimal | None
    total_floors: int | None
    arcgis_layer_id: str | None
    floors: list[FloorSummary] | None = None


class FloorListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    floor_id: int
    building_id: int
    floor_number: int | None
    floor_name: str | None
    altitude_min: Decimal | None
    altitude_max: Decimal | None


class GeofenceListItem(BaseModel):
    geofence_id: int
    geofence_rule_id: int
    name: str | None
    building_id: int | None
    building_name: str | None
    floor_id: int | None
    floor_name: str | None
    center_lat: Decimal | None
    center_lng: Decimal | None
    radius_meters: Decimal | None
    altitude_min: Decimal | None
    altitude_max: Decimal | None
    allow_checkin: bool | None
    allow_checkout: bool | None
    is_active: bool | None
    created_by_account_id: int | None


# ── Response data ─────────────────────────────────────────────────────────────

class CreateBuildingData(BaseModel):
    building_id: int
    name: str | None
    arcgis_layer_valid: bool


class UpdateBuildingData(BaseModel):
    building_id: int
    updated: bool


class CreateFloorData(BaseModel):
    floor_id: int
    building_id: int
    floor_name: str | None


class UpdateFloorData(BaseModel):
    floor_id: int
    updated: bool


class CreateGeofenceData(BaseModel):
    geofence_id: int
    geofence_rule_id: int
    is_active: bool


class UpdateGeofenceData(BaseModel):
    geofence_id: int
    updated: bool


class DisableGeofenceData(BaseModel):
    geofence_id: int
    is_active: bool

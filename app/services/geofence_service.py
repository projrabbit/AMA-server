from __future__ import annotations

import math

from fastapi import HTTPException, status

from app.models.business import AuditActionType
from app.repositories.auth_repository import create_audit_log
from app.repositories.geofence_repository import (
    create_building,
    create_floor,
    create_geofence,
    disable_geofence,
    get_active_geofences_for_floor,
    get_building_by_id,
    get_building_by_name,
    get_buildings,
    get_floor_by_id,
    get_floor_by_number_and_building,
    get_floors_for_building,
    get_geofence_by_id,
    get_geofences,
    update_building_fields,
    update_floor_fields,
    update_geofence_fields,
)
from app.schemas.geofence import (
    BuildingListItem,
    CreateBuildingData,
    CreateFloorData,
    CreateGeofenceData,
    DisableGeofenceData,
    FloorListItem,
    GeofenceListItem,
    UpdateBuildingData,
    UpdateFloorData,
    UpdateGeofenceData,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _validate_arcgis_layer(arcgis_layer_id: str | None) -> None:
    # TODO: replace with real ArcGIS REST API validation when available
    if not arcgis_layer_id or not arcgis_layer_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_ARCGIS_LAYER",
                "message": "ArcGIS layer ID is invalid or missing",
                "details": {},
            },
        )


def _validate_altitude(altitude_min, altitude_max) -> None:
    if altitude_min is not None and altitude_max is not None:
        if float(altitude_min) >= float(altitude_max):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_ALTITUDE_RANGE",
                    "message": "altitude_min must be less than altitude_max",
                    "details": {},
                },
            )


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


def _circles_overlap(
    lat1: float, lon1: float, r1: float,
    lat2: float, lon2: float, r2: float,
) -> bool:
    return _haversine_m(lat1, lon1, lat2, lon2) < (r1 + r2)


def _geofence_to_item(rule) -> GeofenceListItem:
    cs = rule.cell_space
    fl = cs.floor if cs else None
    bld = fl.building if fl else None
    return GeofenceListItem(
        geofence_id=rule.geofence_rule_id,
        geofence_rule_id=rule.geofence_rule_id,
        name=cs.name if cs else None,
        building_id=cs.building_id if cs else None,
        building_name=bld.name if bld else None,
        floor_id=cs.floor_id if cs else None,
        floor_name=fl.floor_name if fl else None,
        center_lat=cs.center_lat if cs else None,
        center_lng=cs.center_lng if cs else None,
        radius_meters=rule.allowed_radius_m,
        altitude_min=rule.altitude_min,
        altitude_max=rule.altitude_max,
        allow_checkin=rule.allow_checkin,
        allow_checkout=rule.allow_checkout,
        is_active=rule.is_active,
        created_by_account_id=rule.created_by_account_id,
    )


# ── Buildings ─────────────────────────────────────────────────────────────────

def list_buildings_svc(db, *, q: str | None, include_floors: bool) -> list[BuildingListItem]:
    rows = get_buildings(db, q=q)
    result = []
    for b in rows:
        item = BuildingListItem.model_validate(b)
        if not include_floors:
            item.floors = None
        result.append(item)
    return result


def create_building_svc(db, account_id: int, body, ip_address: str | None) -> CreateBuildingData:
    _validate_arcgis_layer(body.arcgis_layer_id)
    if get_building_by_name(db, body.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "BUILDING_NAME_EXISTS", "message": "Building name already exists", "details": {}},
        )
    building = create_building(
        db,
        name=body.name,
        address=body.address,
        center_lat=body.center_lat,
        center_lng=body.center_lng,
        total_floors=body.total_floors,
        arcgis_layer_id=body.arcgis_layer_id,
    )
    create_audit_log(
        db,
        account_id=account_id,
        action_type=AuditActionType.create,
        target_entity="BUILDING",
        target_id=building.building_id,
        ip_address=ip_address,
    )
    return CreateBuildingData(
        building_id=building.building_id,
        name=building.name,
        arcgis_layer_valid=True,
    )


def update_building_svc(
    db, account_id: int, building_id: int, body, ip_address: str | None
) -> UpdateBuildingData:
    building = get_building_by_id(db, building_id)
    if building is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BUILDING_NOT_FOUND", "message": "Building not found", "details": {}},
        )
    if body.arcgis_layer_id is not None:
        _validate_arcgis_layer(body.arcgis_layer_id)
    update_building_fields(
        db,
        building,
        name=body.name,
        address=body.address,
        center_lat=body.center_lat,
        center_lng=body.center_lng,
        total_floors=body.total_floors,
        arcgis_layer_id=body.arcgis_layer_id,
    )
    return UpdateBuildingData(building_id=building_id, updated=True)


# ── Floors ────────────────────────────────────────────────────────────────────

def list_floors_svc(db, building_id: int) -> list[FloorListItem]:
    if get_building_by_id(db, building_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BUILDING_NOT_FOUND", "message": "Building not found", "details": {}},
        )
    floors = get_floors_for_building(db, building_id)
    return [FloorListItem.model_validate(f) for f in floors]


def create_floor_svc(
    db, account_id: int, building_id: int, body, ip_address: str | None
) -> CreateFloorData:
    if get_building_by_id(db, building_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BUILDING_NOT_FOUND", "message": "Building not found", "details": {}},
        )
    _validate_altitude(body.altitude_min, body.altitude_max)
    if get_floor_by_number_and_building(db, body.floor_number, building_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "FLOOR_NUMBER_EXISTS",
                "message": "Floor number already exists in this building",
                "details": {},
            },
        )
    floor = create_floor(
        db,
        building_id=building_id,
        floor_number=body.floor_number,
        floor_name=body.floor_name,
        altitude_min=body.altitude_min,
        altitude_max=body.altitude_max,
    )
    create_audit_log(
        db,
        account_id=account_id,
        action_type=AuditActionType.create,
        target_entity="FLOOR",
        target_id=floor.floor_id,
        ip_address=ip_address,
    )
    return CreateFloorData(
        floor_id=floor.floor_id,
        building_id=floor.building_id,
        floor_name=floor.floor_name,
    )


def update_floor_svc(db, floor_id: int, body) -> UpdateFloorData:
    floor = get_floor_by_id(db, floor_id)
    if floor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "FLOOR_NOT_FOUND", "message": "Floor not found", "details": {}},
        )
    new_min = body.altitude_min if body.altitude_min is not None else floor.altitude_min
    new_max = body.altitude_max if body.altitude_max is not None else floor.altitude_max
    _validate_altitude(new_min, new_max)
    update_floor_fields(
        db,
        floor,
        floor_number=body.floor_number,
        floor_name=body.floor_name,
        altitude_min=body.altitude_min,
        altitude_max=body.altitude_max,
    )
    return UpdateFloorData(floor_id=floor_id, updated=True)


# ── Geofences ─────────────────────────────────────────────────────────────────

def list_geofences_svc(
    db, *, building_id: int | None, floor_id: int | None, is_active: bool | None
) -> list[GeofenceListItem]:
    rules = get_geofences(db, building_id=building_id, floor_id=floor_id, is_active=is_active)
    return [_geofence_to_item(r) for r in rules]


def create_geofence_svc(
    db, account_id: int, body, ip_address: str | None
) -> CreateGeofenceData:
    floor = get_floor_by_id(db, body.floor_id)
    if floor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "FLOOR_NOT_FOUND", "message": "Floor not found", "details": {}},
        )
    _validate_altitude(body.altitude_min, body.altitude_max)
    for other in get_active_geofences_for_floor(db, body.floor_id):
        cs = other.cell_space
        if _circles_overlap(
            float(body.center_lat), float(body.center_lng), float(body.radius_meters),
            float(cs.center_lat), float(cs.center_lng), float(other.allowed_radius_m),
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "GEOFENCE_OVERLAP",
                    "message": "New geofence overlaps an active geofence on the same floor",
                    "details": {},
                },
            )
    rule = create_geofence(
        db,
        floor_id=body.floor_id,
        building_id=floor.building_id,
        name=body.name,
        center_lat=body.center_lat,
        center_lng=body.center_lng,
        allowed_radius_m=body.radius_meters,
        altitude_min=body.altitude_min,
        altitude_max=body.altitude_max,
        allow_checkin=body.allow_checkin,
        allow_checkout=body.allow_checkout,
        created_by_account_id=account_id,
    )
    create_audit_log(
        db,
        account_id=account_id,
        action_type=AuditActionType.create,
        target_entity="GEOFENCE_RULE",
        target_id=rule.geofence_rule_id,
        ip_address=ip_address,
    )
    return CreateGeofenceData(
        geofence_id=rule.geofence_rule_id,
        geofence_rule_id=rule.geofence_rule_id,
        is_active=True,
    )


def update_geofence_svc(
    db, account_id: int, geofence_id: int, body, ip_address: str | None
) -> UpdateGeofenceData:
    rule = get_geofence_by_id(db, geofence_id)
    if rule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "GEOFENCE_NOT_FOUND", "message": "Geofence not found", "details": {}},
        )
    new_min = body.altitude_min if body.altitude_min is not None else rule.altitude_min
    new_max = body.altitude_max if body.altitude_max is not None else rule.altitude_max
    _validate_altitude(new_min, new_max)

    cs = rule.cell_space
    new_lat = float(body.center_lat if body.center_lat is not None else cs.center_lat)
    new_lng = float(body.center_lng if body.center_lng is not None else cs.center_lng)
    new_radius = float(body.radius_meters if body.radius_meters is not None else rule.allowed_radius_m)

    for other in get_active_geofences_for_floor(db, cs.floor_id, exclude_id=geofence_id):
        other_cs = other.cell_space
        if _circles_overlap(
            new_lat, new_lng, new_radius,
            float(other_cs.center_lat), float(other_cs.center_lng), float(other.allowed_radius_m),
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "GEOFENCE_OVERLAP",
                    "message": "Updated geofence overlaps an existing active geofence",
                    "details": {},
                },
            )
    update_geofence_fields(
        db,
        rule,
        cs,
        name=body.name,
        center_lat=body.center_lat,
        center_lng=body.center_lng,
        allowed_radius_m=body.radius_meters,
        altitude_min=body.altitude_min,
        altitude_max=body.altitude_max,
        allow_checkin=body.allow_checkin,
        allow_checkout=body.allow_checkout,
        is_active=body.is_active,
    )
    create_audit_log(
        db,
        account_id=account_id,
        action_type=AuditActionType.update,
        target_entity="GEOFENCE_RULE",
        target_id=geofence_id,
        ip_address=ip_address,
    )
    return UpdateGeofenceData(geofence_id=geofence_id, updated=True)


def disable_geofence_svc(
    db, account_id: int, geofence_id: int, ip_address: str | None
) -> DisableGeofenceData:
    rule = get_geofence_by_id(db, geofence_id)
    if rule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "GEOFENCE_NOT_FOUND", "message": "Geofence not found", "details": {}},
        )
    if rule.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "ALREADY_DISABLED", "message": "Geofence is already inactive", "details": {}},
        )
    disable_geofence(db, rule)
    create_audit_log(
        db,
        account_id=account_id,
        action_type=AuditActionType.delete,
        target_entity="GEOFENCE_RULE",
        target_id=geofence_id,
        ip_address=ip_address,
    )
    return DisableGeofenceData(geofence_id=geofence_id, is_active=False)

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.gis import Building, CellSpace, Floor, GeofenceRule


# ── Buildings ─────────────────────────────────────────────────────────────────

def get_buildings(db: Session, *, q: str | None) -> list[Building]:
    stmt = select(Building).options(joinedload(Building.floors))
    if q:
        stmt = stmt.where(
            Building.name.ilike(f"%{q}%") | Building.address.ilike(f"%{q}%")
        )
    return list(db.execute(stmt).unique().scalars().all())


def get_building_by_id(db: Session, building_id: int) -> Building | None:
    return db.get(Building, building_id)


def get_building_by_name(db: Session, name: str) -> Building | None:
    return db.execute(select(Building).where(Building.name == name)).scalars().first()


def create_building(
    db: Session,
    *,
    name: str,
    address: str,
    center_lat,
    center_lng,
    total_floors: int,
    arcgis_layer_id: str,
) -> Building:
    building = Building(
        name=name,
        address=address,
        center_lat=center_lat,
        center_lng=center_lng,
        total_floors=total_floors,
        arcgis_layer_id=arcgis_layer_id,
    )
    db.add(building)
    db.commit()
    db.refresh(building)
    return building


def update_building_fields(db: Session, building: Building, **fields) -> Building:
    for key, value in fields.items():
        if value is not None:
            setattr(building, key, value)
    db.commit()
    db.refresh(building)
    return building


# ── Floors ────────────────────────────────────────────────────────────────────

def get_floors_for_building(db: Session, building_id: int) -> list[Floor]:
    stmt = (
        select(Floor)
        .where(Floor.building_id == building_id)
        .order_by(Floor.floor_number)
    )
    return list(db.execute(stmt).scalars().all())


def get_floor_by_id(db: Session, floor_id: int) -> Floor | None:
    return db.get(Floor, floor_id)


def get_floor_by_number_and_building(
    db: Session, floor_number: int, building_id: int
) -> Floor | None:
    stmt = select(Floor).where(
        Floor.floor_number == floor_number,
        Floor.building_id == building_id,
    )
    return db.execute(stmt).scalars().first()


def create_floor(
    db: Session,
    *,
    building_id: int,
    floor_number: int,
    floor_name: str,
    altitude_min,
    altitude_max,
) -> Floor:
    floor = Floor(
        building_id=building_id,
        floor_number=floor_number,
        floor_name=floor_name,
        altitude_min=altitude_min,
        altitude_max=altitude_max,
    )
    db.add(floor)
    db.commit()
    db.refresh(floor)
    return floor


def update_floor_fields(db: Session, floor: Floor, **fields) -> Floor:
    for key, value in fields.items():
        if value is not None:
            setattr(floor, key, value)
    db.commit()
    db.refresh(floor)
    return floor


# ── Geofences ─────────────────────────────────────────────────────────────────

def get_geofences(
    db: Session,
    *,
    building_id: int | None,
    floor_id: int | None,
    is_active: bool | None,
) -> list[GeofenceRule]:
    stmt = (
        select(GeofenceRule)
        .join(GeofenceRule.cell_space)
        .options(
            joinedload(GeofenceRule.cell_space)
            .joinedload(CellSpace.floor)
            .joinedload(Floor.building)
        )
    )
    if building_id is not None:
        stmt = stmt.where(CellSpace.building_id == building_id)
    if floor_id is not None:
        stmt = stmt.where(CellSpace.floor_id == floor_id)
    if is_active is not None:
        stmt = stmt.where(GeofenceRule.is_active == is_active)
    return list(db.execute(stmt).unique().scalars().all())


def get_geofence_by_id(db: Session, geofence_rule_id: int) -> GeofenceRule | None:
    stmt = (
        select(GeofenceRule)
        .where(GeofenceRule.geofence_rule_id == geofence_rule_id)
        .options(
            joinedload(GeofenceRule.cell_space)
            .joinedload(CellSpace.floor)
            .joinedload(Floor.building)
        )
    )
    return db.execute(stmt).unique().scalars().first()


def get_active_geofences_for_floor(
    db: Session, floor_id: int, exclude_id: int | None = None
) -> list[GeofenceRule]:
    stmt = (
        select(GeofenceRule)
        .join(GeofenceRule.cell_space)
        .options(joinedload(GeofenceRule.cell_space))
        .where(CellSpace.floor_id == floor_id, GeofenceRule.is_active == True)  # noqa: E712
    )
    if exclude_id is not None:
        stmt = stmt.where(GeofenceRule.geofence_rule_id != exclude_id)
    return list(db.execute(stmt).unique().scalars().all())


def create_geofence(
    db: Session,
    *,
    floor_id: int,
    building_id: int,
    name: str,
    center_lat,
    center_lng,
    allowed_radius_m,
    altitude_min,
    altitude_max,
    allow_checkin: bool,
    allow_checkout: bool,
    created_by_account_id: int,
) -> GeofenceRule:
    cell_space = CellSpace(
        floor_id=floor_id,
        building_id=building_id,
        name=name,
        center_lat=center_lat,
        center_lng=center_lng,
    )
    db.add(cell_space)
    db.flush()

    rule = GeofenceRule(
        cell_space_id=cell_space.cell_space_id,
        allowed_radius_m=allowed_radius_m,
        altitude_min=altitude_min,
        altitude_max=altitude_max,
        allow_checkin=allow_checkin,
        allow_checkout=allow_checkout,
        is_active=True,
        created_by_account_id=created_by_account_id,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update_geofence_fields(
    db: Session,
    rule: GeofenceRule,
    cell_space: CellSpace,
    **fields,
) -> GeofenceRule:
    _cell_space_fields = {"name", "center_lat", "center_lng"}
    _rule_fields = {
        "allowed_radius_m", "altitude_min", "altitude_max",
        "allow_checkin", "allow_checkout", "is_active",
    }
    for key, value in fields.items():
        if value is None:
            continue
        if key in _cell_space_fields:
            setattr(cell_space, key, value)
        elif key in _rule_fields:
            setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return rule


def disable_geofence(db: Session, rule: GeofenceRule) -> GeofenceRule:
    rule.is_active = False
    db.commit()
    db.refresh(rule)
    return rule

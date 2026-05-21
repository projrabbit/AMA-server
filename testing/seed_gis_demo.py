"""Seed a small, idempotent GIS demo dataset.

Inserts (or upserts by name):
- 1 building       : "Demo Office HCM"  @ 268 Ly Thuong Kiet, Q.10, HCMC
- 2 floors         : Floor 1 (0-4 m),  Floor 2 (4-8 m)
- 6 rooms          : 101/102/103  on F1, 201/202/203 on F2
- 6 geofence rules : one per room, radius 5 m, ~25 m apart so they do not overlap

Idempotency: matches existing rows by name / (building_id, floor_number) /
(floor_id, name).  Re-running this script does NOT create duplicates.

Usage:
    uv run python testing/seed_gis_demo.py
"""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

# Allow `python testing/seed_gis_demo.py` from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.gis import Building, CellSpace, Floor, GeofenceRule


# ── Demo dataset definition ───────────────────────────────────────────────────

# Building is hosted on the OSM polygon of Nha thi dau Phu Tho (219 Ly Thuong
# Kiet, P.15, Q.11, HCMC). The polygon's 4 main corners form a clean rotated
# rectangle ~134 m x 102 m, so the 3D shell in gis_view.html can match the
# basemap polygon edge-for-edge. center_lat/lng is the polygon centroid.
BUILDING = {
    "name": "Demo Office HCM",
    "address": "Nha thi dau Phu Tho, 219 Ly Thuong Kiet, District 11, Ho Chi Minh City",
    "center_lat": Decimal("10.76897572"),
    "center_lng": Decimal("106.65774758"),
    "total_floors": 2,
    "arcgis_layer_id": "demo-office-hcm",
}

FLOORS = [
    {
        "floor_number": 1,
        "floor_name": "Floor 1 - Reception & Workspace",
        "altitude_min": Decimal("0.00"),
        "altitude_max": Decimal("20.00"),
    },
    {
        "floor_number": 2,
        "floor_name": "Floor 2 - Management & Meetings",
        "altitude_min": Decimal("20.00"),
        "altitude_max": Decimal("40.00"),
    },
]

# Four rooms per floor, one per quadrant of the rotated rectangle (SW, SE,
# NW, NE). A 2 m cross-shaped corridor runs through the centre of each
# floor (long-axis 2/134 + short-axis 2/102 fractional widths). Each room
# fills ~66 m x ~50 m of a single quadrant.
#
# Room name -> quadrant mapping (by sorted name index):
#   101 / 201 -> SW    102 / 202 -> SE    103 / 203 -> NW    104 / 204 -> NE
#
# Adjacent quadrant centres are >=51 m apart, so the geofence overlap
# check (4 + 4 = 8 m) clears trivially.
ROOMS = [
    # Floor 1 - 4 corners
    {"floor_number": 1, "name": "Room 101 - Reception",    "lat": "10.76861720", "lng": "106.65760250"},  # SW
    {"floor_number": 1, "name": "Room 102 - Workspace",    "lat": "10.76874030", "lng": "106.65805880"},  # SE
    {"floor_number": 1, "name": "Room 103 - Break Room",   "lat": "10.76921120", "lng": "106.65743650"},  # NW
    {"floor_number": 1, "name": "Room 104 - Engineering",  "lat": "10.76933430", "lng": "106.65789280"},  # NE
    # Floor 2 - same quadrants, different altitude band
    {"floor_number": 2, "name": "Room 201 - Manager Office", "lat": "10.76861720", "lng": "106.65760250"},  # SW
    {"floor_number": 2, "name": "Room 202 - Meeting Room",   "lat": "10.76874030", "lng": "106.65805880"},  # SE
    {"floor_number": 2, "name": "Room 203 - HR Office",      "lat": "10.76921120", "lng": "106.65743650"},  # NW
    {"floor_number": 2, "name": "Room 204 - Finance",        "lat": "10.76933430", "lng": "106.65789280"},  # NE
]

# created_by_account_id for geofence rules.
# 1001 is the seeded admin (linh.tran@example.com) from the c2495ccaca1b migration.
SEED_ACCOUNT_ID = 1001
RADIUS_METERS = Decimal("4.00")


# ── Idempotent helpers ────────────────────────────────────────────────────────

def upsert_building(db: Session) -> Building:
    building = db.execute(
        select(Building).where(Building.name == BUILDING["name"])
    ).scalars().first()
    if building is None:
        building = Building(**BUILDING)
        db.add(building)
        db.flush()
        print(f"  + created building '{building.name}' (id={building.building_id})")
        return building

    for key, value in BUILDING.items():
        setattr(building, key, value)
    print(f"  = reused building '{building.name}' (id={building.building_id})")
    return building


def upsert_floor(db: Session, building: Building, spec: dict) -> Floor:
    floor = db.execute(
        select(Floor).where(
            Floor.building_id == building.building_id,
            Floor.floor_number == spec["floor_number"],
        )
    ).scalars().first()
    if floor is None:
        floor = Floor(building_id=building.building_id, **spec)
        db.add(floor)
        db.flush()
        print(f"    + created floor {spec['floor_number']} '{spec['floor_name']}' (id={floor.floor_id})")
        return floor

    for key, value in spec.items():
        setattr(floor, key, value)
    print(f"    = reused floor {spec['floor_number']} '{spec['floor_name']}' (id={floor.floor_id})")
    return floor


def upsert_room(
    db: Session,
    building: Building,
    floor: Floor,
    room: dict,
) -> tuple[CellSpace, GeofenceRule]:
    cell_space = db.execute(
        select(CellSpace).where(
            CellSpace.floor_id == floor.floor_id,
            CellSpace.name == room["name"],
        )
    ).scalars().first()

    if cell_space is None:
        cell_space = CellSpace(
            floor_id=floor.floor_id,
            building_id=building.building_id,
            name=room["name"],
            address=BUILDING["address"],
            center_lat=Decimal(room["lat"]),
            center_lng=Decimal(room["lng"]),
            total_floors=BUILDING["total_floors"],
            arcgis_layer_id=f"demo-office-hcm-f{floor.floor_number}-{room['name'].split()[1].lower()}",
        )
        db.add(cell_space)
        db.flush()
        action = "+ created"
    else:
        cell_space.center_lat = Decimal(room["lat"])
        cell_space.center_lng = Decimal(room["lng"])
        cell_space.address = BUILDING["address"]
        cell_space.building_id = building.building_id
        cell_space.total_floors = BUILDING["total_floors"]
        action = "= reused"
    print(f"      {action} room '{cell_space.name}' (cell_space_id={cell_space.cell_space_id})")

    rule = db.execute(
        select(GeofenceRule).where(GeofenceRule.cell_space_id == cell_space.cell_space_id)
    ).scalars().first()

    rule_fields = dict(
        allowed_radius_m=RADIUS_METERS,
        altitude_min=floor.altitude_min,
        altitude_max=floor.altitude_max,
        allow_checkin=True,
        allow_checkout=True,
        is_active=True,
        created_by_account_id=SEED_ACCOUNT_ID,
    )
    if rule is None:
        rule = GeofenceRule(cell_space_id=cell_space.cell_space_id, **rule_fields)
        db.add(rule)
        db.flush()
        print(f"        + created geofence rule (id={rule.geofence_rule_id}, radius={RADIUS_METERS} m)")
    else:
        for key, value in rule_fields.items():
            setattr(rule, key, value)
        print(f"        = reused geofence rule (id={rule.geofence_rule_id}, radius={RADIUS_METERS} m)")
    return cell_space, rule


# ── Entry point ───────────────────────────────────────────────────────────────

def cleanup_orphan_rooms(db: Session, building: Building, valid_names: set[str]) -> None:
    """Remove cell_spaces (and their geofence_rule) in this building whose
    name is not in `valid_names`. Keeps the demo building's room set in sync
    with ROOMS after renames or count changes."""
    orphans = db.execute(
        select(CellSpace).where(
            CellSpace.building_id == building.building_id,
            CellSpace.name.notin_(valid_names),
        )
    ).scalars().all()
    for cs in orphans:
        rule = db.execute(
            select(GeofenceRule).where(GeofenceRule.cell_space_id == cs.cell_space_id)
        ).scalars().first()
        if rule is not None:
            db.delete(rule)
        db.delete(cs)
        print(f"      - removed orphan room '{cs.name}' (cell_space_id={cs.cell_space_id})")


def main() -> int:
    db = SessionLocal()
    try:
        print("Seeding GIS demo dataset:")
        building = upsert_building(db)

        floors_by_number: dict[int, Floor] = {}
        for spec in FLOORS:
            floors_by_number[spec["floor_number"]] = upsert_floor(db, building, spec)

        for room in ROOMS:
            floor = floors_by_number[room["floor_number"]]
            upsert_room(db, building, floor, room)

        cleanup_orphan_rooms(db, building, {r["name"] for r in ROOMS})

        db.commit()
        print("\nDone. Building, floors, and geofences are present in schema 'gis'.")
        print(f"Use building_id={building.building_id} to inspect via API.")
        return 0
    except Exception as exc:
        db.rollback()
        print(f"\nERROR: seed failed: {exc!r}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())

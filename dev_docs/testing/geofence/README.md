# Geofence Test Suite

Test files for `Module 3: Geofence` (`/api/v1/buildings/*`, `/api/v1/floors/*`, `/api/v1/geofences/*`).

## Files

| File | Endpoint(s) | Tests |
|------|-------------|-------|
| `tests/geofence/test_buildings.py` | `GET /buildings`, `POST /buildings`, `PUT /buildings/{id}`, `GET /buildings/{id}/floors`, `POST /buildings/{id}/floors` | 27 |
| `tests/geofence/test_floors.py` | `PUT /floors/{id}` | 6 |
| `tests/geofence/test_geofences.py` | `GET /geofences`, `POST /geofences`, `PUT /geofences/{id}`, `DELETE /geofences/{id}` | 20 |

**Total: 53 tests, all passing.**

## How To Run

```bash
uv run pytest tests/geofence/ -v
uv run pytest tests/geofence/test_buildings.py -v
uv run pytest tests/geofence/test_floors.py -v
uv run pytest tests/geofence/test_geofences.py -v
uv run pytest tests/geofence/ -v --cov=app --cov-report=term-missing
uv run pytest tests/geofence/ -x
```

## Architecture

```
TestClient (no live server)
    └── app.dependency_overrides[get_db] = MagicMock session
    └── unittest.mock.patch() for service-layer functions
    └── SimpleNamespace fixtures (Pydantic from_attributes=True compatible)
    └── Geofence is a CellSpace + GeofenceRule pair; make_geofence() builds a
        SimpleNamespace with a nested .cell_space that has .floor.building
    └── Haversine overlap tested by placing two geofences at identical coordinates
        (distance=0 < r1+r2 always triggers overlap)
```

## Patch Paths Quick Reference

```python
# Service-level patches (service imports repository at module level)
"app.services.geofence_service.get_buildings"
"app.services.geofence_service.get_building_by_id"
"app.services.geofence_service.get_building_by_name"
"app.services.geofence_service.create_building"
"app.services.geofence_service.update_building_fields"
"app.services.geofence_service.get_floors_for_building"
"app.services.geofence_service.get_floor_by_id"
"app.services.geofence_service.get_floor_by_number_and_building"
"app.services.geofence_service.create_floor"
"app.services.geofence_service.update_floor_fields"
"app.services.geofence_service.get_geofences"
"app.services.geofence_service.get_geofence_by_id"
"app.services.geofence_service.get_active_geofences_for_floor"
"app.services.geofence_service.create_geofence"
"app.services.geofence_service.update_geofence_fields"
"app.services.geofence_service.disable_geofence"
"app.services.geofence_service.create_audit_log"

# Dependency-level patch (role guard resolution)
"app.api.dependencies.get_account_by_id"
```

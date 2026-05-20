# Geofence Module — Test Report

**Date**: 2026-05-20
**Environment**: Local (no live database — DB dependency fully mocked)
**Test runner**: `uv run pytest tests/geofence/ -v`
**Result**: ✅ 53 / 53 passed — 0 failed — 0 skipped
**Duration**: ~17s

---

## Coverage By Endpoint

| Endpoint | Tests | Result |
|----------|-------|--------|
| `GET /buildings` | 5 | ✅ All pass |
| `POST /buildings` | 6 | ✅ All pass |
| `PUT /buildings/{id}` | 5 | ✅ All pass |
| `GET /buildings/{id}/floors` | 3 | ✅ All pass |
| `POST /buildings/{id}/floors` | 8 | ✅ All pass |
| `PUT /floors/{id}` | 6 | ✅ All pass |
| `GET /geofences` | 4 | ✅ All pass |
| `POST /geofences` | 6 | ✅ All pass |
| `PUT /geofences/{id}` | 5 | ✅ All pass |
| `DELETE /geofences/{id}` | 5 | ✅ All pass |

---

## Test Infrastructure

### Strategy

All tests use FastAPI's `TestClient` with `get_db` globally overridden by a `MagicMock` — no real PostgreSQL connection. Repository functions are patched at the service-import level (`app.services.geofence_service.<fn>`).

A geofence in the data model is a `CellSpace + GeofenceRule` pair. The `make_geofence()` factory builds a `SimpleNamespace` with a nested `.cell_space` containing `.floor.building`, which matches the join chain `GeofenceRule → CellSpace → Floor → Building` used in `_geofence_to_item()`.

The Haversine overlap test works by returning a geofence with the same center coordinates as the request — distance = 0 < r1 + r2, so `_circles_overlap()` always returns True.

The ArcGIS validation is a stub: any non-empty string passes; an empty string raises 400 `INVALID_ARCGIS_LAYER`.

The altitude merge-then-check on `PUT /floors/{id}` is tested by sending only `altitude_min=20.0` with a fixture that has `altitude_max=15.0` — the service merges to (20.0, 15.0) and raises 400.

### Patch Paths Used

| Patch target | Used in |
|---|---|
| `app.services.geofence_service.get_buildings` | `test_buildings.py` |
| `app.services.geofence_service.get_building_by_id` | `test_buildings.py` |
| `app.services.geofence_service.get_building_by_name` | `test_buildings.py` |
| `app.services.geofence_service.create_building` | `test_buildings.py` |
| `app.services.geofence_service.update_building_fields` | `test_buildings.py` |
| `app.services.geofence_service.get_floors_for_building` | `test_buildings.py` |
| `app.services.geofence_service.get_floor_by_number_and_building` | `test_buildings.py` |
| `app.services.geofence_service.create_floor` | `test_buildings.py` |
| `app.services.geofence_service.get_floor_by_id` | `test_buildings.py`, `test_floors.py`, `test_geofences.py` |
| `app.services.geofence_service.update_floor_fields` | `test_floors.py` |
| `app.services.geofence_service.get_geofences` | `test_geofences.py` |
| `app.services.geofence_service.get_geofence_by_id` | `test_geofences.py` |
| `app.services.geofence_service.get_active_geofences_for_floor` | `test_geofences.py` |
| `app.services.geofence_service.create_geofence` | `test_geofences.py` |
| `app.services.geofence_service.update_geofence_fields` | `test_geofences.py` |
| `app.services.geofence_service.disable_geofence` | `test_geofences.py` |
| `app.services.geofence_service.create_audit_log` | `test_buildings.py`, `test_geofences.py` |
| `app.api.dependencies.get_account_by_id` | `conftest.py` (via role fixtures) |

### Test Fixtures

| Fixture | Type | Purpose |
|---------|------|---------|
| `as_hr` | `dict` (headers) | HR auth headers + `get_account_by_id` patched to return HR account |
| `as_admin` | `dict` (headers) | Admin auth headers + `get_account_by_id` patched to return admin account |
| `hr_auth_headers` | `dict` (headers) | Raw HR headers (no patch) — used for 403 tests on admin-only endpoints |
| `employee_auth_headers` | `dict` (headers) | Raw employee headers — used for 403 tests on HR/admin-only endpoints |
| `building_ns` | `SimpleNamespace` | Building with `building_id=1, name="Main Office", floors=[]` |
| `floor_ns` | `SimpleNamespace` | Floor with `floor_id=2, building_id=1, altitude_min=10, altitude_max=15` |
| `geofence_ns` | `SimpleNamespace` | GeofenceRule with nested `cell_space.floor.building`; `geofence_rule_id=7, is_active=True` |

---

## Detailed Results

### `GET /buildings` — 5 tests

#### Success cases (3)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200` — list with one building, success=True | ✅ Pass |
| 2 | `test_floors_none_without_include_floors` — floors field is null by default | ✅ Pass |
| 3 | `test_floors_populated_with_include_floors` — floors list populated when ?include_floors=true | ✅ Pass |

#### Error cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 4 | `test_401_no_token` | 401 | ✅ Pass |
| 5 | `test_403_employee_role` | 403 | ✅ Pass |

---

### `POST /buildings` — 6 tests

#### Success cases (1)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_201` — building_id + arcgis_layer_valid=True | ✅ Pass |

#### Error cases (5)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 2 | `test_400_invalid_arcgis_layer` — empty arcgis_layer_id | 400 `INVALID_ARCGIS_LAYER` | ✅ Pass |
| 3 | `test_409_name_exists` — building name already taken | 409 `BUILDING_NAME_EXISTS` | ✅ Pass |
| 4 | `test_422_missing_name` — name field omitted | 422 | ✅ Pass |
| 5 | `test_401_no_token` | 401 | ✅ Pass |
| 6 | `test_403_hr_role` — HR cannot create buildings (admin only) | 403 | ✅ Pass |

---

### `PUT /buildings/{id}` — 5 tests

#### Success cases (1)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200` — updated=True | ✅ Pass |

#### Error cases (4)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 2 | `test_404_not_found` | 404 `BUILDING_NOT_FOUND` | ✅ Pass |
| 3 | `test_400_invalid_arcgis_layer` — empty string in body | 400 `INVALID_ARCGIS_LAYER` | ✅ Pass |
| 4 | `test_401_no_token` | 401 | ✅ Pass |
| 5 | `test_403_hr_role` | 403 | ✅ Pass |

---

### `GET /buildings/{id}/floors` — 3 tests

#### Success cases (1)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200` — list with floor_id, building_id present | ✅ Pass |

#### Error cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 2 | `test_404_building_not_found` | 404 `BUILDING_NOT_FOUND` | ✅ Pass |
| 3 | `test_401_no_token` | 401 | ✅ Pass |

---

### `POST /buildings/{id}/floors` — 8 tests

#### Success cases (1)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_201` — floor_id, building_id, floor_name in response | ✅ Pass |

#### Error cases (7)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 2 | `test_404_building_not_found` | 404 `BUILDING_NOT_FOUND` | ✅ Pass |
| 3 | `test_400_invalid_altitude` — min > max | 400 `INVALID_ALTITUDE_RANGE` | ✅ Pass |
| 4 | `test_400_equal_altitude` — min == max | 400 `INVALID_ALTITUDE_RANGE` | ✅ Pass |
| 5 | `test_409_floor_number_exists` — duplicate number in building | 409 `FLOOR_NUMBER_EXISTS` | ✅ Pass |
| 6 | `test_422_missing_field` — floor_number omitted | 422 | ✅ Pass |
| 7 | `test_401_no_token` | 401 | ✅ Pass |
| 8 | `test_403_hr_role` — HR cannot create floors (admin only) | 403 | ✅ Pass |

---

### `PUT /floors/{id}` — 6 tests

#### Success cases (1)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200` — floor_id + updated=True | ✅ Pass |

#### Error cases (5)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 2 | `test_404_not_found` | 404 `FLOOR_NOT_FOUND` | ✅ Pass |
| 3 | `test_400_invalid_altitude` — both min/max provided, min > max | 400 `INVALID_ALTITUDE_RANGE` | ✅ Pass |
| 4 | `test_400_merged_altitude_invalid` — only min provided, merged with existing max fails | 400 `INVALID_ALTITUDE_RANGE` | ✅ Pass |
| 5 | `test_401_no_token` | 401 | ✅ Pass |
| 6 | `test_403_hr_role` | 403 | ✅ Pass |

---

### `GET /geofences` — 4 tests

#### Success cases (2)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200` — geofence_id, geofence_rule_id, name, is_active present | ✅ Pass |
| 2 | `test_returns_empty_list` — empty array when no geofences | ✅ Pass |

#### Error cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 3 | `test_401_no_token` | 401 | ✅ Pass |
| 4 | `test_403_employee_role` | 403 | ✅ Pass |

---

### `POST /geofences` — 6 tests

#### Success cases (1)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_201` — geofence_id == geofence_rule_id, is_active=True | ✅ Pass |

#### Error cases (5)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 2 | `test_404_floor_not_found` | 404 `FLOOR_NOT_FOUND` | ✅ Pass |
| 3 | `test_400_invalid_altitude` — altitude_min > altitude_max | 400 `INVALID_ALTITUDE_RANGE` | ✅ Pass |
| 4 | `test_409_overlap` — same-center geofence triggers Haversine overlap | 409 `GEOFENCE_OVERLAP` | ✅ Pass |
| 5 | `test_422_missing_field` — floor_id omitted | 422 | ✅ Pass |
| 6 | `test_401_no_token` | 401 | ✅ Pass |

---

### `PUT /geofences/{id}` — 5 tests

#### Success cases (1)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200` — updated=True, excludes self from overlap check | ✅ Pass |

#### Error cases (4)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 2 | `test_404_not_found` | 404 `GEOFENCE_NOT_FOUND` | ✅ Pass |
| 3 | `test_409_overlap` — another geofence at same center triggers overlap | 409 `GEOFENCE_OVERLAP` | ✅ Pass |
| 4 | `test_401_no_token` | 401 | ✅ Pass |
| 5 | `test_403_employee_role` | 403 | ✅ Pass |

---

### `DELETE /geofences/{id}` — 5 tests

#### Success cases (1)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200` — geofence_id present, is_active=False | ✅ Pass |

#### Error cases (4)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 2 | `test_404_not_found` | 404 `GEOFENCE_NOT_FOUND` | ✅ Pass |
| 3 | `test_409_already_disabled` — is_active=False on fixture | 409 `ALREADY_DISABLED` | ✅ Pass |
| 4 | `test_401_no_token` | 401 | ✅ Pass |
| 5 | `test_403_employee_role` | 403 | ✅ Pass |

---

## Security Behaviours Verified

| Behaviour | Verified By |
|-----------|-------------|
| Only admin can create/update buildings and floors | `test_403_hr_role` on POST/PUT buildings, POST floors, PUT floors |
| HR and admin can read buildings, floors, geofences | `as_hr` success tests across all GET endpoints |
| HR and admin can create/update/delete geofences | `as_hr` success tests on POST/PUT/DELETE geofences |
| All protected endpoints reject missing token | `test_401_no_token` present on every endpoint |
| Employees cannot access any geofence management endpoints | `test_403_employee_role` on GET buildings, GET/POST/PUT/DELETE geofences |

---

## Known Limitations Of This Test Run

1. **No real database** — all repository functions are mocked; SQL join correctness not verified.
2. **ArcGIS validation is a stub** — only checks non-empty string; no real ArcGIS REST API call.
3. **Haversine overlap test uses identical centers** — real overlapping-but-not-identical coordinates not tested.
4. **Floor number uniqueness not enforced at DB level** — enforced only in service layer (no `UniqueConstraint` in `Floor` model).
5. **Building name uniqueness not enforced at DB level** — enforced only in service layer.
6. **Non-paginated endpoints** — `GET /buildings` and `GET /geofences` return all results; no pagination limit tested.

---

## How To Run

```bash
uv run pytest tests/geofence/ -v
uv run pytest tests/geofence/ -v --cov=app --cov-report=term-missing
```

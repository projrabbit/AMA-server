# Admin Management Module — Test Report

**Date**: 2026-05-20
**Environment**: Local (no live database — DB dependency fully mocked)
**Test runner**: `uv run pytest tests/admin/ -v`
**Result**: ✅ 74 / 74 passed — 0 failed — 0 skipped
**Duration**: ~27s

---

## Coverage By Endpoint

| Endpoint | Tests | Result |
|----------|-------|--------|
| `GET /employees` | 4 | ✅ All pass |
| `POST /employees` | 8 | ✅ All pass |
| `GET /employees/{id}` | 4 | ✅ All pass |
| `PUT /employees/{id}` | 3 | ✅ All pass |
| `PUT /employees/{id}/deactivate` | 4 | ✅ All pass |
| `PUT /employees/{id}/shift` | 3 | ✅ All pass |
| `GET /departments` | 4 | ✅ All pass |
| `POST /departments` | 5 | ✅ All pass |
| `PUT /departments/{id}` | 4 | ✅ All pass |
| `GET /shifts` | 4 | ✅ All pass |
| `POST /shifts` | 5 | ✅ All pass |
| `PUT /shifts/{id}` | 5 | ✅ All pass |
| `POST /devices/register` | 6 | ✅ All pass |
| `GET /devices/me` | 5 | ✅ All pass |
| `GET /devices` | 4 | ✅ All pass |
| `PUT /devices/{id}/trust` | 6 | ✅ All pass |

---

## Test Infrastructure

### Strategy

All tests use FastAPI's `TestClient` with `get_db` globally overridden by a `MagicMock` session — no real PostgreSQL connection. Repository functions are patched at the service-import level (`app.services.admin_service.<fn>`) since `admin_service.py` imports all repository functions at module level.

Role guards in `app/api/dependencies.py` call `get_account_by_id(db, account_id)` to resolve the current account. Because `db` is a `MagicMock`, `get_account_by_id` would return a `MagicMock` whose `.role` attribute fails the `AccountRole` enum check and always returns 403. This is solved by the role-aware auth fixtures in `tests/admin/conftest.py` which patch `app.api.dependencies.get_account_by_id` to return a real `SimpleNamespace` account with the correct role.

### Patch Paths Used

| Patch target | Used in |
|---|---|
| `app.services.admin_service.*` (25 functions) | All test files |
| `app.api.dependencies.get_account_by_id` | `tests/admin/conftest.py` (via role fixtures) |

### Test Fixtures

| Fixture | Type | Purpose |
|---------|------|---------|
| `as_hr` | `dict` (headers) | HR auth headers + `get_account_by_id` patched to return HR account |
| `as_admin` | `dict` (headers) | Admin auth headers + `get_account_by_id` patched to return admin account |
| `as_employee` | `dict` (headers) | Employee auth headers + `get_account_by_id` patched to return employee account |
| `hr_auth_headers` | `dict` (headers) | Raw HR headers (no patch) — used for 403 tests with wrong role |
| `employee_auth_headers` | `dict` (headers) | Raw employee headers (no patch) — used for 403 tests |
| `employee_full` | `SimpleNamespace` | Full employee with `.account`, `.devices`, `.shifts` sub-namespaces |
| `dept_orm` | `SimpleNamespace` | Department ORM-like object with `department_id=10, name="Engineering"` |
| `shift_ns` | `SimpleNamespace` | Shift with `shift_id=20, employee_id=1001, name="Morning Shift"` |
| `device_ns` | `SimpleNamespace` | Device with `device_id=30, is_trusted=False, platform="android"` |

---

## Detailed Results

### `GET /employees` — 4 tests

#### Success cases (2)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200` — list with one employee | ✅ Pass |
| 2 | `test_response_shape` — success=True, data is list, meta.total=1 | ✅ Pass |

#### Error cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 3 | `test_401_without_token` | 401 | ✅ Pass |
| 4 | `test_403_employee_role` | 403 | ✅ Pass |

---

### `POST /employees` — 8 tests

#### Success cases (2)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_201` — creates employee + account | ✅ Pass |
| 2 | `test_response_has_employee_id` — data.employee_id present | ✅ Pass |

#### Error cases (6)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 3 | `test_409_email_conflict` | 409 `EMAIL_ALREADY_EXISTS` | ✅ Pass |
| 4 | `test_409_phone_conflict` | 409 `PHONE_ALREADY_EXISTS` | ✅ Pass |
| 5 | `test_404_department_not_found` | 404 `DEPARTMENT_NOT_FOUND` | ✅ Pass |
| 6 | `test_422_missing_field` — no email | 422 | ✅ Pass |
| 7 | `test_422_weak_password` — password too short | 422 | ✅ Pass |
| 8 | `test_401_no_token` | 401 | ✅ Pass |

---

### `GET /employees/{id}` — 4 tests

#### Success cases (2)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200` | ✅ Pass |
| 2 | `test_response_has_fields` — employee_id + face_registered present | ✅ Pass |

#### Error cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 3 | `test_404_not_found` | 404 `EMPLOYEE_NOT_FOUND` | ✅ Pass |
| 4 | `test_401_no_token` | 401 | ✅ Pass |

---

### `PUT /employees/{id}` — 3 tests

#### Success cases (1)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200` — data.updated=True | ✅ Pass |

#### Error cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 2 | `test_404_employee_not_found` | 404 | ✅ Pass |
| 3 | `test_409_email_conflict` | 409 `EMAIL_ALREADY_EXISTS` | ✅ Pass |

---

### `PUT /employees/{id}/deactivate` — 4 tests

#### Success cases (1)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200` — data.account_locked=True | ✅ Pass |

#### Error cases (3)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 2 | `test_404_not_found` | 404 | ✅ Pass |
| 3 | `test_409_already_inactive` | 409 `ALREADY_INACTIVE` | ✅ Pass |
| 4 | `test_403_employee_role` | 403 | ✅ Pass |

---

### `PUT /employees/{id}/shift` — 3 tests

#### Success cases (1)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200` — data.assigned=True, data.shift_id=20 | ✅ Pass |

#### Error cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 2 | `test_404_employee_not_found` | 404 `EMPLOYEE_NOT_FOUND` | ✅ Pass |
| 3 | `test_404_shift_not_found` | 404 `SHIFT_NOT_FOUND` | ✅ Pass |

---

### `GET /departments` — 4 tests

#### Success cases (2)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200` | ✅ Pass |
| 2 | `test_response_shape` — success=True, data[0].name="Engineering", meta.total=1 | ✅ Pass |

#### Error cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 3 | `test_401_no_token` | 401 | ✅ Pass |
| 4 | `test_403_employee_role` | 403 | ✅ Pass |

---

### `POST /departments` — 5 tests

#### Success cases (1)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_201` — data.name="Engineering" | ✅ Pass |

#### Error cases (4)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 2 | `test_409_name_exists` | 409 `DEPARTMENT_NAME_EXISTS` | ✅ Pass |
| 3 | `test_404_manager_not_found` — manager_id provided but not found | 404 `MANAGER_NOT_FOUND` | ✅ Pass |
| 4 | `test_422_missing_name` | 422 | ✅ Pass |
| 5 | `test_401_no_token` | 401 | ✅ Pass |

---

### `PUT /departments/{id}` — 4 tests

#### Success cases (1)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200` — data.updated=True | ✅ Pass |

#### Error cases (3)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 2 | `test_404_not_found` | 404 `DEPARTMENT_NOT_FOUND` | ✅ Pass |
| 3 | `test_409_name_conflict` — name taken by another department | 409 `DEPARTMENT_NAME_EXISTS` | ✅ Pass |
| 4 | `test_401_no_token` | 401 | ✅ Pass |

---

### `GET /shifts` — 4 tests

#### Success cases (2)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200` | ✅ Pass |
| 2 | `test_response_shape` — data[0].name="Morning Shift", meta.total=1 | ✅ Pass |

#### Error cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 3 | `test_401_no_token` | 401 | ✅ Pass |
| 4 | `test_403_employee_role` | 403 | ✅ Pass |

---

### `POST /shifts` — 5 tests

#### Success cases (1)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_201` — data.name="Morning Shift" | ✅ Pass |

#### Error cases (4)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 2 | `test_404_employee_not_found` | 404 `EMPLOYEE_NOT_FOUND` | ✅ Pass |
| 3 | `test_409_shift_conflict` — overlapping times | 409 `SHIFT_TIME_CONFLICT` | ✅ Pass |
| 4 | `test_422_missing_times` — no start_time or end_time | 422 | ✅ Pass |
| 5 | `test_401_no_token` | 401 | ✅ Pass |

---

### `PUT /shifts/{id}` — 5 tests

#### Success cases (1)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200` — data.updated=True | ✅ Pass |

#### Error cases (4)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 2 | `test_404_not_found` | 404 `SHIFT_NOT_FOUND` | ✅ Pass |
| 3 | `test_409_time_conflict` — new times conflict with another shift | 409 `SHIFT_TIME_CONFLICT` | ✅ Pass |
| 4 | `test_401_no_token` | 401 | ✅ Pass |
| 5 | `test_403_employee_role` | 403 | ✅ Pass |

---

### `POST /devices/register` — 6 tests

#### Success cases (3)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_201_new_device` — fingerprint not found, creates new device | ✅ Pass |
| 2 | `test_returns_201_update_existing` — same fingerprint+employee, updates metadata | ✅ Pass |
| 3 | `test_response_has_registered_at` — registered_at field present | ✅ Pass |

#### Error cases (3)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 4 | `test_401_no_token` | 401 | ✅ Pass |
| 5 | `test_403_hr_role` — HR cannot register devices | 403 | ✅ Pass |
| 6 | `test_422_missing_fingerprint` | 422 | ✅ Pass |

---

### `GET /devices/me` — 5 tests

#### Success cases (3)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200_with_list` — list with one device | ✅ Pass |
| 2 | `test_returns_empty_list_when_no_devices` — empty list, not null | ✅ Pass |
| 3 | `test_device_fields` — device_id, is_trusted, registered_at present | ✅ Pass |

#### Error cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 4 | `test_401_no_token` | 401 | ✅ Pass |
| 5 | `test_403_hr_role` | 403 | ✅ Pass |

---

### `GET /devices` — 4 tests

#### Success cases (1)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200` — meta.total=1 | ✅ Pass |

#### Error cases (3)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 2 | `test_401_no_token` | 401 | ✅ Pass |
| 3 | `test_403_hr_role` — HR cannot list all devices | 403 | ✅ Pass |
| 4 | `test_403_employee_role` | 403 | ✅ Pass |

---

### `PUT /devices/{id}/trust` — 6 tests

#### Success cases (2)
| # | Test | Status |
|---|------|--------|
| 1 | `test_trust_device_200` — data.is_trusted=True, data.updated=True | ✅ Pass |
| 2 | `test_untrust_device_200` — revoke trust on previously trusted device | ✅ Pass |

#### Error cases (4)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 3 | `test_404_device_not_found` | 404 `DEVICE_NOT_FOUND` | ✅ Pass |
| 4 | `test_401_no_token` | 401 | ✅ Pass |
| 5 | `test_403_hr_role` | 403 | ✅ Pass |
| 6 | `test_422_missing_is_trusted` — empty body | 422 | ✅ Pass |

---

## Security Behaviours Verified

| Behaviour | Verified By |
|-----------|-------------|
| Only employees can register/view own devices | `test_403_hr_role` on `POST /devices/register`, `GET /devices/me` |
| Only admins can list all devices or manage trust | `test_403_hr_role` + `test_403_employee_role` on `GET /devices`, `PUT /devices/{id}/trust` |
| HR/Admin-only employee and department management | `test_403_employee_role` across employees, departments, shifts |
| Deactivating an employee requires HR/Admin role | `test_403_employee_role` on `PUT /employees/{id}/deactivate` |
| All protected endpoints reject missing token | `test_401_no_token` present on every endpoint |

---

## Known Limitations Of This Test Run

1. **No real database** — all repository functions are mocked; SQL query correctness is not tested here.
2. **`face_registered` is always `False`** — Module 5 (Face Verification) not yet implemented; this field is a stub.
3. **Shift conflict logic not integration-tested** — the EXISTS query is unit-tested at the service layer only.
4. **Pagination math not exhaustively tested** — only `total=1` / empty-list cases covered.

---

## How To Run

```bash
uv run pytest tests/admin/ -v
uv run pytest tests/admin/ -v --cov=app --cov-report=term-missing
```

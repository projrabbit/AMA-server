# API Implementation Checklist

Tracks implementation status of every endpoint defined in `FULL_API_DOCS.md`.

**Legend**
- ✅ Completed — endpoint is wired, service logic and repository written
- 🚧 In Progress — partially implemented
- ⬜ Not Started

**Progress**: 31 / 47 endpoints complete

---

## Module 1: Authentication

| Status | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| ✅ | `POST` | `/auth/login` | Issues access + refresh JWT, writes audit log |
| ✅ | `POST` | `/auth/refresh` | Validates refresh token, issues new access token |
| ✅ | `GET` | `/auth/me` | Returns account + employee from token |
| ✅ | `POST` | `/auth/logout` | Blacklists both JTIs, writes audit log |
| ✅ | `PUT` | `/auth/change-password` | Verifies current password, hashes new, writes audit log |

**Files written**
- `app/core/security.py` — tokens, password hashing, in-memory JTI blacklist
- `app/schemas/common.py` — `SuccessResponse[T]`, `ErrorResponse`
- `app/schemas/auth.py` — all request/response models
- `app/repositories/auth_repository.py` — DB queries
- `app/services/auth_service.py` — business logic
- `app/api/dependencies.py` — `CurrentAccount`, role guards
- `app/api/v1/endpoints/auth.py` — 5 route handlers

---

## Module 2: Attendance

| Status | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| ⬜ | `POST` | `/attendance/check-in` | multipart/form-data; GPS + face + liveness + fraud pipeline |
| ⬜ | `POST` | `/attendance/check-out` | Same pipeline; pairs with check-in record |
| ⬜ | `GET` | `/attendance/today-status` | Mobile home screen state |
| ⬜ | `GET` | `/attendance/history` | Date-range, paginated, role-scoped |
| ⬜ | `GET` | `/attendance/exceptions` | Rejected / late / early-leave list |
| ⬜ | `GET` | `/attendance/{record_id}` | Full detail including fraud result |
| ⬜ | `PUT` | `/attendance/{record_id}/approve` | Manual HR override |

**Dependencies before starting**
- Module 3 (Geofence) — geofence lookup needed for check-in validation
- Module 4 (Fraud Detection) — evaluate fraud before writing record
- Module 5 (Face Verification) — face match called during check-in

---

## Module 3: Geofence

| Status | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| ✅ | `GET` | `/buildings` | `include_floors` populates nested floors list; q searches name+address; non-paginated |
| ✅ | `POST` | `/buildings` | ArcGIS validation is a stub (non-empty string passes); 400 `INVALID_ARCGIS_LAYER` on empty |
| ✅ | `PUT` | `/buildings/{building_id}` | Re-runs ArcGIS stub only when `arcgis_layer_id` field is provided in body |
| ✅ | `GET` | `/buildings/{building_id}/floors` | 404 `BUILDING_NOT_FOUND` if building missing |
| ✅ | `POST` | `/buildings/{building_id}/floors` | 400 `INVALID_ALTITUDE_RANGE` if min >= max; 409 `FLOOR_NUMBER_EXISTS` for duplicate number per building |
| ✅ | `PUT` | `/floors/{floor_id}` | Merges existing altitude values with request before validating; 400 if merged result invalid |
| ✅ | `GET` | `/geofences` | Non-paginated; joins GeofenceRule→CellSpace→Floor→Building; filter by building_id/floor_id/is_active |
| ✅ | `POST` | `/geofences` | Creates CellSpace + GeofenceRule atomically (flush+commit); Python Haversine overlap check |
| ✅ | `PUT` | `/geofences/{geofence_id}` | Overlap check excludes self; updates CellSpace (name/lat/lng) and GeofenceRule (radius/altitude/flags) |
| ✅ | `DELETE` | `/geofences/{geofence_id}` | Soft delete — sets `is_active=False`; 409 `ALREADY_DISABLED` if already inactive |

**Files written**
- `app/schemas/geofence.py` — all request/response models
- `app/repositories/geofence_repository.py` — all DB queries
- `app/services/geofence_service.py` — business logic, Haversine helpers, ArcGIS stub
- `app/api/v1/endpoints/buildings.py` — 5 route handlers (GET/POST buildings, PUT building, GET/POST floors)
- `app/api/v1/endpoints/floors.py` — 1 route handler (PUT floor)
- `app/api/v1/endpoints/geofences.py` — 4 route handlers (GET/POST/PUT/DELETE geofences)
- `app/api/v1/router.py` — registered 3 new routers (buildings, floors, geofences)
- `tests/geofence/__init__.py`
- `tests/geofence/conftest.py` — make_building, make_floor, make_geofence, as_hr, as_admin
- `tests/geofence/test_buildings.py` — 27 tests
- `tests/geofence/test_floors.py` — 6 tests
- `tests/geofence/test_geofences.py` — 20 tests

---

## Module 4: Fraud Detection

| Status | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| ⬜ | `POST` | `/internal/fraud/evaluate` | Internal only; not exposed publicly |
| ⬜ | `GET` | `/fraud/records` | Filter by flags, date range, confidence score |
| ⬜ | `GET` | `/fraud/records/{fraud_id}` | Full detail with linked attendance record |

**Notes**
- `FraudDetection` model is in `app/models/business.py`
- Fraud evaluation is called inline during attendance check-in/out
- `buddy_punch` detection requires querying recent records for the same device used by different employees

---

## Module 5: Face Verification

| Status | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| ⬜ | `POST` | `/employees/{employee_id}/face` | Upload reference face; stored in MinIO/S3 |
| ⬜ | `GET` | `/employees/{employee_id}/face` | Returns metadata only, not the image |
| ⬜ | `DELETE` | `/employees/{employee_id}/face` | Removes stored reference |
| ⬜ | `POST` | `/internal/face/verify` | Internal; returns match + liveness scores |

**Notes**
- Face images stored in object storage (MinIO or S3); DB stores the object key only
- Requires `face_recognition` / `opencv` / `mediapipe` libraries (not yet in `pyproject.toml`)
- Object storage client not yet configured

---

## Module 6: Notification

| Status | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| ⬜ | `GET` | `/notifications` | Paginated; filter by `is_read`, `type` |
| ⬜ | `PUT` | `/notifications/{notification_id}/read` | Owner-only |
| ⬜ | `PUT` | `/notifications/read-all` | Bulk mark read |
| ⬜ | `GET` | `/notifications/preferences` | Per-user push/in-app settings |
| ⬜ | `PUT` | `/notifications/preferences` | Update preferences |
| ⬜ | `POST` | `/internal/notifications/send` | Internal dispatch called after attendance record creation |

**Notes**
- No `Notification` or `NotificationPreference` table exists in current models — must be added to `app/models/business.py` and a new migration created
- Push delivery integration (FCM / APNs) is out of scope for MVP backend; `send` endpoint creates in-app records only

---

## Module 7: Report

| Status | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| ⬜ | `GET` | `/dashboard/summary` | KPIs for today; designed for 60s polling |
| ⬜ | `GET` | `/realtime/employees-location` | Active check-ins without checkout; 30s polling |
| ⬜ | `GET` | `/reports/attendance` | Date-range report with per-employee summary |
| ⬜ | `GET` | `/reports/attendance/export` | Binary Excel/PDF response |

**Notes**
- Export requires `openpyxl` (Excel) and `reportlab` or `weasyprint` (PDF) — not yet in `pyproject.toml`
- Dashboard and realtime queries should be optimised with DB indexes already defined on `attendance_record.timestamp` and `attendance_record.status`

---

## Module 8: Audit Log

| Status | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| ⬜ | `GET` | `/audit-logs` | Filter by actor, action, entity, date range; max 100/page |
| ⬜ | `GET` | `/audit-logs/{log_id}` | Full detail with before/after payload |

**Notes**
- `AuditLog` model in `app/models/business.py` — immutable, no write APIs via HTTP
- `ip_address` column added in the auth implementation pass

---

## Module 9: Admin Management

### Employees

| Status | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| ✅ | `GET` | `/employees` | ilike search on name/email/phone; paginated; joinloads Account + Department |
| ✅ | `POST` | `/employees` | `db.flush()` to get employee_id before Account insert; single commit |
| ✅ | `GET` | `/employees/{employee_id}` | `face_registered=False` stub until Module 5; latest device/shift from list tail |
| ✅ | `PUT` | `/employees/{employee_id}` | Email/phone uniqueness excludes self; `employee_status` param avoids shadowing `fastapi.status` |
| ✅ | `PUT` | `/employees/{employee_id}/deactivate` | 409 `ALREADY_INACTIVE` if already inactive; writes 2 audit logs (EMPLOYEE + ACCOUNT) |
| ✅ | `PUT` | `/employees/{employee_id}/shift` | Sets `shift.employee_id` to point to the employee; 404 if either not found |

### Departments

| Status | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| ✅ | `GET` | `/departments` | Scalar query with correlated COUNT subquery + LEFT JOIN for manager name |
| ✅ | `POST` | `/departments` | 404 `MANAGER_NOT_FOUND` if `manager_id` provided but employee missing |
| ✅ | `PUT` | `/departments/{department_id}` | Name conflict check excludes self by `department_id` |

### Shifts

| Status | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| ✅ | `GET` | `/shifts` | Filter by `employee_id`; joinloads Employee |
| ✅ | `POST` | `/shifts` | EXISTS conflict query: `start < req_end AND end > req_start` |
| ✅ | `PUT` | `/shifts/{shift_id}` | Merges existing times with request before conflict check; excludes self via `exclude_shift_id` |

### Devices

| Status | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| ✅ | `POST` | `/devices/register` | Upsert on `(employee_id, device_fingerprint)`; new fingerprint → insert, same → update metadata |
| ✅ | `GET` | `/devices/me` | Returns `list[DeviceDetail]` (not single object); ordered by `registered_at DESC` |
| ✅ | `GET` | `/devices` | Admin-only; filter by `employee_id`, `is_trusted`, `platform`; joinloads Employee → Department |
| ✅ | `PUT` | `/devices/{device_id}/trust` | Writes audit log (update, DEVICE); 404 `DEVICE_NOT_FOUND` |

**Files written**
- `app/models/business.py` — `Device`: added `os_version`, `app_version`, renamed `register_at` → `registered_at`, composite unique `(employee_id, device_fingerprint)`, non-unique individual indexes; `Employee.devices` list relationship
- `alembic/versions/495dabd80749_update_device_model_for_multi_device_.py` — migration applied
- `app/schemas/admin.py` — all request/response models for Employees, Departments, Shifts, Devices
- `app/repositories/admin_repository.py` — all DB queries
- `app/services/admin_service.py` — business logic with HTTPException error codes
- `app/api/v1/endpoints/employees.py` — 6 route handlers
- `app/api/v1/endpoints/departments.py` — 3 route handlers
- `app/api/v1/endpoints/shifts.py` — 3 route handlers
- `app/api/v1/endpoints/devices.py` — 4 route handlers
- `app/api/v1/router.py` — registered 4 new routers
- `tests/admin/__init__.py`
- `tests/admin/conftest.py` — fixtures + role-aware auth patches
- `tests/admin/test_employees.py` — 20 tests
- `tests/admin/test_departments.py` — 13 tests
- `tests/admin/test_shifts.py` — 13 tests
- `tests/admin/test_devices.py` — 16 tests

---

## Implementation Order (Recommended)

The modules have dependencies. This order minimises blocked work:

```
1. Module 9 — Admin Management        (no upstream deps; unblocks everything)
2. Module 3 — Geofence               (needs buildings/floors from Module 9)
3. Module 8 — Audit Log              (read-only; can be done anytime)
4. Module 5 — Face Verification      (needs employee from Module 9)
5. Module 4 — Fraud Detection        (needs device from Module 9)
6. Module 6 — Notification           (needs new DB models; self-contained)
7. Module 2 — Attendance             (needs Modules 3, 4, 5 complete)
8. Module 7 — Report                 (needs Modules 2 and 9 complete)
```

---

## Missing DB Models (Must Add Before Implementation)

| Model | Needed For | Status |
|-------|-----------|--------|
| `Notification` | Module 6 | ⬜ Not in `business.py` |
| `NotificationPreference` | Module 6 | ⬜ Not in `business.py` |

## Missing Python Dependencies (Must Add to `pyproject.toml`)

| Package | Needed For |
|---------|-----------|
| `python-multipart` | File uploads (check-in face image) |
| `openpyxl` | Excel report export |
| `reportlab` or `weasyprint` | PDF report export |
| `boto3` or `minio` | Object storage for face images and exports |
| `face_recognition` / `opencv-python` / `mediapipe` | Face verification service |

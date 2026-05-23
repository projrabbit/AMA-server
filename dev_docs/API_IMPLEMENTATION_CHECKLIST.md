# API Implementation Checklist

Tracks implementation status of every endpoint defined in `FULL_API_DOCS.md`.

**Legend**
- ✅ Completed — endpoint is wired, service logic and repository written
- 🚧 In Progress — partially implemented
- ⬜ Not Started

**Progress**: 57 / 57 endpoints complete 🎉

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
| ✅ | `POST` | `/attendance/check-in` | multipart/form-data; GPS threshold 20 m; MinIO selfie upload before fraud eval; always writes record; status=rejected if outside geofence or face/liveness fail; status=flagged if other fraud flags; `_run_checkin_pipeline` shared with check-out |
| ✅ | `POST` | `/attendance/check-out` | Same pipeline as check-in; sets `matched_checkin_record_id` + `worked_minutes`; 409 `FAILED_NO_CHECKIN` if no approved/flagged check-in today |
| ✅ | `GET` | `/attendance/today-status` | `can_check_in/can_check_out` derived from today's active checkin/checkout presence; employee-only |
| ✅ | `GET` | `/attendance/history` | Required `from`/`to` params (`alias="from"` for reserved word); employee locked to self; service groups records by date; returns 5-tuple; all times in +07:00 |
| ✅ | `GET` | `/attendance/exceptions` | Default filter shows rejected/flagged/late/early-leave; `status` param narrows; OR filter built in repository |
| ✅ | `GET` | `/attendance/{record_id}` | hr/admin only; joinloads employee+dept, device, shift, fraud_detection; 404 `RECORD_NOT_FOUND` |
| ✅ | `PUT` | `/attendance/{record_id}/approve` | 404 `RECORD_NOT_FOUND`; 409 `ALREADY_APPROVED`; sets approved_by_account_id + approved_at; writes audit log |

**Files written**
- `app/models/business.py` — MODIFIED `AttendanceRecord`: `geofence_rule_id` now nullable; added `face_image_object_key`, `matched_checkin_record_id` (self-ref FK, `use_alter=True`), `worked_minutes`, `approved_by_account_id`, `approved_at`; 2 new indexes
- `alembic/versions/e8509aa02ee1_extend_attendance_record_add_new_columns.py` — migration applied
- `app/repositories/geofence_repository.py` — MODIFIED: added `find_geofence_for_location` (Haversine, altitude range check)
- `app/schemas/attendance.py` — all request/response models
- `app/repositories/attendance_repository.py` — all DB queries
- `app/services/attendance_service.py` — full check-in/check-out pipeline + 5 other service functions
- `app/api/v1/endpoints/attendance.py` — 7 route handlers
- `app/api/v1/router.py` — registered attendance router under `/attendance`
- `tests/attendance/__init__.py`
- `tests/attendance/conftest.py` — `make_shift`, `make_device`, `make_fraud_detection`, `make_attendance_record`, `as_employee`, `as_hr`, `as_admin`
- `tests/attendance/test_checkin.py` — 10 tests
- `tests/attendance/test_checkout.py` — 5 tests
- `tests/attendance/test_today_status.py` — 5 tests
- `tests/attendance/test_history.py` — 9 tests
- `tests/attendance/test_exceptions.py` — 6 tests
- `tests/attendance/test_record_detail.py` — 5 tests
- `tests/attendance/test_approve.py` — 7 tests

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
| ✅ | `POST` | `/internal/fraud/evaluate` | No JWT guard; pure evaluation — no DB write; detects 6 fraud flags; confidence score via deduction formula (mock_location −40, gps_spoofing −35, face_mismatch −30, liveness_failed −25, buddy_punch −25, unknown_device −20) |
| ✅ | `GET` | `/fraud/records` | 11 optional filters; `contains_eager` join through `attendance_record → employee → department`; ordered by `checked_at DESC` |
| ✅ | `GET` | `/fraud/records/{fraud_id}` | `joinedload` for employee, department, and device chains; 404 `FRAUD_NOT_FOUND` if missing |

**Notes**
- `FraudDetection` model was extended with 4 missing columns (`unknown_device`, `face_mismatch_detected`, `liveness_failed`, `confidence_score`) via migration `1430b8e61515`
- Face comparison in `evaluate` reuses `_extract_landmarks`, `_cosine_similarity`, `_liveness_score` helpers imported from `face_service`; selfie downloaded from MinIO via `face_image_object_key`
- `buddy_punch` detection queries `attendance_record JOIN device` for same `device_fingerprint` used by a different `employee_id` in last 24 h
- `unknown_device` = device not found for that employee OR `is_trusted = False`

**Files written**
- `app/models/business.py` — MODIFIED `FraudDetection`: added `unknown_device`, `face_mismatch_detected`, `liveness_failed`, `confidence_score` columns
- `alembic/versions/1430b8e61515_add_missing_columns_to_fraud_detection.py` — migration applied
- `app/schemas/fraud.py` — `LivenessSignals`, `RawSignals`, `EvaluateFraudRequest`, `EvaluateFraudResult`, `FraudEmployeeInfo`, `FraudRecordItem`, `FraudAttendanceInfo`, `FraudDeviceInfo`, `FraudRecordDetailData`
- `app/repositories/fraud_repository.py` — `get_fraud_records`, `get_fraud_record_by_id`, `get_recent_device_records`, `get_device_by_fingerprint_and_employee`
- `app/services/fraud_service.py` — `evaluate_fraud`, `list_fraud_records`, `get_fraud_record_detail`
- `app/api/v1/endpoints/fraud.py` — `internal_fraud_router` (POST /evaluate) + `fraud_router` (GET /records, GET /records/{fraud_id})
- `app/api/v1/router.py` — registered `fraud_router` under `/fraud` and `internal_fraud_router` under `/internal`
- `tests/fraud/__init__.py`
- `tests/fraud/conftest.py` — `make_department`, `make_device`, `make_attendance_record`, `make_employee_with_dept`, `make_fraud_record`, `as_hr`, `as_admin`, `as_employee`
- `tests/fraud/test_evaluate.py` — 14 tests
- `tests/fraud/test_fraud_records.py` — 8 tests
- `tests/fraud/test_fraud_detail.py` — 6 tests

---

## Module 5: Face Verification

| Status | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| ✅ | `POST` | `/employees/{employee_id}/face` | Upload reference face; mediapipe face detection; stored in MinIO |
| ✅ | `GET` | `/employees/{employee_id}/face` | Returns metadata only; 404 if employee not found |
| ✅ | `DELETE` | `/employees/{employee_id}/face` | Deletes MinIO object + DB row; 404 FACE_NOT_REGISTERED if none |
| ✅ | `POST` | `/internal/face/verify` | No auth guard; FaceMesh cosine similarity + liveness signal scoring |

**Files written**
- `app/models/business.py` — ADD `FaceReference`: face_id, employee_id (unique FK), face_object_key, registered_at; ADD face_reference relationship to Employee
- `alembic/versions/1cb0ebeb16f1_add_face_reference_table.py` — migration applied
- `app/core/storage.py` — MinIO singleton, upload/download/delete helpers, bucket auto-create
- `app/schemas/face.py` — FaceStatusData, RegisterFaceData, DeleteFaceData, VerifyFaceData
- `app/repositories/face_repository.py` — get_face_reference, upsert_face_reference, delete_face_reference
- `app/services/face_service.py` — register_employee_face, get_face_status, remove_employee_face, verify_face_internal; mediapipe FaceDetection + FaceMesh helpers
- `app/api/v1/endpoints/face.py` — employee_face_router (3 routes) + internal_face_router (1 route)
- `app/api/v1/router.py` — registered both routers under /employees and /internal prefixes
- `app/repositories/admin_repository.py` — joinedload(Employee.face_reference) added to get_employee_by_id
- `app/services/admin_service.py` — replaced face_registered=False stub with employee.face_reference is not None
- `pyproject.toml` — added: python-multipart, minio, mediapipe, Pillow
- `tests/face/__init__.py`
- `tests/face/conftest.py` — make_face_reference, as_hr, as_admin, as_employee
- `tests/face/test_face_register.py` — 10 tests
- `tests/face/test_face_status.py` — 4 tests
- `tests/face/test_face_delete.py` — 4 tests
- `tests/face/test_face_verify.py` — 4 tests

---

## Module 6: Notification

| Status | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| ✅ | `GET` | `/notifications` | Paginated; filter by `is_read`, `type`; returns `(items, total, unread_count)` tuple; `meta` includes `total_pages` and `unread_count` |
| ✅ | `PUT` | `/notifications/{notification_id}/read` | Owner-only; 403 `FORBIDDEN` if `notif.account_id != account_id`; 404 `NOTIFICATION_NOT_FOUND` if missing |
| ✅ | `PUT` | `/notifications/read-all` | Bulk SQLAlchemy `update()` returning `rowcount`; static path registered before `/{notification_id}/read` to avoid route conflict |
| ✅ | `GET` | `/notifications/preferences` | Get-or-create (upsert) pattern — first access inserts all-true defaults; no 404 ever |
| ✅ | `PUT` | `/notifications/preferences` | All 8 boolean fields required; validation raises 422 on missing field |
| ✅ | `POST` | `/internal/notifications/send` | No JWT guard; unknown `account_ids` silently skipped and counted in `failed_count`; valid accounts counted in `sent_count`; single commit after all inserts |

**Notes**
- `Notification` and `NotificationPreference` tables added to `app/models/business.py`; migration `6b9d84669f48` applied
- Push delivery integration (FCM / APNs) out of scope for MVP; `send` endpoint creates in-app `Notification` rows only
- Route registration order in `notifications.py` is critical: `/read-all`, `/preferences` (static) must be registered before `/{notification_id}/read` (parametric)

**Files written**
- `app/models/business.py` — MODIFIED: added `NotificationType` enum, `notification_type_enum` SQLEnum; added `Notification`, `NotificationPreference` model classes; added `notifications` + `notification_preference` relationships on `Account`
- `alembic/versions/6b9d84669f48_add_notification_and_notification_.py` — migration applied
- `app/schemas/notification.py` — `NotificationItem`, `MarkReadData`, `MarkAllReadData`, `NotificationPreferenceData`, `UpdatePreferencesRequest`, `UpdatePreferencesData`, `SendNotificationRequest`, `SendNotificationData`
- `app/repositories/notification_repository.py` — `get_notifications`, `count_notifications`, `count_unread`, `get_notification_by_id`, `mark_notification_read`, `mark_all_read`, `get_or_create_preferences`, `update_preferences`, `get_account_by_id_simple`, `create_notification`
- `app/services/notification_service.py` — `list_notifications`, `mark_read`, `mark_all_notifications_read`, `get_preferences`, `update_notification_preferences`, `send_notifications`
- `app/api/v1/endpoints/notifications.py` — `notification_router` (5 routes) + `internal_notification_router` (1 route)
- `app/api/v1/router.py` — registered `notification_router` under `/notifications` and `internal_notification_router` under `/internal`
- `tests/notification/__init__.py`
- `tests/notification/conftest.py` — `make_notification`, `make_preference`, `as_employee`, `as_hr`, `as_admin`, `employee_account`, `hr_account`
- `tests/notification/test_list_notifications.py` — 8 tests
- `tests/notification/test_mark_read.py` — 6 tests
- `tests/notification/test_mark_all_read.py` — 4 tests
- `tests/notification/test_preferences.py` — 8 tests
- `tests/notification/test_send_notification.py` — 5 tests

---

## Module 7: Report

| Status | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| ✅ | `GET` | `/dashboard/summary` | `date` defaults to today (+07:00); `absent_count` = shift-holders minus checked-in shift-holders; `on_time_rate` = on_time / total_employees × 100 rounded 2dp; `meta.refresh_interval_seconds=60` |
| ✅ | `GET` | `/realtime/employees-location` | Approved/flagged checkin today with no checkout; optional `building_id`/`floor_id`/`department_id` filters via subqueries; `arcgis_layer_id` from CellSpace; `meta.refresh_interval_seconds=30`; hr/admin only |
| ✅ | `GET` | `/reports/attendance` | Required `from`/`to` (`alias="from"` workaround); records grouped in-memory by employee; `absent_count` per employee = range_days − work_days; no pagination; manager/hr/admin |
| ✅ | `GET` | `/reports/attendance/export` | Returns `Response` (not `SuccessResponse[T]`); 400 `INVALID_EXPORT_FORMAT`; 404 `NO_REPORT_DATA` when no records; 3 sheets Excel (Summary, By Employee, Details); single-page PDF via reportlab; hr/admin only |

**Files written**
- `pyproject.toml` — ADDED: `openpyxl>=3.1.0`, `reportlab>=4.0.0`
- `app/schemas/report.py` — `ActiveLocationItem`, `DashboardSummaryData`, `RealtimeLocationItem`, `ReportSummary`, `ReportEmployeeSummary`, `ReportDayDetail`, `AttendanceReportData`
- `app/repositories/report_repository.py` — `get_active_employee_count`, `get_shift_holder_count`, `get_dashboard_checkin_stats`, `get_fraud_alert_count`, `get_checked_in_shift_holders_count`, `get_active_locations`, `get_realtime_locations`, `get_report_records`
- `app/services/report_service.py` — `get_dashboard_summary`, `get_realtime_locations`, `get_attendance_report`, `export_attendance_report`, `_generate_excel`, `_generate_pdf`
- `app/api/v1/endpoints/report.py` — `dashboard_router` (1 route), `realtime_router` (1 route), `reports_router` (2 routes: export registered before attendance to avoid path conflict)
- `app/api/v1/router.py` — REGISTERED: 3 routers under `/dashboard`, `/realtime`, `/reports`
- `tests/report/__init__.py`
- `tests/report/conftest.py` — `make_active_location`, `make_realtime_location`, `make_report_data`, `as_hr`, `as_admin`, `as_manager`, `as_employee`
- `tests/report/test_dashboard.py` — 10 tests
- `tests/report/test_realtime.py` — 8 tests
- `tests/report/test_attendance_report.py` — 11 tests
- `tests/report/test_export.py` — 11 tests

---

## Module 8: Audit Log

| Status | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| ✅ | `GET` | `/audit-logs` | Filter by `account_id`, `action_type`, `target_entity`, `since`, `until`; default `limit=20`, max 100 |
| ✅ | `GET` | `/audit-logs/{log_id}` | Returns single `AuditLogItem` or 404 `LOG_NOT_FOUND` |

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
| `Notification` | Module 6 | ✅ Added in migration `6b9d84669f48` |
| `NotificationPreference` | Module 6 | ✅ Added in migration `6b9d84669f48` |

## Missing Python Dependencies (Must Add to `pyproject.toml`)

| Package | Needed For |
|---------|-----------|
| `python-multipart` | File uploads (check-in face image) |
| `openpyxl` | Excel report export |
| `reportlab` or `weasyprint` | PDF report export |
| `boto3` or `minio` | Object storage for face images and exports |
| `face_recognition` / `opencv-python` / `mediapipe` | Face verification service |

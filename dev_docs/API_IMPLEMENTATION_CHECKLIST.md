# API Implementation Checklist

Tracks implementation status of every endpoint defined in `FULL_API_DOCS.md`.

**Legend**
- ✅ Completed — endpoint is wired, service logic and repository written
- 🚧 In Progress — partially implemented
- ⬜ Not Started

**Progress**: 5 / 47 endpoints complete

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
| ⬜ | `GET` | `/buildings` | Optional `include_floors`, search by name/address |
| ⬜ | `POST` | `/buildings` | Validates ArcGIS layer ID |
| ⬜ | `PUT` | `/buildings/{building_id}` | Re-validates ArcGIS layer on update |
| ⬜ | `GET` | `/buildings/{building_id}/floors` | List floors with altitude ranges |
| ⬜ | `POST` | `/buildings/{building_id}/floors` | Altitude range required |
| ⬜ | `PUT` | `/floors/{floor_id}` | Update altitude range |
| ⬜ | `GET` | `/geofences` | Filter by building, floor, is_active |
| ⬜ | `POST` | `/geofences` | Overlap check via PostGIS |
| ⬜ | `PUT` | `/geofences/{geofence_id}` | Re-runs overlap check |
| ⬜ | `DELETE` | `/geofences/{geofence_id}` | Soft delete (`is_active = false`) |

**Notes**
- Overlap validation requires PostGIS `ST_DWithin` or `ST_Distance` query
- GIS models live in `app/models/gis.py` — `Building`, `Floor`, `GeofenceRule`, `CellSpace`

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
| ⬜ | `GET` | `/employees` | Search by name/email/phone; paginated |
| ⬜ | `POST` | `/employees` | Creates `Employee` + `Account` atomically |
| ⬜ | `GET` | `/employees/{employee_id}` | Includes account, device, shift |
| ⬜ | `PUT` | `/employees/{employee_id}` | Email/phone uniqueness re-validated |
| ⬜ | `PUT` | `/employees/{employee_id}/deactivate` | Sets `status = inactive` and `is_active = false` |
| ⬜ | `PUT` | `/employees/{employee_id}/shift` | Reassigns existing shift |

### Departments

| Status | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| ⬜ | `GET` | `/departments` | Includes employee count and manager name |
| ⬜ | `POST` | `/departments` | Name uniqueness check |
| ⬜ | `PUT` | `/departments/{department_id}` | Name uniqueness re-checked |

### Shifts

| Status | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| ⬜ | `GET` | `/shifts` | Filter by employee |
| ⬜ | `POST` | `/shifts` | Conflict check against existing shifts for employee |
| ⬜ | `PUT` | `/shifts/{shift_id}` | Re-runs conflict check |

### Devices

| Status | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| ⬜ | `POST` | `/devices/register` | New devices start untrusted |
| ⬜ | `GET` | `/devices/me` | Current employee's registered device |
| ⬜ | `GET` | `/devices` | Admin view; filter by trust status, platform |
| ⬜ | `PUT` | `/devices/{device_id}/trust` | Approve or revoke trust |

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

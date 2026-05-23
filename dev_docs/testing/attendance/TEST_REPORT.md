# Attendance Module — Test Report

**Date**: 2026-05-22
**Environment**: Local (no live database — DB dependency fully mocked)
**Test runner**: `uv run pytest tests/attendance/ -v`
**Result**: ✅ 47 / 47 passed — 0 failed — 0 skipped
**Duration**: ~19.72s

---

## Coverage By Endpoint

| Endpoint | Tests | Result |
|----------|-------|--------|
| `POST /attendance/check-in` | 10 | ✅ All pass |
| `POST /attendance/check-out` | 5 | ✅ All pass |
| `GET /attendance/today-status` | 5 | ✅ All pass |
| `GET /attendance/history` | 9 | ✅ All pass |
| `GET /attendance/exceptions` | 6 | ✅ All pass |
| `GET /attendance/{record_id}` | 5 | ✅ All pass |
| `PUT /attendance/{record_id}/approve` | 7 | ✅ All pass |

---

## Test Infrastructure

### Strategy
All service functions are patched at `app.services.attendance_service.<fn>`. The `get_db` dependency is overridden with a `MagicMock` session in `tests/conftest.py`. Auth fixtures patch `app.api.dependencies.get_account_by_id` to return a `SimpleNamespace` account with the desired role. Check-in and check-out tests send multipart/form-data via `TestClient` with a dummy JPEG bytes body; the entire `attendance_service.check_in` / `check_out` is patched at the service level so no MinIO, fraud, or face calls are made.

### Patch Paths Used

| Patch target | Used in |
|---|---|
| `app.services.attendance_service.check_in` | `test_checkin.py` |
| `app.services.attendance_service.check_out` | `test_checkout.py` |
| `app.services.attendance_service.get_today_status` | `test_today_status.py` |
| `app.services.attendance_service.list_history` | `test_history.py` |
| `app.services.attendance_service.list_exceptions` | `test_exceptions.py` |
| `app.services.attendance_service.get_record_detail` | `test_record_detail.py` |
| `app.services.attendance_service.approve_attendance_record` | `test_approve.py` |
| `app.api.dependencies.get_account_by_id` | `conftest.py` (all tests) |

### Test Fixtures

| Fixture | Role / Purpose | Notable Values |
|---------|---------------|----------------|
| `as_employee` | Employee-role auth headers | `account_id=1002`, `role=employee`, `employee_id=1002` |
| `as_hr` | HR-role auth headers | `account_id=1001`, `role=hr`, `employee_id=None` |
| `as_admin` | Admin-role auth headers | `account_id=1000`, `role=admin`, `employee_id=None` |
| `make_shift` | Returns `ShiftInfo` schema object | `shift_id=10`, Morning/Night variants |
| `make_device` | Returns `RecordDeviceInfo` schema object | `device_id=12`, `platform=android`, `is_trusted=True` |
| `make_fraud_detection` | Returns `RecordFraudDetection` schema object | All flags false, `confidence_score=92.0` |
| `make_attendance_record` | Returns `AttendanceRecordDetailData` schema object | `record_id=1002`, status=rejected |

---

## Detailed Results

### POST /attendance/check-in — 10 tests

#### Success cases (4)
| # | Test | Status |
|---|------|--------|
| 1 | `test_201_approved_status` — GPS inside geofence, all checks pass | ✅ Pass |
| 2 | `test_201_rejected_outside_geofence` — geofence miss → status=rejected | ✅ Pass |
| 3 | `test_201_flagged_status` — fraud flags set → status=flagged | ✅ Pass |
| 4 | `test_response_shape` — verifies all top-level fields present | ✅ Pass |

#### Error cases (4)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 5 | `test_409_already_checked_in` | 409 `ALREADY_CHECKED_IN` | ✅ Pass |
| 6 | `test_422_missing_required_field` | 422 validation error | ✅ Pass |
| 7 | `test_401_no_token` | 401 | ✅ Pass |
| 8 | `test_403_hr_role` | 403 | ✅ Pass |

#### Additional (2)
| # | Test | Status |
|---|------|--------|
| 9 | `test_face_image_optional` — check-in without selfie still works | ✅ Pass |
| 10 | `test_mock_location_flag_forwarded` — `is_mock_location=true` reaches service | ✅ Pass |

---

### POST /attendance/check-out — 5 tests

#### Success cases (2)
| # | Test | Status |
|---|------|--------|
| 1 | `test_201_checkout_success` — `worked_minutes` and `matched_checkin_record_id` in response | ✅ Pass |
| 2 | `test_admin_can_checkout` | ✅ Pass |

#### Error cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 3 | `test_409_no_checkin` | 409 `FAILED_NO_CHECKIN` | ✅ Pass |
| 4 | `test_401_no_token` | 401 | ✅ Pass |

#### Additional (1)
| # | Test | Status |
|---|------|--------|
| 5 | `test_403_hr_role` | ✅ Pass |

---

### GET /attendance/today-status — 5 tests

#### Success cases (3)
| # | Test | Status |
|---|------|--------|
| 1 | `test_200_no_checkin_yet` — `can_check_in=true`, `latest_checkin=null` | ✅ Pass |
| 2 | `test_200_checked_in_awaiting_checkout` — `can_check_out=true`, `latest_checkin` populated | ✅ Pass |
| 3 | `test_200_shift_included` — `current_shift.name` correct | ✅ Pass |

#### Auth cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 4 | `test_401_when_no_token` | 401 | ✅ Pass |
| 5 | `test_403_when_hr_role` | 403 | ✅ Pass |

---

### GET /attendance/history — 9 tests

#### Success cases (5)
| # | Test | Status |
|---|------|--------|
| 1 | `test_200_with_items` — `days` list, `meta.total`, employee info | ✅ Pass |
| 2 | `test_200_empty_range` — `days=[]` | ✅ Pass |
| 3 | `test_hr_can_view_any_employee` — `employee_id` param accepted | ✅ Pass |
| 4 | `test_pagination_params_forwarded` — `page` and `limit` forwarded | ✅ Pass |
| 5 | `test_summary_fields_present` — `work_days`, `late_count`, `rejected_count` | ✅ Pass |

#### Error cases (3)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 6 | `test_403_employee_views_other` | 403 `FORBIDDEN` | ✅ Pass |
| 7 | `test_404_employee_not_found` | 404 `EMPLOYEE_NOT_FOUND` | ✅ Pass |
| 8 | `test_422_missing_from_date` | 422 | ✅ Pass |

#### Auth cases (1)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 9 | `test_401_when_no_token` | 401 | ✅ Pass |

---

### GET /attendance/exceptions — 6 tests

#### Success cases (4)
| # | Test | Status |
|---|------|--------|
| 1 | `test_200_with_items` — `data[0].record_id`, `meta.total` | ✅ Pass |
| 2 | `test_200_empty_list` | ✅ Pass |
| 3 | `test_filters_forwarded` — `status_filter`, `department_id`, `page` forwarded | ✅ Pass |
| 4 | `test_pagination_meta_present` — `total` and `total_pages` in `meta` | ✅ Pass |

#### Auth cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 5 | `test_401_when_no_token` | 401 | ✅ Pass |
| 6 | `test_403_when_employee_role` | 403 | ✅ Pass |

---

### GET /attendance/{record_id} — 5 tests

#### Success cases (2)
| # | Test | Status |
|---|------|--------|
| 1 | `test_200_with_full_data` — employee, device, fraud_detection all present | ✅ Pass |
| 2 | `test_admin_can_access` | ✅ Pass |

#### Error cases (1)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 3 | `test_404_when_not_found` | 404 `RECORD_NOT_FOUND` | ✅ Pass |

#### Auth cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 4 | `test_401_when_no_token` | 401 | ✅ Pass |
| 5 | `test_403_when_employee_role` | 403 | ✅ Pass |

---

### PUT /attendance/{record_id}/approve — 7 tests

#### Success cases (3)
| # | Test | Status |
|---|------|--------|
| 1 | `test_200_with_approve_data` — `record_id`, `status`, `approved_by_account_id` correct | ✅ Pass |
| 2 | `test_admin_can_approve` | ✅ Pass |
| 3 | `test_note_accepted_in_body` — optional `note` body field accepted | ✅ Pass |

#### Error cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 4 | `test_404_when_not_found` | 404 `RECORD_NOT_FOUND` | ✅ Pass |
| 5 | `test_409_already_approved` | 409 `ALREADY_APPROVED` | ✅ Pass |

#### Auth cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 6 | `test_401_when_no_token` | 401 | ✅ Pass |
| 7 | `test_403_when_employee_role` | 403 | ✅ Pass |

---

## Security Behaviours Verified

| Behaviour | Verified By |
|-----------|-------------|
| Employee cannot view another employee's history | `test_403_employee_views_other` |
| Employee cannot access exception list (HR/admin only) | `test_403_when_employee_role` (exceptions) |
| Employee cannot view attendance record detail | `test_403_when_employee_role` (record_detail) |
| Employee cannot approve records | `test_403_when_employee_role` (approve) |
| HR cannot submit check-in/check-out | `test_403_hr_role` (checkin, checkout) |
| HR cannot view today-status | `test_403_when_hr_role` |
| Unauthenticated requests rejected across all endpoints | Multiple `test_401_*` tests |

---

## Known Limitations Of This Test Run

1. **No real database** — repository and service functions are mocked.
2. **No real MinIO** — face image upload is bypassed by patching at service level.
3. **No real fraud evaluation** — `attendance_service.check_in/check_out` fully mocked; fraud pipeline not exercised here (covered in `tests/fraud/`).
4. **GPS pipeline not exercised** — Haversine geofence logic tested through `tests/geofence/`.

---

## How To Run

```bash
uv run pytest tests/attendance/ -v
uv run pytest tests/attendance/ -v --cov=app --cov-report=term-missing
```

# Report Module — Test Report

**Date**: 2026-05-23
**Environment**: Local (no live database — DB dependency fully mocked)
**Test runner**: `uv run pytest tests/report/ -v`
**Result**: ✅ 40 / 40 passed — 0 failed — 0 skipped
**Duration**: ~15.15s

---

## Coverage By Endpoint

| Endpoint | Tests | Result |
|----------|-------|--------|
| `GET /dashboard/summary` | 10 | ✅ All pass |
| `GET /realtime/employees-location` | 8 | ✅ All pass |
| `GET /reports/attendance` | 11 | ✅ All pass |
| `GET /reports/attendance/export` | 11 | ✅ All pass |

---

## Test Infrastructure

### Strategy
All service functions are patched at `app.services.report_service.<fn>`. The `get_db` dependency is overridden with a `MagicMock` session in `tests/conftest.py`. Auth fixtures patch `app.api.dependencies.get_account_by_id` to return a `SimpleNamespace` account with the desired role. The export endpoint returns a `Response` (binary, not JSON envelope) — its tests verify `Content-Type` and `Content-Disposition` headers rather than parsing JSON. The module introduces a `manager` role fixture in addition to the standard `hr`/`admin`/`employee` set.

### Patch Paths Used

| Patch target | Used in |
|---|---|
| `app.services.report_service.get_dashboard_summary` | `test_dashboard.py` |
| `app.services.report_service.get_realtime_locations` | `test_realtime.py` |
| `app.services.report_service.get_attendance_report` | `test_attendance_report.py` |
| `app.services.report_service.export_attendance_report` | `test_export.py` |
| `app.api.dependencies.get_account_by_id` | `conftest.py` (all tests) |

### Test Fixtures

| Fixture | Role / Purpose | Notable Values |
|---------|---------------|----------------|
| `as_hr` | HR-role auth headers | `account_id=1003`, `role=hr` |
| `as_admin` | Admin-role auth headers | `account_id=1001`, `role=admin` |
| `as_manager` | Manager-role auth headers | `account_id=1004`, `role=manager` |
| `as_employee` | Employee-role auth headers | `account_id=1002`, `role=employee` |
| `make_active_location()` | `ActiveLocationItem` schema object | `employee_id=10`, building/floor filled |
| `make_realtime_location()` | `RealtimeLocationItem` schema object | includes `arcgis_layer_id`, `gps_accuracy` |
| `make_report_data()` | `AttendanceReportData` schema object | 1 employee, 14 work_days, 1 detail row |

---

## Detailed Results

### GET /dashboard/summary — 10 tests

#### Success cases (8)
| # | Test | Status |
|---|------|--------|
| 1 | `test_200_manager_role` — manager can access dashboard | ✅ Pass |
| 2 | `test_200_hr_role` — hr can access dashboard | ✅ Pass |
| 3 | `test_200_admin_role` — admin can access dashboard | ✅ Pass |
| 4 | `test_kpi_fields_present` — all KPI fields present and correct | ✅ Pass |
| 5 | `test_refresh_interval_in_meta` — `meta.refresh_interval_seconds == 60` | ✅ Pass |
| 6 | `test_active_locations_list` — location item fields present | ✅ Pass |
| 7 | `test_date_param_forwarded` — `date` query param forwarded to service | ✅ Pass |
| 8 | `test_defaults_to_today_when_no_date` — service called when no date param | ✅ Pass |

#### Auth cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 9 | `test_401_no_token` | 401 | ✅ Pass |
| 10 | `test_403_employee_role` | 403 | ✅ Pass |

---

### GET /realtime/employees-location — 8 tests

#### Success cases (5)
| # | Test | Status |
|---|------|--------|
| 1 | `test_200_with_items` — location fields including `arcgis_layer_id` and `gps_accuracy` | ✅ Pass |
| 2 | `test_200_empty_list` — empty array when no active check-ins | ✅ Pass |
| 3 | `test_refresh_interval_in_meta` — `meta.refresh_interval_seconds == 30` | ✅ Pass |
| 4 | `test_filters_forwarded` — `building_id`, `floor_id`, `department_id` forwarded | ✅ Pass |
| 5 | `test_location_fields_present` — lat/lng/floor_name/building_name/checked_in_at present | ✅ Pass |

#### Auth cases (3)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 6 | `test_401_no_token` | 401 | ✅ Pass |
| 7 | `test_403_employee_role` | 403 | ✅ Pass |
| 8 | `test_403_manager_role` | 403 (realtime is hr/admin only) | ✅ Pass |

---

### GET /reports/attendance — 11 tests

#### Success cases (7)
| # | Test | Status |
|---|------|--------|
| 1 | `test_200_manager_role` — manager can access report | ✅ Pass |
| 2 | `test_200_hr_role` — hr can access report | ✅ Pass |
| 3 | `test_range_in_response` — `data.range.from` and `data.range.to` match params | ✅ Pass |
| 4 | `test_summary_fields_present` — all 7 summary fields present | ✅ Pass |
| 5 | `test_employees_list_present` — per-employee entries with correct fields | ✅ Pass |
| 6 | `test_details_list_present` — per-day detail rows with worked_minutes/status | ✅ Pass |
| 7 | `test_filters_forwarded` — `department_id` and `employee_id` forwarded | ✅ Pass |

#### Error cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 8 | `test_422_missing_from_date` | 422 | ✅ Pass |
| 9 | `test_422_missing_to_date` | 422 | ✅ Pass |

#### Auth cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 10 | `test_401_no_token` | 401 | ✅ Pass |
| 11 | `test_403_employee_role` | 403 | ✅ Pass |

---

### GET /reports/attendance/export — 11 tests

#### Success cases (5)
| # | Test | Status |
|---|------|--------|
| 1 | `test_200_excel_download` — binary response body matches mock bytes | ✅ Pass |
| 2 | `test_excel_content_type` — `Content-Type` contains xlsx MIME type | ✅ Pass |
| 3 | `test_excel_content_disposition` — `Content-Disposition: attachment` with filename | ✅ Pass |
| 4 | `test_200_pdf_download` — binary response for pdf format | ✅ Pass |
| 5 | `test_pdf_content_type` — `Content-Type` is `application/pdf` | ✅ Pass |

#### Error cases (3)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 6 | `test_400_invalid_format` | 400 `INVALID_EXPORT_FORMAT` | ✅ Pass |
| 7 | `test_404_no_data` | 404 `NO_REPORT_DATA` | ✅ Pass |
| 8 | `test_422_missing_format` | 422 (format param required) | ✅ Pass |

#### Auth cases (3)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 9 | `test_401_no_token` | 401 | ✅ Pass |
| 10 | `test_403_employee_role` | 403 | ✅ Pass |
| 11 | `test_403_manager_role` | 403 (export is hr/admin only) | ✅ Pass |

---

## Security Behaviours Verified

| Behaviour | Verified By |
|-----------|-------------|
| Employee cannot access any report endpoint | `test_403_employee_role` (all 4 files) |
| Manager cannot access realtime locations | `test_403_manager_role` (realtime) |
| Manager cannot export reports | `test_403_manager_role` (export) |
| Unauthenticated requests rejected | `test_401_no_token` (all 4 files) |

---

## Known Limitations Of This Test Run

1. **No real database** — all repository functions are mocked at the service level.
2. **No real Excel/PDF generation** — `export_attendance_report` is patched; actual openpyxl/reportlab output is not validated in tests.
3. **`absent_count` logic** — shift-holder definition (any employee with a Shift record) is not validated in unit tests since repository calls are mocked.

---

## How To Run

```bash
uv run pytest tests/report/ -v
uv run pytest tests/report/ -v --cov=app --cov-report=term-missing
```

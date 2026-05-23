# Report Test Suite

Test files for `Module 7: Report` (`/api/v1/dashboard/*`, `/api/v1/realtime/*`, `/api/v1/reports/*`).

## Files

| File | Endpoint | Tests |
|------|----------|-------|
| `tests/report/test_dashboard.py` | `GET /dashboard/summary` | 10 |
| `tests/report/test_realtime.py` | `GET /realtime/employees-location` | 8 |
| `tests/report/test_attendance_report.py` | `GET /reports/attendance` | 11 |
| `tests/report/test_export.py` | `GET /reports/attendance/export` | 11 |

**Total: 40 tests, all passing.**

## How To Run

```bash
uv run pytest tests/report/ -v
uv run pytest tests/report/test_dashboard.py -v
uv run pytest tests/report/ -v --cov=app --cov-report=term-missing
uv run pytest tests/report/ -x
```

## Architecture

```
TestClient (no live server)
    └── app.dependency_overrides[get_db] = MagicMock session
    └── unittest.mock.patch() for service functions
    └── SimpleNamespace fixtures (Pydantic from_attributes=True compatible)
    └── Export endpoint returns Response (not SuccessResponse) — tests check headers not JSON
    └── manager role fixture added (ManagerOrAboveAccount guard covers manager/hr/admin)
```

## Patch Paths Quick Reference

```python
"app.services.report_service.get_dashboard_summary"
"app.services.report_service.get_realtime_locations"
"app.services.report_service.get_attendance_report"
"app.services.report_service.export_attendance_report"
"app.api.dependencies.get_account_by_id"
```

# Attendance Test Suite

Test files for `Module 2: Attendance` (`/api/v1/attendance/*`).

## Files

| File | Endpoint | Tests |
|------|----------|-------|
| `tests/attendance/test_checkin.py` | `POST /attendance/check-in` | 10 |
| `tests/attendance/test_checkout.py` | `POST /attendance/check-out` | 5 |
| `tests/attendance/test_today_status.py` | `GET /attendance/today-status` | 5 |
| `tests/attendance/test_history.py` | `GET /attendance/history` | 9 |
| `tests/attendance/test_exceptions.py` | `GET /attendance/exceptions` | 6 |
| `tests/attendance/test_record_detail.py` | `GET /attendance/{record_id}` | 5 |
| `tests/attendance/test_approve.py` | `PUT /attendance/{record_id}/approve` | 7 |

**Total: 47 tests, all passing.**

## How To Run

```bash
uv run pytest tests/attendance/ -v
uv run pytest tests/attendance/test_checkin.py -v
uv run pytest tests/attendance/ -v --cov=app --cov-report=term-missing
uv run pytest tests/attendance/ -x
```

## Architecture

```
TestClient (no live server)
    └── app.dependency_overrides[get_db] = MagicMock session
    └── unittest.mock.patch() for service functions
    └── SimpleNamespace fixtures (Pydantic from_attributes=True compatible)
    └── multipart/form-data tests use TestClient(app).post(..., files={...}, data={...})
    └── check-in/check-out patch face upload + fraud eval at service level
```

## Patch Paths Quick Reference

```python
"app.services.attendance_service.check_in"
"app.services.attendance_service.check_out"
"app.services.attendance_service.get_today_status"
"app.services.attendance_service.list_history"
"app.services.attendance_service.list_exceptions"
"app.services.attendance_service.get_record_detail"
"app.services.attendance_service.approve_attendance_record"
"app.api.dependencies.get_account_by_id"
```

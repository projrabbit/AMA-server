# Admin Management Test Suite

Test files for `Module 9: Admin Management` (`/api/v1/employees/*`, `/api/v1/departments/*`, `/api/v1/shifts/*`, `/api/v1/devices/*`).

## Files

| File | Endpoint(s) | Tests |
|------|-------------|-------|
| `tests/admin/test_employees.py` | `GET/POST /employees`, `GET/PUT /employees/{id}`, `PUT /employees/{id}/deactivate`, `PUT /employees/{id}/shift` | 20 |
| `tests/admin/test_departments.py` | `GET/POST /departments`, `PUT /departments/{id}` | 13 |
| `tests/admin/test_shifts.py` | `GET/POST /shifts`, `PUT /shifts/{id}` | 13 |
| `tests/admin/test_devices.py` | `POST /devices/register`, `GET /devices/me`, `GET /devices`, `PUT /devices/{id}/trust` | 16 |

**Total: 74 tests, all passing.**

## How To Run

```bash
uv run pytest tests/admin/ -v
uv run pytest tests/admin/test_employees.py -v
uv run pytest tests/admin/test_departments.py -v
uv run pytest tests/admin/test_shifts.py -v
uv run pytest tests/admin/test_devices.py -v
uv run pytest tests/admin/ -v --cov=app --cov-report=term-missing
uv run pytest tests/admin/ -x
```

## Architecture

```
TestClient (no live server)
    └── app.dependency_overrides[get_db] = MagicMock session
    └── unittest.mock.patch() for service-layer functions
    └── SimpleNamespace fixtures (Pydantic from_attributes=True compatible)
    └── Role-aware auth fixtures patch app.api.dependencies.get_account_by_id
        so that role guards resolve to the correct AccountRole enum value
```

## Patch Paths Quick Reference

```python
# Service-level patches (all tests use these — service imports repo at module level)
"app.services.admin_service.get_employees"
"app.services.admin_service.get_employee_by_id"
"app.services.admin_service.get_employee_by_email"
"app.services.admin_service.get_employee_by_phone"
"app.services.admin_service.get_department_by_id"
"app.services.admin_service.get_department_by_name"
"app.services.admin_service.get_departments"
"app.services.admin_service.create_employee_and_account"
"app.services.admin_service.update_employee_fields"
"app.services.admin_service.deactivate_employee"
"app.services.admin_service.create_department"
"app.services.admin_service.update_department_fields"
"app.services.admin_service.get_shifts"
"app.services.admin_service.get_shift_by_id"
"app.services.admin_service.has_shift_conflict"
"app.services.admin_service.create_shift"
"app.services.admin_service.update_shift_fields"
"app.services.admin_service.assign_shift_to_employee"
"app.services.admin_service.get_devices"
"app.services.admin_service.get_device_by_id"
"app.services.admin_service.get_device_by_fingerprint_and_employee"
"app.services.admin_service.get_devices_for_employee"
"app.services.admin_service.create_device"
"app.services.admin_service.update_device_metadata"
"app.services.admin_service.update_device_trust"
"app.services.admin_service.create_audit_log"

# Dependency-level patch (role guard resolution)
"app.api.dependencies.get_account_by_id"
```

# Authentication Test Suite

Test files for `Module 1: Authentication` (`/api/v1/auth/*`).

## Files

| File | Endpoint | Tests |
|------|----------|-------|
| `tests/auth/test_login.py` | `POST /auth/login` | 15 |
| `tests/auth/test_refresh.py` | `POST /auth/refresh` | 13 |
| `tests/auth/test_me.py` | `GET /auth/me` | 11 |
| `tests/auth/test_logout.py` | `POST /auth/logout` | 9 |
| `tests/auth/test_change_password.py` | `PUT /auth/change-password` | 15 |
| `tests/conftest.py` | Shared fixtures | — |

**Total: 63 tests, all passing.**

## How To Run

```bash
# All auth tests, verbose
uv run pytest tests/auth/ -v

# Single file
uv run pytest tests/auth/test_login.py -v

# With coverage report
uv run pytest tests/auth/ -v --cov=app --cov-report=term-missing

# Stop on first failure
uv run pytest tests/auth/ -x
```

## Architecture

```
TestClient (no live server)
    └── app.dependency_overrides[get_db] = MagicMock session
    └── unittest.mock.patch() for repository functions
    └── Real JWTs issued per test via create_access_token / create_refresh_token
    └── SimpleNamespace fixtures (Pydantic from_attributes=True compatible)
```

## Patch Paths Quick Reference

When writing new tests for auth endpoints, use these patch targets:

```python
# For /login
"app.services.auth_service.get_account_by_username"
"app.services.auth_service.update_last_login"
"app.services.auth_service.create_audit_log"

# For /me, /logout, /change-password  (module-level import in dependencies.py)
"app.api.dependencies.get_account_by_id"

# For /refresh  (inline import inside service function)
"app.repositories.auth_repository.get_account_by_id"
```

## Full Test Report

See [`TEST_REPORT.md`](./TEST_REPORT.md) for the complete run results, per-test breakdown, and security behaviours verified.

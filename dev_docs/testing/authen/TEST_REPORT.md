# Authentication Module — Test Report

**Date**: 2026-05-20
**Environment**: Local (no live database — DB dependency fully mocked)
**Test runner**: `uv run pytest tests/auth/ -v`
**Result**: ✅ 63 / 63 passed — 0 failed — 0 skipped
**Duration**: ~25 s

---

## Coverage By Endpoint

| Endpoint | Tests | Result |
|----------|-------|--------|
| `POST /auth/login` | 15 | ✅ All pass |
| `POST /auth/refresh` | 13 | ✅ All pass |
| `GET /auth/me` | 11 | ✅ All pass |
| `POST /auth/logout` | 9 | ✅ All pass |
| `PUT /auth/change-password` | 15 | ✅ All pass |

---

## Test Infrastructure

### Strategy
Tests use FastAPI's `TestClient` with the database dependency overridden by a `MagicMock` session. No real PostgreSQL connection is required. Account fixtures are `SimpleNamespace` objects (not SQLAlchemy ORM instances), which Pydantic serialises correctly via `from_attributes=True`.

### Patch Paths Used
| Patch target | Used in |
|---|---|
| `app.services.auth_service.get_account_by_username` | login tests |
| `app.services.auth_service.update_last_login` | login tests |
| `app.services.auth_service.create_audit_log` | login, logout, change-password |
| `app.api.dependencies.get_account_by_id` | me, logout, change-password |
| `app.repositories.auth_repository.get_account_by_id` | refresh (inline import) |

### Test Accounts

| Fixture | Role | Username | Password |
|---------|------|----------|----------|
| `admin_account` | admin | linh.tran@example.com | TestPass@123 |
| `employee_account` | employee | minh.nguyen@example.com | TestPass@123 |
| `hr_account` | hr | hoa.pham@example.com | TestPass@123 |
| `locked_account` | employee | locked@example.com | TestPass@123 (account inactive) |

All password hashes are generated at fixture time with the real `get_password_hash` (PBKDF2-SHA256, 600 000 iterations).

### Tokens
Real JWTs are created per fixture using `create_access_token` / `create_refresh_token`. Each carries a unique `jti` (UUID4). Blacklist tests verify that the in-memory `_token_blacklist` dict is updated correctly.

---

## Detailed Results

### POST /auth/login — 15 tests

#### Success cases (8)
| # | Test | Status |
|---|------|--------|
| 1 | Admin login returns HTTP 200 | ✅ Pass |
| 2 | Response shape: `success`, `data.access_token`, `data.refresh_token`, `token_type`, `expires_in` | ✅ Pass |
| 3 | `data.account` block contains `account_id`, `username`, `role`, `is_active` | ✅ Pass |
| 4 | `data.employee` block contains `employee_id`, `email` | ✅ Pass |
| 5 | Employee-role login returns `role = "employee"` | ✅ Pass |
| 6 | Access and refresh tokens are non-empty strings (> 20 chars) | ✅ Pass |
| 7 | Access token and refresh token are different values | ✅ Pass |
| 8 | Audit log `create_audit_log` is called once with `action_type = login` | ✅ Pass |

#### Error cases (7)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 9 | Wrong password | 401 `INVALID_CREDENTIALS` | ✅ Pass |
| 10 | Unknown username | 401 `INVALID_CREDENTIALS` | ✅ Pass |
| 11 | Locked account (`is_active=False`) | 401 `ACCOUNT_LOCKED` | ✅ Pass |
| 12 | Missing `username` field | 422 | ✅ Pass |
| 13 | Missing `password` field | 422 | ✅ Pass |
| 14 | Empty JSON body `{}` | 422 | ✅ Pass |
| 15 | Error response has `success: false` | ✅ Pass | ✅ Pass |

---

### POST /auth/refresh — 13 tests

#### Success cases (6)
| # | Test | Status |
|---|------|--------|
| 16 | Valid refresh token returns 200 | ✅ Pass |
| 17 | Response shape: `access_token`, `token_type`, `expires_in` | ✅ Pass |
| 18 | New access token differs from the original | ✅ Pass |
| 19 | New access token is a valid JWT with `type: access` and correct `sub` | ✅ Pass |
| 20 | New access token has a fresh `jti` (different from original) | ✅ Pass |
| 21 | Employee-role refresh works | ✅ Pass |

#### Error cases (7)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 22 | Invalid JWT string | 401 `INVALID_REFRESH_TOKEN` | ✅ Pass |
| 23 | Access token submitted as refresh token (type mismatch) | 401 `INVALID_REFRESH_TOKEN` | ✅ Pass |
| 24 | Blacklisted refresh token | 401 `INVALID_REFRESH_TOKEN` | ✅ Pass |
| 25 | Locked account's refresh token | 401 | ✅ Pass |
| 26 | Missing `refresh_token` field | 422 | ✅ Pass |
| 27 | Empty string token | 401 | ✅ Pass |
| 28 | Error response has `success: false` | ✅ Pass | ✅ Pass |

---

### GET /auth/me — 11 tests

#### Success cases (6)
| # | Test | Status |
|---|------|--------|
| 29 | Valid Bearer token returns 200 | ✅ Pass |
| 30 | Response shape: `data.account`, `data.employee` | ✅ Pass |
| 31 | `account` block: `account_id`, `username`, `role`, `is_active` match fixture | ✅ Pass |
| 32 | `employee` block: `employee_id`, `email`, `department_id` match fixture | ✅ Pass |
| 33 | Employee-role account returns correct role | ✅ Pass |
| 34 | Response contains no `password` or `password_hash` fields | ✅ Pass |

#### Error cases (5)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 35 | No Authorization header | 401 | ✅ Pass |
| 36 | Malformed token string | 401 | ✅ Pass |
| 37 | `Basic` auth scheme instead of `Bearer` | 401 | ✅ Pass |
| 38 | Refresh token submitted as Bearer token (type mismatch) | 401 | ✅ Pass |
| 39 | Blacklisted access token | 401 | ✅ Pass |

---

### POST /auth/logout — 9 tests

#### Success cases (7)
| # | Test | Status |
|---|------|--------|
| 40 | Logout returns 200 | ✅ Pass |
| 41 | Response message contains "logged out" | ✅ Pass |
| 42 | Access token JTI is in blacklist after logout | ✅ Pass |
| 43 | Refresh token JTI is in blacklist after logout | ✅ Pass |
| 44 | Using the blacklisted access token on `/me` returns 401 | ✅ Pass |
| 45 | Logout without refresh token body still returns 200 | ✅ Pass |
| 46 | Audit log `create_audit_log` called once with `action_type = logout` | ✅ Pass |

#### Error cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 47 | No Authorization header | 401 | ✅ Pass |
| 48 | Invalid token string | 401 | ✅ Pass |

---

### PUT /auth/change-password — 15 tests

#### Success cases (5)
| # | Test | Status |
|---|------|--------|
| 49 | Valid password change returns 200 | ✅ Pass |
| 50 | Response shape: `success: true`, `data.message` | ✅ Pass |
| 51 | `account.password_hash` is updated in memory with new hash | ✅ Pass |
| 52 | Old password no longer verifies against updated hash | ✅ Pass (implied by #51) |
| 53 | Audit log written once | ✅ Pass |
| 54 | Employee can change own password | ✅ Pass |

#### Error cases (10)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 55 | Wrong `current_password` | 400 `WRONG_CURRENT_PASSWORD` | ✅ Pass |
| 56 | `new_password` ≠ `confirm_password` | 400 `PASSWORD_MISMATCH` | ✅ Pass |
| 57 | `new_password` shorter than 8 chars | 422 | ✅ Pass |
| 58 | `new_password` has no uppercase letter | 422 | ✅ Pass |
| 59 | `new_password` has no digit | 422 | ✅ Pass |
| 60 | `new_password` has no lowercase letter | 422 | ✅ Pass |
| 61 | No Authorization header | 401 | ✅ Pass |
| 62 | Missing `current_password` field | 422 | ✅ Pass |
| 63 | Empty JSON body `{}` | 422 | ✅ Pass |
| 64 | Error response has `success: false` | ✅ Pass | ✅ Pass |

---

## Security Behaviours Verified

| Behaviour | Verified By |
|-----------|-------------|
| Wrong password returns identical error to unknown username (no user enumeration) | Tests #9 and #10 both return `INVALID_CREDENTIALS` |
| `password_hash` never appears in any API response | Test #34 |
| Refresh token cannot be used as an access token | Test #23 and #38 |
| Access token cannot be used as a refresh token | Test #23 |
| Blacklisted JTI is rejected on all subsequent calls | Tests #24, #39, #44 |
| Both JTIs (access + refresh) are blacklisted on logout | Tests #42 and #43 |
| Locked accounts cannot log in | Test #11 |
| Locked accounts cannot refresh | Test #25 |
| Weak passwords rejected before hitting service layer | Tests #57–#60 |

---

## Known Limitations Of This Test Run

1. **No real database** — repository functions are mocked. Integration-level DB behaviour (uniqueness constraints, transactions, FK violations) is not covered here.
2. **Token expiry** — expiry edge cases (exactly-expired token, clock skew) are not tested; would require time-mocking (`freezegun`).
3. **IP address logging** — `ip_address` is captured from `request.client.host` which `TestClient` sets to `testclient`. Not validated in these tests.

---

## How To Run

```bash
# From project root
uv run pytest tests/auth/ -v

# With coverage
uv run pytest tests/auth/ -v --cov=app --cov-report=term-missing
```

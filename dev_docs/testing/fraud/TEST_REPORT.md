# Fraud Detection Module — Test Report

**Date**: 2026-05-22
**Environment**: Local (no live database — DB dependency fully mocked)
**Test runner**: `uv run pytest tests/fraud/ -v`
**Result**: ✅ 28 / 28 passed — 0 failed — 0 skipped
**Duration**: ~6.68s

---

## Coverage By Endpoint

| Endpoint | Tests | Result |
|----------|-------|--------|
| `POST /internal/fraud/evaluate` | 14 | ✅ All pass |
| `GET /fraud/records` | 8 | ✅ All pass |
| `GET /fraud/records/{fraud_id}` | 6 | ✅ All pass |

---

## Test Infrastructure

### Strategy

All three endpoints are tested through FastAPI's `TestClient` with `get_db` overridden by a `MagicMock`. The `evaluate` endpoint exercises the full detection pipeline by patching the six underlying sub-functions (device lookup, recent-records query, face reference lookup, MinIO download, landmark extraction, cosine similarity, liveness scoring) at their bound names in `app.services.fraud_service`. The `GET` endpoints patch at the service layer (`list_fraud_records`, `get_fraud_record_detail`) since their business logic was already covered by evaluate tests.

The internal endpoint has no auth dependency and is tested without any Authorization header. Role-guard tests for the public endpoints confirm that `employee` role receives 403 and missing token receives 401.

### Patch Paths Used

| Patch target | Used in |
|---|---|
| `app.services.fraud_service.get_device_by_fingerprint_and_employee` | `test_evaluate.py` |
| `app.services.fraud_service.get_recent_device_records` | `test_evaluate.py` |
| `app.services.fraud_service.get_face_reference` | `test_evaluate.py` |
| `app.services.fraud_service.storage.download_file` | `test_evaluate.py` |
| `app.services.fraud_service._extract_landmarks` | `test_evaluate.py` |
| `app.services.fraud_service._cosine_similarity` | `test_evaluate.py` |
| `app.services.fraud_service._liveness_score` | `test_evaluate.py` |
| `app.services.fraud_service.list_fraud_records` | `test_fraud_records.py` |
| `app.services.fraud_service.get_fraud_record_detail` | `test_fraud_detail.py` |
| `app.api.dependencies.get_account_by_id` | `test_fraud_records.py`, `test_fraud_detail.py` |

### Test Fixtures

| Fixture | Role | Notable values |
|---------|------|----------------|
| `make_department` | Department SimpleNamespace | `department_id=1001`, `name="Engineering"` |
| `make_device` | Device SimpleNamespace | `is_trusted=True` default; `platform` wrapped in `SimpleNamespace(value=...)` |
| `make_attendance_record` | AttendanceRecord SimpleNamespace | Includes nested `.employee` and `.device` |
| `make_employee_with_dept` | Employee SimpleNamespace with `.department` | Wraps `make_employee` and attaches a department |
| `make_fraud_record` | FraudDetection SimpleNamespace | `mock_location_detected=True`, `confidence_score=Decimal("60.0")` default |
| `_FACE_REF` (module-level) | Minimal face reference with `face_object_key` | Used so `storage.download_file(face_ref.face_object_key)` doesn't raise `AttributeError` |
| `_TRUSTED_DEVICE` (module-level) | Trusted device fixture | Prevents `unknown_device=True` in happy-path tests |
| `as_hr` | HR auth headers + `get_account_by_id` patch | Used for all public fraud endpoint tests |
| `as_admin` | Admin auth headers + patch | Used for role confirmation tests |
| `as_employee` | Employee auth headers + patch | Used for 403 role guard tests |

---

## Detailed Results

### POST /internal/fraud/evaluate — 14 tests

#### Success cases (2)
| # | Test | Status |
|---|------|--------|
| 1 | Clean verdict — all flags false, confidence 100.0 | ✅ Pass |
| 2 | No auth required — returns 200 without Authorization header | ✅ Pass |

#### Mock location detection (1)
| # | Test | Status |
|---|------|--------|
| 3 | `is_mock_location=true` → `mock_location_detected=true`, confidence 30.0, reason "mock_location" | ✅ Pass |

#### GPS spoofing detection (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 4 | `speed_mps=10.0` (> 5.0 threshold) → `gps_spoofing_detected=true` | 200 | ✅ Pass |
| 5 | `speed_mps=0.3` (< threshold) → `gps_spoofing_detected=false` | 200 | ✅ Pass |

#### Unknown device detection (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 6 | Device not in DB → `unknown_device=true` | 200 | ✅ Pass |
| 7 | Device exists but `is_trusted=false` → `unknown_device=true` | 200 | ✅ Pass |

#### Buddy punch detection (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 8 | Same device used by different employee in last 24 h → `buddy_punch_suspected=true` | 200 | ✅ Pass |
| 9 | No other employee used device → `buddy_punch_suspected=false` | 200 | ✅ Pass |

#### Face verification (3)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 10 | No face reference stored → `face_mismatch_detected=true` | 200 | ✅ Pass |
| 11 | Cosine similarity 0.5 (< 0.92 threshold) → `face_mismatch_detected=true` | 200 | ✅ Pass |
| 12 | All liveness signals false → `liveness_failed=true` | 200 | ✅ Pass |

#### Confidence score (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 13 | All 6 flags triggered → confidence floored at 0.0 | 200 | ✅ Pass |
| 14 | No flags triggered → confidence 100.0 | 200 | ✅ Pass |

---

### GET /fraud/records — 8 tests

#### Success cases (6)
| # | Test | Status |
|---|------|--------|
| 1 | HR role — returns 200 with record list and correct fields | ✅ Pass |
| 2 | Admin role — returns 200 | ✅ Pass |
| 3 | Pagination meta (`page`, `limit`, `total`, `total_pages`) present | ✅ Pass |
| 4 | `employee_id` filter passed through to service | ✅ Pass |
| 5 | `mock_location=true` filter passed through to service | ✅ Pass |
| 6 | `min_confidence_score` / `max_confidence_score` filters passed through | ✅ Pass |

#### Error cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 7 | No Authorization header | 401 | ✅ Pass |
| 8 | Employee role | 403 `FORBIDDEN` | ✅ Pass |

---

### GET /fraud/records/{fraud_id} — 6 tests

#### Success cases (3)
| # | Test | Status |
|---|------|--------|
| 1 | HR role — returns 200 with full nested detail (employee, attendance, device) | ✅ Pass |
| 2 | Admin role — returns 200 | ✅ Pass |
| 3 | Correct `fraud_id` forwarded to service | ✅ Pass |

#### Error cases (3)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 4 | Non-existent `fraud_id` | 404 `FRAUD_NOT_FOUND` | ✅ Pass |
| 5 | No Authorization header | 401 | ✅ Pass |
| 6 | Employee role | 403 `FORBIDDEN` | ✅ Pass |

---

## Security Behaviours Verified

| Behaviour | Verified By |
|-----------|-------------|
| Internal evaluate endpoint accessible without JWT | Test #2 (test_evaluate) |
| Public fraud endpoints reject unauthenticated requests | Tests #7 (records), #5 (detail) |
| Employee role blocked from fraud list endpoint | Test #8 (records) |
| Employee role blocked from fraud detail endpoint | Test #6 (detail) |

---

## Known Limitations Of This Test Run

1. **No real database** — all repository functions are mocked; SQL query correctness (joins, filters) is not exercised.
2. **No real MinIO** — `storage.download_file` is mocked; actual object download and image decoding not tested.
3. **Face comparison pipeline not fully exercised** — `_extract_landmarks` and `_cosine_similarity` are patched; mediapipe model inference is not invoked in tests.

---

## How To Run

```bash
uv run pytest tests/fraud/ -v
uv run pytest tests/fraud/ -v --cov=app --cov-report=term-missing
```

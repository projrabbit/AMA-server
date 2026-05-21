# Face Verification Module — Test Report

**Date**: 2026-05-22
**Environment**: Local (no live database — DB dependency fully mocked; no live MinIO — storage patched; no mediapipe inference — detection/landmark functions patched)
**Test runner**: `uv run pytest tests/face/ -v`
**Result**: ✅ 22 / 22 passed — 0 failed — 0 skipped
**Duration**: ~29s

---

## Coverage By Endpoint

| Endpoint | Tests | Result |
|----------|-------|--------|
| `POST /employees/{employee_id}/face` | 10 | ✅ All pass |
| `GET /employees/{employee_id}/face` | 4 | ✅ All pass |
| `DELETE /employees/{employee_id}/face` | 4 | ✅ All pass |
| `POST /internal/face/verify` | 4 | ✅ All pass |

---

## Test Infrastructure

### Strategy

All tests use FastAPI's `TestClient` with `get_db` globally overridden by a `MagicMock`. Repository functions are patched at the service-import level (`app.services.face_service.<fn>`). MinIO storage helpers are patched at `app.services.face_service.storage.*` so no live MinIO instance is required. Mediapipe helpers `_detect_faces` and `_extract_landmarks` are always patched — no real CPU/GPU inference runs during tests.

The `_make_jpeg()` helper creates a minimal valid JPEG via Pillow (`Image.new("RGB", (200, 200))`). The image-too-small test uses a 64×64 JPEG which fails the `_MIN_IMAGE_DIMENSION = 128` guard before face detection is reached, so `_detect_faces` is not patched for that case.

The `/internal/face/verify` endpoint carries no auth guard, so no authorization headers are needed for those tests.

### Patch Paths Used

| Patch target | Used in |
|---|---|
| `app.services.face_service.get_employee_by_id` | `test_face_register.py`, `test_face_status.py`, `test_face_delete.py` |
| `app.services.face_service.get_face_reference` | `test_face_register.py`, `test_face_delete.py`, `test_face_verify.py` |
| `app.services.face_service.upsert_face_reference` | `test_face_register.py` |
| `app.services.face_service.delete_face_reference` | `test_face_delete.py` |
| `app.services.face_service.storage.upload_file` | `test_face_register.py` |
| `app.services.face_service.storage.download_file` | `test_face_verify.py` |
| `app.services.face_service.storage.delete_file` | `test_face_register.py`, `test_face_delete.py` |
| `app.services.face_service._detect_faces` | `test_face_register.py` |
| `app.services.face_service._extract_landmarks` | `test_face_verify.py` |
| `app.services.face_service.create_audit_log` | `test_face_register.py`, `test_face_delete.py` |
| `app.api.dependencies.get_account_by_id` | `conftest.py` (via `as_hr`, `as_admin`, `as_employee`) |

### Test Fixtures

| Fixture | Type | Purpose |
|---------|------|---------|
| `as_hr` | `dict` (headers) | HR auth headers + `get_account_by_id` patched to return HR account |
| `as_admin` | `dict` (headers) | Admin auth headers + `get_account_by_id` patched to return admin account |
| `as_employee` | `dict` (headers) | Employee auth headers + `get_account_by_id` patched — used to verify 403 responses |
| `face_ref` | `SimpleNamespace` | `face_id=1, employee_id=1001, face_object_key="faces/employee_1001/reference_2026-05-22.jpg"` |

---

## Detailed Results

### `POST /employees/{employee_id}/face` — 10 tests

#### Success cases (3)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_201_with_face_data` — no prior face; single detection; returns face_registered=True, face_object_key, registered_at | ✅ Pass |
| 2 | `test_replaces_existing_reference` — prior face reference exists; old MinIO object deleted; new reference upserted | ✅ Pass |
| 3 | `test_admin_can_register` — admin role succeeds on the HR-or-admin guard | ✅ Pass |

#### Error cases (7)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 4 | `test_employee_not_found_returns_404` — `get_employee_by_id` returns None | 404 `EMPLOYEE_NOT_FOUND` | ✅ Pass |
| 5 | `test_no_face_detected_returns_400` — `_detect_faces` returns empty list | 400 `NO_FACE_DETECTED` | ✅ Pass |
| 6 | `test_multiple_faces_returns_400` — `_detect_faces` returns 2 detections | 400 `MULTIPLE_FACES` | ✅ Pass |
| 7 | `test_image_too_small_returns_400` — 64×64 JPEG fails dimension guard before detection | 400 `IMAGE_TOO_SMALL` | ✅ Pass |
| 8 | `test_missing_file_returns_422` — no `face_image` field in request | 422 | ✅ Pass |
| 9 | `test_employee_role_is_forbidden` — employee JWT on HR-or-admin endpoint | 403 | ✅ Pass |
| 10 | `test_no_token_returns_401` — no Authorization header | 401 | ✅ Pass |

---

### `GET /employees/{employee_id}/face` — 4 tests

#### Success cases (2)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_registered_true_when_face_exists` — `get_face_reference` returns a ref; face_registered=True, face_object_key and registered_at populated | ✅ Pass |
| 2 | `test_returns_registered_false_when_no_face` — `get_face_reference` returns None; face_registered=False, face_object_key=null, registered_at=null | ✅ Pass |

#### Error cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 3 | `test_employee_not_found_returns_404` | 404 `EMPLOYEE_NOT_FOUND` | ✅ Pass |
| 4 | `test_employee_role_is_forbidden` | 403 | ✅ Pass |

---

### `DELETE /employees/{employee_id}/face` — 4 tests

#### Success cases (1)
| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200_face_removed` — MinIO object deleted, DB row deleted; face_removed=True, employee_id=1001 | ✅ Pass |

#### Error cases (3)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 2 | `test_employee_not_found_returns_404` | 404 `EMPLOYEE_NOT_FOUND` | ✅ Pass |
| 3 | `test_no_face_registered_returns_404` — `get_face_reference` returns None | 404 `FACE_NOT_REGISTERED` | ✅ Pass |
| 4 | `test_hr_role_is_forbidden` — HR is not sufficient; admin-only endpoint | 403 | ✅ Pass |

---

### `POST /internal/face/verify` — 4 tests

#### Success cases (2)
| # | Test | Status |
|---|------|--------|
| 1 | `test_matched_face_and_passed_liveness` — both images return identical landmark vectors (cosine=1.0); all three liveness signals True → liveness_score=1.0, liveness_passed=True | ✅ Pass |
| 2 | `test_failed_liveness_signals` — all liveness signals False → liveness_score=0.0, liveness_passed=False | ✅ Pass |

#### Error cases (2)
| # | Test | Expected | Status |
|---|------|----------|--------|
| 3 | `test_no_face_reference_returns_404` — `get_face_reference` returns None | 404 `FACE_NOT_REGISTERED` | ✅ Pass |
| 4 | `test_no_selfie_face_detected_returns_zero_score` — reference has landmarks, selfie `_extract_landmarks` returns None → face_match_score=0.0, face_matched=False | 200 (zero score) | ✅ Pass |

---

## Security Behaviours Verified

| Behaviour | Verified By |
|-----------|-------------|
| Only HR and admin can register a face | `test_employee_role_is_forbidden`, `test_no_token_returns_401` on POST |
| Only HR and admin can read face status | `test_employee_role_is_forbidden` on GET |
| Only admin (not HR) can delete a face reference | `test_hr_role_is_forbidden` on DELETE |
| Internal verify endpoint requires no token | Verified by calling without headers — 200 returned |
| All user-facing endpoints reject missing token | `test_no_token_returns_401` / `test_401_no_token` present |

---

## Known Limitations Of This Test Run

1. **No real database** — all repository functions are mocked; SQL uniqueness constraint on `employee_id` not exercised.
2. **No live MinIO** — `upload_file`, `download_file`, `delete_file` are patched; actual network connectivity and bucket creation not tested.
3. **No real mediapipe inference** — `_detect_faces` and `_extract_landmarks` are patched with fixed return values; model accuracy not measured.
4. **Face match threshold not boundary-tested** — `_FACE_MATCH_THRESHOLD = 0.92` is correct by inspection; no near-threshold score tested.
5. **File size limit (5 MB) not tested** — bytes-length guard exists in service but no test sends >5 MB payload.
6. **PNG format not separately tested** — JPEG is used in all upload fixtures; PNG path through `_load_pil_image` is untested.

---

## How To Run

```bash
uv run pytest tests/face/ -v
uv run pytest tests/face/ -v --cov=app --cov-report=term-missing
```

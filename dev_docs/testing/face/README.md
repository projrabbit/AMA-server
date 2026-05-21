# Face Verification Test Suite

Test files for `Module 5: Face Verification` (`/api/v1/employees/{id}/face`, `/api/v1/internal/face/verify`).

## Files

| File | Endpoint(s) | Tests |
|------|-------------|-------|
| `tests/face/test_face_register.py` | `POST /employees/{employee_id}/face` | 10 |
| `tests/face/test_face_status.py` | `GET /employees/{employee_id}/face` | 4 |
| `tests/face/test_face_delete.py` | `DELETE /employees/{employee_id}/face` | 4 |
| `tests/face/test_face_verify.py` | `POST /internal/face/verify` | 4 |

**Total: 22 tests, all passing.**

## How To Run

```bash
uv run pytest tests/face/ -v
uv run pytest tests/face/test_face_register.py -v
uv run pytest tests/face/test_face_status.py -v
uv run pytest tests/face/test_face_delete.py -v
uv run pytest tests/face/test_face_verify.py -v
uv run pytest tests/face/ -v --cov=app --cov-report=term-missing
uv run pytest tests/face/ -x
```

## Architecture

```
TestClient (no live server)
    └── app.dependency_overrides[get_db] = MagicMock session
    └── unittest.mock.patch() for service-layer and storage functions
    └── SimpleNamespace fixtures (Pydantic from_attributes=True compatible)
    └── make_face_reference() builds a SimpleNamespace with face_id, employee_id,
        face_object_key, registered_at
    └── _make_jpeg() generates a minimal valid JPEG via Pillow (no real image needed)
    └── mediapipe _detect_faces / _extract_landmarks are always patched — no real
        GPU/CPU inference in tests
    └── MinIO storage.upload_file / storage.download_file / storage.delete_file patched
        — no live MinIO instance needed
    └── /internal/face/verify has no auth guard — no headers required
```

## Patch Paths Quick Reference

```python
# Service-level patches
"app.services.face_service.get_employee_by_id"
"app.services.face_service.get_face_reference"
"app.services.face_service.upsert_face_reference"
"app.services.face_service.delete_face_reference"
"app.services.face_service.storage.upload_file"
"app.services.face_service.storage.download_file"
"app.services.face_service.storage.delete_file"
"app.services.face_service._detect_faces"
"app.services.face_service._extract_landmarks"
"app.services.face_service.create_audit_log"

# Dependency-level patch (role guard resolution)
"app.api.dependencies.get_account_by_id"
```

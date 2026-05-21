"""Tests for POST /employees/{employee_id}/face."""
from __future__ import annotations

import io
from unittest.mock import patch

import pytest
from PIL import Image

from tests.conftest import client
from tests.face.conftest import make_employee_with_face, make_face_reference

_PATCH_GET_EMP = "app.services.face_service.get_employee_by_id"
_PATCH_GET_REF = "app.services.face_service.get_face_reference"
_PATCH_UPSERT = "app.services.face_service.upsert_face_reference"
_PATCH_UPLOAD = "app.services.face_service.storage.upload_file"
_PATCH_DELETE_FILE = "app.services.face_service.storage.delete_file"
_PATCH_DETECT = "app.services.face_service._detect_faces"
_PATCH_AUDIT = "app.services.face_service.create_audit_log"


def _make_jpeg(width: int = 200, height: int = 200) -> bytes:
    img = Image.new("RGB", (width, height), color=(200, 180, 160))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _upload(auth_headers: dict, employee_id: int = 1001, image_bytes: bytes | None = None):
    data = image_bytes or _make_jpeg()
    return client.post(
        f"/api/v1/employees/{employee_id}/face",
        headers=auth_headers,
        files={"face_image": ("face.jpg", data, "image/jpeg")},
    )


class TestRegisterFaceSuccess:
    def test_returns_201_with_face_data(self, as_hr, face_ref):
        emp = make_employee_with_face(face_reference=None)
        with (
            patch(_PATCH_GET_EMP, return_value=emp),
            patch(_PATCH_GET_REF, return_value=None),
            patch(_PATCH_DETECT, return_value=[object()]),
            patch(_PATCH_UPLOAD, return_value="faces/employee_1001/reference_2026-05-22.jpg"),
            patch(_PATCH_UPSERT, return_value=face_ref),
            patch(_PATCH_AUDIT),
        ):
            resp = _upload(as_hr)

        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["employee_id"] == 1001
        assert body["data"]["face_registered"] is True
        assert "face_object_key" in body["data"]

    def test_replaces_existing_reference(self, as_hr, face_ref):
        old_ref = make_face_reference(face_object_key="faces/employee_1001/reference_2026-01-01.jpg")
        with (
            patch(_PATCH_GET_EMP, return_value=make_employee_with_face()),
            patch(_PATCH_GET_REF, return_value=old_ref),
            patch(_PATCH_DETECT, return_value=[object()]),
            patch(_PATCH_DELETE_FILE),
            patch(_PATCH_UPLOAD, return_value=face_ref.face_object_key),
            patch(_PATCH_UPSERT, return_value=face_ref),
            patch(_PATCH_AUDIT),
        ):
            resp = _upload(as_hr)

        assert resp.status_code == 201
        assert resp.json()["data"]["face_registered"] is True

    def test_admin_can_register(self, as_admin, face_ref):
        with (
            patch(_PATCH_GET_EMP, return_value=make_employee_with_face()),
            patch(_PATCH_GET_REF, return_value=None),
            patch(_PATCH_DETECT, return_value=[object()]),
            patch(_PATCH_UPLOAD, return_value=face_ref.face_object_key),
            patch(_PATCH_UPSERT, return_value=face_ref),
            patch(_PATCH_AUDIT),
        ):
            resp = _upload(as_admin)

        assert resp.status_code == 201


class TestRegisterFaceErrors:
    def test_employee_not_found_returns_404(self, as_hr):
        with patch(_PATCH_GET_EMP, return_value=None):
            resp = _upload(as_hr, employee_id=9999)

        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "EMPLOYEE_NOT_FOUND"

    def test_no_face_detected_returns_400(self, as_hr):
        with (
            patch(_PATCH_GET_EMP, return_value=make_employee_with_face()),
            patch(_PATCH_GET_REF, return_value=None),
            patch(_PATCH_DETECT, return_value=[]),
        ):
            resp = _upload(as_hr)

        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "NO_FACE_DETECTED"

    def test_multiple_faces_returns_400(self, as_hr):
        with (
            patch(_PATCH_GET_EMP, return_value=make_employee_with_face()),
            patch(_PATCH_GET_REF, return_value=None),
            patch(_PATCH_DETECT, return_value=[object(), object()]),
        ):
            resp = _upload(as_hr)

        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "MULTIPLE_FACES"

    def test_image_too_small_returns_400(self, as_hr):
        with patch(_PATCH_GET_EMP, return_value=make_employee_with_face()):
            tiny = _make_jpeg(width=64, height=64)
            resp = _upload(as_hr, image_bytes=tiny)

        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "IMAGE_TOO_SMALL"

    def test_missing_file_returns_422(self, as_hr):
        resp = client.post("/api/v1/employees/1001/face", headers=as_hr)
        assert resp.status_code == 422

    def test_employee_role_is_forbidden(self, as_employee):
        resp = _upload(as_employee)
        assert resp.status_code == 403

    def test_no_token_returns_401(self):
        resp = _upload({})
        assert resp.status_code == 401

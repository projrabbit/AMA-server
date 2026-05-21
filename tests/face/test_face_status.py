"""Tests for GET /employees/{employee_id}/face."""
from __future__ import annotations

from unittest.mock import patch

from tests.conftest import client
from tests.face.conftest import make_employee_with_face, make_face_reference

_PATCH_GET_EMP = "app.services.face_service.get_employee_by_id"
_PATCH_GET_REF = "app.services.face_service.get_face_reference"


def _get(auth_headers: dict, employee_id: int = 1001):
    return client.get(f"/api/v1/employees/{employee_id}/face", headers=auth_headers)


class TestGetFaceStatus:
    def test_returns_registered_true_when_face_exists(self, as_hr, face_ref):
        with (
            patch(_PATCH_GET_EMP, return_value=make_employee_with_face()),
            patch(_PATCH_GET_REF, return_value=face_ref),
        ):
            resp = _get(as_hr)

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["face_registered"] is True
        assert body["data"]["face_object_key"] == face_ref.face_object_key
        assert body["data"]["registered_at"] is not None

    def test_returns_registered_false_when_no_face(self, as_hr):
        with (
            patch(_PATCH_GET_EMP, return_value=make_employee_with_face()),
            patch(_PATCH_GET_REF, return_value=None),
        ):
            resp = _get(as_hr)

        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["face_registered"] is False
        assert body["data"]["face_object_key"] is None
        assert body["data"]["registered_at"] is None

    def test_employee_not_found_returns_404(self, as_hr):
        with patch(_PATCH_GET_EMP, return_value=None):
            resp = _get(as_hr, employee_id=9999)

        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "EMPLOYEE_NOT_FOUND"

    def test_employee_role_is_forbidden(self, as_employee):
        resp = _get(as_employee)
        assert resp.status_code == 403

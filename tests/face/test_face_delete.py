"""Tests for DELETE /employees/{employee_id}/face."""
from __future__ import annotations

from unittest.mock import patch

from tests.conftest import client
from tests.face.conftest import make_employee_with_face, make_face_reference

_PATCH_GET_EMP = "app.services.face_service.get_employee_by_id"
_PATCH_GET_REF = "app.services.face_service.get_face_reference"
_PATCH_DELETE_REF = "app.services.face_service.delete_face_reference"
_PATCH_DELETE_FILE = "app.services.face_service.storage.delete_file"
_PATCH_AUDIT = "app.services.face_service.create_audit_log"


def _delete(auth_headers: dict, employee_id: int = 1001):
    return client.delete(f"/api/v1/employees/{employee_id}/face", headers=auth_headers)


class TestDeleteFace:
    def test_returns_200_face_removed(self, as_admin, face_ref):
        with (
            patch(_PATCH_GET_EMP, return_value=make_employee_with_face()),
            patch(_PATCH_GET_REF, return_value=face_ref),
            patch(_PATCH_DELETE_FILE),
            patch(_PATCH_DELETE_REF),
            patch(_PATCH_AUDIT),
        ):
            resp = _delete(as_admin)

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["face_removed"] is True
        assert body["data"]["employee_id"] == 1001

    def test_employee_not_found_returns_404(self, as_admin):
        with patch(_PATCH_GET_EMP, return_value=None):
            resp = _delete(as_admin, employee_id=9999)

        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "EMPLOYEE_NOT_FOUND"

    def test_no_face_registered_returns_404(self, as_admin):
        with (
            patch(_PATCH_GET_EMP, return_value=make_employee_with_face()),
            patch(_PATCH_GET_REF, return_value=None),
        ):
            resp = _delete(as_admin)

        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "FACE_NOT_REGISTERED"

    def test_hr_role_is_forbidden(self, as_hr):
        resp = _delete(as_hr)
        assert resp.status_code == 403

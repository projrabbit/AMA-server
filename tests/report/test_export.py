"""Tests for GET /reports/attendance/export."""
from __future__ import annotations

from unittest.mock import patch

from fastapi import HTTPException

from tests.conftest import client

_PATCH = "app.services.report_service.export_attendance_report"

_EXCEL_CT = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_PDF_CT = "application/pdf"
_FAKE_BYTES = b"fake-binary-content"

_BASE_PARAMS = {"from": "2026-05-01", "to": "2026-05-20"}


def _get(headers: dict, params: dict):
    return client.get("/api/v1/reports/attendance/export", headers=headers, params=params)


class TestExportSuccess:
    def test_200_excel_download(self, as_hr):
        with patch(_PATCH, return_value=(_FAKE_BYTES, "attendance_report_2026-05-01_2026-05-20.xlsx", _EXCEL_CT)):
            resp = _get(as_hr, {**_BASE_PARAMS, "format": "excel"})
        assert resp.status_code == 200
        assert resp.content == _FAKE_BYTES

    def test_excel_content_type(self, as_hr):
        with patch(_PATCH, return_value=(_FAKE_BYTES, "report.xlsx", _EXCEL_CT)):
            resp = _get(as_hr, {**_BASE_PARAMS, "format": "excel"})
        assert _EXCEL_CT in resp.headers["content-type"]

    def test_excel_content_disposition(self, as_hr):
        filename = "attendance_report_2026-05-01_2026-05-20.xlsx"
        with patch(_PATCH, return_value=(_FAKE_BYTES, filename, _EXCEL_CT)):
            resp = _get(as_hr, {**_BASE_PARAMS, "format": "excel"})
        assert "attachment" in resp.headers["content-disposition"]
        assert filename in resp.headers["content-disposition"]

    def test_200_pdf_download(self, as_admin):
        with patch(_PATCH, return_value=(_FAKE_BYTES, "attendance_report_2026-05-01_2026-05-20.pdf", _PDF_CT)):
            resp = _get(as_admin, {**_BASE_PARAMS, "format": "pdf"})
        assert resp.status_code == 200
        assert resp.content == _FAKE_BYTES

    def test_pdf_content_type(self, as_admin):
        with patch(_PATCH, return_value=(_FAKE_BYTES, "report.pdf", _PDF_CT)):
            resp = _get(as_admin, {**_BASE_PARAMS, "format": "pdf"})
        assert _PDF_CT in resp.headers["content-type"]


class TestExportErrors:
    def test_400_invalid_format(self, as_hr):
        with patch(
            _PATCH,
            side_effect=HTTPException(
                status_code=400,
                detail={"code": "INVALID_EXPORT_FORMAT", "message": "Format must be 'excel' or 'pdf'", "details": {}},
            ),
        ):
            resp = _get(as_hr, {**_BASE_PARAMS, "format": "csv"})
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_EXPORT_FORMAT"

    def test_404_no_data(self, as_hr):
        with patch(
            _PATCH,
            side_effect=HTTPException(
                status_code=404,
                detail={"code": "NO_REPORT_DATA", "message": "No attendance data found", "details": {}},
            ),
        ):
            resp = _get(as_hr, {**_BASE_PARAMS, "format": "excel"})
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "NO_REPORT_DATA"

    def test_422_missing_format(self, as_hr):
        resp = _get(as_hr, {**_BASE_PARAMS})
        assert resp.status_code == 422


class TestExportAuth:
    def test_401_no_token(self):
        resp = _get({}, {**_BASE_PARAMS, "format": "excel"})
        assert resp.status_code == 401

    def test_403_employee_role(self, as_employee):
        resp = _get(as_employee, {**_BASE_PARAMS, "format": "excel"})
        assert resp.status_code == 403

    def test_403_manager_role(self, as_manager):
        resp = _get(as_manager, {**_BASE_PARAMS, "format": "excel"})
        assert resp.status_code == 403

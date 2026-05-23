from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Query, Response

from app.api.dependencies import DbSession, HROrAdminAccount, ManagerOrAboveAccount
from app.schemas.common import SuccessResponse
from app.schemas.report import AttendanceReportData, DashboardSummaryData, RealtimeLocationItem
from app.services import report_service

dashboard_router = APIRouter()
realtime_router = APIRouter()
reports_router = APIRouter()


@dashboard_router.get("/summary", response_model=SuccessResponse[DashboardSummaryData])
def get_dashboard_summary(
    account: ManagerOrAboveAccount,
    db: DbSession,
    target_date: date | None = Query(default=None, alias="date"),
):
    if target_date is None:
        target_date = datetime.now(timezone(timedelta(hours=7))).date()
    data = report_service.get_dashboard_summary(db, target_date)
    return SuccessResponse(data=data, meta={"refresh_interval_seconds": 60})


@realtime_router.get("/employees-location", response_model=SuccessResponse[list[RealtimeLocationItem]])
def get_realtime_locations(
    account: HROrAdminAccount,
    db: DbSession,
    building_id: int | None = None,
    floor_id: int | None = None,
    department_id: int | None = None,
):
    data = report_service.get_realtime_locations(
        db, building_id=building_id, floor_id=floor_id, department_id=department_id
    )
    return SuccessResponse(data=data, meta={"refresh_interval_seconds": 30})


# /attendance/export must be registered before /attendance to prevent path conflict
@reports_router.get("/attendance/export")
def export_attendance_report(
    account: HROrAdminAccount,
    db: DbSession,
    format: str = Query(...),
    from_: date = Query(..., alias="from"),
    to: date = Query(...),
    department_id: int | None = None,
    employee_id: int | None = None,
):
    content, filename, content_type = report_service.export_attendance_report(
        db, format, from_, to, department_id=department_id, employee_id=employee_id
    )
    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@reports_router.get("/attendance", response_model=SuccessResponse[AttendanceReportData])
def get_attendance_report(
    account: ManagerOrAboveAccount,
    db: DbSession,
    from_: date = Query(..., alias="from"),
    to: date = Query(...),
    department_id: int | None = None,
    employee_id: int | None = None,
):
    data = report_service.get_attendance_report(
        db, from_, to, department_id=department_id, employee_id=employee_id
    )
    return SuccessResponse(data=data)

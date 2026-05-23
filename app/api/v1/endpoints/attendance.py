from __future__ import annotations

from datetime import date

from fastapi import APIRouter, File, Form, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentAccount, DbSession, EmployeeAccount, HROrAdminAccount
from app.schemas.attendance import ApproveRequest, AttendanceHistoryData
from app.schemas.common import SuccessResponse
from app.services import attendance_service

router = APIRouter()


@router.post("/check-in", status_code=201)
async def check_in(
    request: Request,
    account: EmployeeAccount,
    db: DbSession,
    device_fingerprint: str = Form(...),
    platform: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    altitude: float = Form(...),
    gps_accuracy: float = Form(...),
    liveness_signals: str = Form(...),
    face_image: UploadFile = File(...),
    employee_id: int | None = Form(None),
    model: str | None = Form(None),
    captured_at: str | None = Form(None),
    is_mock_location: bool = Form(False),
    raw_signals: str | None = Form(None),
):
    face_bytes = await face_image.read()
    result = attendance_service.check_in(
        db,
        account=account,
        employee_id_form=employee_id,
        device_fingerprint=device_fingerprint,
        platform_str=platform,
        model=model,
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        gps_accuracy=gps_accuracy,
        liveness_signals_json=liveness_signals,
        raw_signals_json=raw_signals,
        face_image_bytes=face_bytes,
        face_image_content_type=face_image.content_type or "image/jpeg",
        is_mock_location=is_mock_location,
        ip_address=request.client.host if request.client else None,
    )
    return SuccessResponse(data=result)


@router.post("/check-out", status_code=201)
async def check_out(
    request: Request,
    account: EmployeeAccount,
    db: DbSession,
    device_fingerprint: str = Form(...),
    platform: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    altitude: float = Form(...),
    gps_accuracy: float = Form(...),
    liveness_signals: str = Form(...),
    face_image: UploadFile = File(...),
    employee_id: int | None = Form(None),
    model: str | None = Form(None),
    captured_at: str | None = Form(None),
    is_mock_location: bool = Form(False),
    raw_signals: str | None = Form(None),
):
    face_bytes = await face_image.read()
    result = attendance_service.check_out(
        db,
        account=account,
        employee_id_form=employee_id,
        device_fingerprint=device_fingerprint,
        platform_str=platform,
        model=model,
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        gps_accuracy=gps_accuracy,
        liveness_signals_json=liveness_signals,
        raw_signals_json=raw_signals,
        face_image_bytes=face_bytes,
        face_image_content_type=face_image.content_type or "image/jpeg",
        is_mock_location=is_mock_location,
        ip_address=request.client.host if request.client else None,
    )
    return SuccessResponse(data=result)


@router.get("/today-status")
def today_status(account: EmployeeAccount, db: DbSession):
    result = attendance_service.get_today_status(db, account)
    return SuccessResponse(data=result)


@router.get("/history")
def history(
    account: CurrentAccount,
    db: DbSession,
    from_: date = Query(..., alias="from"),
    to: date = Query(...),
    employee_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    data, total, cur_page, cur_limit, total_pages = attendance_service.list_history(
        db,
        account,
        employee_id=employee_id,
        from_date=from_,
        to_date=to,
        page=page,
        limit=limit,
    )
    return SuccessResponse(
        data=data,
        meta={"page": cur_page, "limit": cur_limit, "total": total, "total_pages": total_pages},
    )


@router.get("/exceptions")
def exceptions(
    account: HROrAdminAccount,
    db: DbSession,
    from_: date | None = Query(None, alias="from"),
    to: date | None = Query(None),
    status: str | None = Query(None),
    department_id: int | None = Query(None),
    employee_id: int | None = Query(None),
    reason: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    items, total = attendance_service.list_exceptions(
        db,
        employee_id=employee_id,
        department_id=department_id,
        from_date=from_,
        to_date=to,
        status_filter=status,
        reason=reason,
        page=page,
        limit=limit,
    )
    total_pages = max(1, (total + limit - 1) // limit)
    return SuccessResponse(
        data=items,
        meta={"page": page, "limit": limit, "total": total, "total_pages": total_pages},
    )


@router.get("/{record_id}")
def record_detail(record_id: int, account: HROrAdminAccount, db: DbSession):
    result = attendance_service.get_record_detail(db, record_id)
    return SuccessResponse(data=result)


@router.put("/{record_id}/approve")
def approve(
    record_id: int,
    request: Request,
    body: ApproveRequest,
    account: HROrAdminAccount,
    db: DbSession,
):
    result = attendance_service.approve_attendance_record(
        db,
        record_id,
        account=account,
        ip_address=request.client.host if request.client else None,
    )
    return SuccessResponse(data=result)

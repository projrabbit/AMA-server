from __future__ import annotations

from fastapi import APIRouter, Query, Request, status

from app.api.dependencies import DbSession, HROrAdminAccount
from app.schemas.admin import CreateShiftRequest, UpdateShiftRequest
from app.schemas.common import SuccessResponse
from app.services import admin_service

router = APIRouter()


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=SuccessResponse[list])
def list_shifts(
    account: HROrAdminAccount,
    db: DbSession,
    employee_id: int | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> SuccessResponse:
    items, meta = admin_service.list_shifts(db, employee_id=employee_id, page=page, limit=limit)
    return SuccessResponse(data=[i.model_dump() for i in items], meta=meta)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SuccessResponse)
def create_shift(
    body: CreateShiftRequest,
    request: Request,
    account: HROrAdminAccount,
    db: DbSession,
) -> SuccessResponse:
    data = admin_service.create_shift_svc(
        db,
        account.account_id,
        employee_id=body.employee_id,
        name=body.name,
        start_time=body.start_time,
        end_time=body.end_time,
        late_tolerance_min=body.late_tolerance_min,
        early_leave_min=body.early_leave_min,
        apply_to_weekends=body.apply_to_weekends,
        ip_address=_ip(request),
    )
    return SuccessResponse(data=data.model_dump())


@router.put("/{shift_id}", response_model=SuccessResponse)
def update_shift(
    shift_id: int,
    body: UpdateShiftRequest,
    request: Request,
    account: HROrAdminAccount,
    db: DbSession,
) -> SuccessResponse:
    data = admin_service.update_shift_svc(
        db,
        account.account_id,
        shift_id,
        name=body.name,
        start_time=body.start_time,
        end_time=body.end_time,
        late_tolerance_min=body.late_tolerance_min,
        early_leave_min=body.early_leave_min,
        apply_to_weekends=body.apply_to_weekends,
        ip_address=_ip(request),
    )
    return SuccessResponse(data=data.model_dump())

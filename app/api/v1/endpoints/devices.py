from __future__ import annotations

from fastapi import APIRouter, Query, Request, status

from app.api.dependencies import AdminAccount, DbSession, EmployeeAccount
from app.models.business import DevicePlatform
from app.schemas.admin import RegisterDeviceRequest, TrustDeviceRequest
from app.schemas.common import SuccessResponse
from app.services import admin_service

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=SuccessResponse)
def register_device(
    body: RegisterDeviceRequest,
    account: EmployeeAccount,
    db: DbSession,
) -> SuccessResponse:
    data = admin_service.register_device_svc(
        db,
        account.employee_id,
        device_fingerprint=body.device_fingerprint,
        platform=body.platform,
        model=body.model,
        os_version=body.os_version,
        app_version=body.app_version,
    )
    return SuccessResponse(data=data.model_dump())


@router.get("/me", response_model=SuccessResponse[list])
def get_my_devices(
    account: EmployeeAccount,
    db: DbSession,
) -> SuccessResponse:
    devices = admin_service.get_my_devices_svc(db, account.employee_id)
    return SuccessResponse(data=[d.model_dump() for d in devices])


@router.get("", response_model=SuccessResponse[list])
def list_devices(
    account: AdminAccount,
    db: DbSession,
    employee_id: int | None = None,
    is_trusted: bool | None = None,
    platform: DevicePlatform | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> SuccessResponse:
    items, meta = admin_service.list_devices_svc(
        db,
        employee_id=employee_id,
        is_trusted=is_trusted,
        platform=platform,
        page=page,
        limit=limit,
    )
    return SuccessResponse(data=[i.model_dump() for i in items], meta=meta)


@router.put("/{device_id}/trust", response_model=SuccessResponse)
def trust_device(
    device_id: int,
    body: TrustDeviceRequest,
    request: Request,
    account: AdminAccount,
    db: DbSession,
) -> SuccessResponse:
    ip = request.client.host if request.client else None
    data = admin_service.trust_device_svc(
        db, account.account_id, device_id, body.is_trusted, ip
    )
    return SuccessResponse(data=data.model_dump())

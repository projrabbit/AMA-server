from __future__ import annotations

from fastapi import APIRouter, Query, Request, status

from app.api.dependencies import DbSession, HROrAdminAccount
from app.schemas.admin import CreateDepartmentRequest, UpdateDepartmentRequest
from app.schemas.common import SuccessResponse
from app.services import admin_service

router = APIRouter()


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=SuccessResponse[list])
def list_departments(
    account: HROrAdminAccount,
    db: DbSession,
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> SuccessResponse:
    items, meta = admin_service.list_departments(db, q=q, page=page, limit=limit)
    return SuccessResponse(data=[i.model_dump() for i in items], meta=meta)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SuccessResponse)
def create_department(
    body: CreateDepartmentRequest,
    account: HROrAdminAccount,
    db: DbSession,
) -> SuccessResponse:
    data = admin_service.create_department_svc(
        db,
        name=body.name,
        description=body.description,
        manager_id=body.manager_id,
    )
    return SuccessResponse(data=data.model_dump())


@router.put("/{department_id}", response_model=SuccessResponse)
def update_department(
    department_id: int,
    body: UpdateDepartmentRequest,
    request: Request,
    account: HROrAdminAccount,
    db: DbSession,
) -> SuccessResponse:
    data = admin_service.update_department_svc(
        db,
        account.account_id,
        department_id,
        name=body.name,
        description=body.description,
        manager_id=body.manager_id,
        ip_address=_ip(request),
    )
    return SuccessResponse(data=data.model_dump())

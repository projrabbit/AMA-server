from __future__ import annotations

import math

from fastapi import APIRouter, Query, Request, status

from app.api.dependencies import DbSession, HROrAdminAccount
from app.models.business import EmployeeStatus
from app.schemas.admin import (
    AssignShiftRequest,
    CreateEmployeeRequest,
    DeactivateEmployeeRequest,
    UpdateEmployeeRequest,
)
from app.schemas.common import SuccessResponse
from app.services import admin_service

router = APIRouter()


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=SuccessResponse[list])
def list_employees(
    account: HROrAdminAccount,
    db: DbSession,
    department_id: int | None = None,
    status_filter: EmployeeStatus | None = Query(default=None, alias="status"),
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> SuccessResponse:
    items, meta = admin_service.list_employees(
        db,
        department_id=department_id,
        status=status_filter,
        q=q,
        page=page,
        limit=limit,
    )
    return SuccessResponse(data=[i.model_dump() for i in items], meta=meta)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SuccessResponse)
def create_employee(
    body: CreateEmployeeRequest,
    request: Request,
    account: HROrAdminAccount,
    db: DbSession,
) -> SuccessResponse:
    data = admin_service.create_employee(
        db,
        account.account_id,
        full_name=body.full_name,
        department_id=body.department_id,
        position=body.position,
        email=str(body.email),
        phone=body.phone,
        hire_date=body.hire_date,
        role=body.role,
        temporary_password=body.temporary_password,
        ip_address=_ip(request),
    )
    return SuccessResponse(data=data.model_dump())


@router.get("/{employee_id}", response_model=SuccessResponse)
def get_employee_detail(
    employee_id: int,
    account: HROrAdminAccount,
    db: DbSession,
) -> SuccessResponse:
    data = admin_service.get_employee_detail(db, employee_id)
    return SuccessResponse(data=data.model_dump())


@router.put("/{employee_id}", response_model=SuccessResponse)
def update_employee(
    employee_id: int,
    body: UpdateEmployeeRequest,
    request: Request,
    account: HROrAdminAccount,
    db: DbSession,
) -> SuccessResponse:
    data = admin_service.update_employee(
        db,
        account.account_id,
        employee_id,
        full_name=body.full_name,
        department_id=body.department_id,
        position=body.position,
        email=str(body.email) if body.email else None,
        phone=body.phone,
        hire_date=body.hire_date,
        employee_status=body.status,
        ip_address=_ip(request),
    )
    return SuccessResponse(data=data.model_dump())


@router.put("/{employee_id}/deactivate", response_model=SuccessResponse)
def deactivate_employee(
    employee_id: int,
    body: DeactivateEmployeeRequest,
    request: Request,
    account: HROrAdminAccount,
    db: DbSession,
) -> SuccessResponse:
    data = admin_service.deactivate_employee_svc(
        db, account.account_id, employee_id, _ip(request)
    )
    return SuccessResponse(data=data.model_dump())


@router.put("/{employee_id}/shift", response_model=SuccessResponse)
def assign_shift(
    employee_id: int,
    body: AssignShiftRequest,
    request: Request,
    account: HROrAdminAccount,
    db: DbSession,
) -> SuccessResponse:
    data = admin_service.assign_shift_svc(
        db, account.account_id, employee_id, body.shift_id, _ip(request)
    )
    return SuccessResponse(data=data.model_dump())

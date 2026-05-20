from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.dependencies import AdminAccount, DbSession, HROrAdminAccount
from app.schemas.common import SuccessResponse
from app.schemas.geofence import (
    CreateBuildingRequest,
    CreateFloorRequest,
    UpdateBuildingRequest,
)
from app.services import geofence_service

router = APIRouter()


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/")
def list_buildings(
    account: HROrAdminAccount,
    db: DbSession,
    q: str | None = None,
    include_floors: bool = False,
) -> SuccessResponse:
    data = geofence_service.list_buildings_svc(db, q=q, include_floors=include_floors)
    return SuccessResponse(data=data)


@router.post("/", status_code=201)
def create_building(
    body: CreateBuildingRequest,
    request: Request,
    account: AdminAccount,
    db: DbSession,
) -> SuccessResponse:
    data = geofence_service.create_building_svc(db, account.account_id, body, _ip(request))
    return SuccessResponse(data=data)


@router.put("/{building_id}")
def update_building(
    building_id: int,
    body: UpdateBuildingRequest,
    request: Request,
    account: AdminAccount,
    db: DbSession,
) -> SuccessResponse:
    data = geofence_service.update_building_svc(db, account.account_id, building_id, body, _ip(request))
    return SuccessResponse(data=data)


@router.get("/{building_id}/floors")
def list_floors(
    building_id: int,
    account: HROrAdminAccount,
    db: DbSession,
) -> SuccessResponse:
    data = geofence_service.list_floors_svc(db, building_id)
    return SuccessResponse(data=data)


@router.post("/{building_id}/floors", status_code=201)
def create_floor(
    building_id: int,
    body: CreateFloorRequest,
    request: Request,
    account: AdminAccount,
    db: DbSession,
) -> SuccessResponse:
    data = geofence_service.create_floor_svc(db, account.account_id, building_id, body, _ip(request))
    return SuccessResponse(data=data)

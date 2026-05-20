from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.dependencies import DbSession, HROrAdminAccount
from app.schemas.common import SuccessResponse
from app.schemas.geofence import CreateGeofenceRequest, UpdateGeofenceRequest
from app.services import geofence_service

router = APIRouter()


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/")
def list_geofences(
    account: HROrAdminAccount,
    db: DbSession,
    building_id: int | None = None,
    floor_id: int | None = None,
    is_active: bool | None = None,
) -> SuccessResponse:
    data = geofence_service.list_geofences_svc(
        db, building_id=building_id, floor_id=floor_id, is_active=is_active
    )
    return SuccessResponse(data=data)


@router.post("/", status_code=201)
def create_geofence(
    body: CreateGeofenceRequest,
    request: Request,
    account: HROrAdminAccount,
    db: DbSession,
) -> SuccessResponse:
    data = geofence_service.create_geofence_svc(db, account.account_id, body, _ip(request))
    return SuccessResponse(data=data)


@router.put("/{geofence_id}")
def update_geofence(
    geofence_id: int,
    body: UpdateGeofenceRequest,
    request: Request,
    account: HROrAdminAccount,
    db: DbSession,
) -> SuccessResponse:
    data = geofence_service.update_geofence_svc(db, account.account_id, geofence_id, body, _ip(request))
    return SuccessResponse(data=data)


@router.delete("/{geofence_id}")
def disable_geofence(
    geofence_id: int,
    request: Request,
    account: HROrAdminAccount,
    db: DbSession,
) -> SuccessResponse:
    data = geofence_service.disable_geofence_svc(db, account.account_id, geofence_id, _ip(request))
    return SuccessResponse(data=data)

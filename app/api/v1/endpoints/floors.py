from __future__ import annotations

from fastapi import APIRouter

from app.api.dependencies import AdminAccount, DbSession
from app.schemas.common import SuccessResponse
from app.schemas.geofence import UpdateFloorRequest
from app.services import geofence_service

router = APIRouter()


@router.put("/{floor_id}")
def update_floor(
    floor_id: int,
    body: UpdateFloorRequest,
    account: AdminAccount,
    db: DbSession,
) -> SuccessResponse:
    data = geofence_service.update_floor_svc(db, floor_id, body)
    return SuccessResponse(data=data)

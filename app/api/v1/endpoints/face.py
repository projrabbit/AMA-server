from __future__ import annotations

from fastapi import APIRouter, File, Form, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.dependencies import AdminAccount, DbSession, HROrAdminAccount
from app.schemas.common import SuccessResponse
from app.schemas.face import DeleteFaceData, FaceStatusData, RegisterFaceData, VerifyFaceData
from app.services import face_service

employee_face_router = APIRouter()
internal_face_router = APIRouter()


@employee_face_router.post(
    "/{employee_id}/face",
    response_model=SuccessResponse[RegisterFaceData],
    status_code=201,
)
async def register_face(
    employee_id: int,
    request: Request,
    account: HROrAdminAccount,
    db: DbSession,
    face_image: UploadFile = File(...),
):
    file_bytes = await face_image.read()
    result = face_service.register_employee_face(
        db=db,
        employee_id=employee_id,
        actor_account_id=account.account_id,
        file_bytes=file_bytes,
        filename=face_image.filename or "face.jpg",
        ip_address=request.client.host if request.client else None,
    )
    return SuccessResponse(data=result)


@employee_face_router.get(
    "/{employee_id}/face",
    response_model=SuccessResponse[FaceStatusData],
)
def get_face_status(
    employee_id: int,
    account: HROrAdminAccount,
    db: DbSession,
):
    result = face_service.get_face_status(db=db, employee_id=employee_id)
    return SuccessResponse(data=result)


@employee_face_router.delete(
    "/{employee_id}/face",
    response_model=SuccessResponse[DeleteFaceData],
)
def delete_face(
    employee_id: int,
    request: Request,
    account: AdminAccount,
    db: DbSession,
):
    result = face_service.remove_employee_face(
        db=db,
        employee_id=employee_id,
        actor_account_id=account.account_id,
        ip_address=request.client.host if request.client else None,
    )
    return SuccessResponse(data=result)


@internal_face_router.post(
    "/face/verify",
    response_model=SuccessResponse[VerifyFaceData],
)
async def verify_face(
    db: DbSession,
    employee_id: int = Form(...),
    face_image: UploadFile = File(...),
    liveness_signals: str = Form(...),
):
    selfie_bytes = await face_image.read()
    result = face_service.verify_face_internal(
        db=db,
        employee_id=employee_id,
        selfie_bytes=selfie_bytes,
        liveness_signals_raw=liveness_signals,
    )
    return SuccessResponse(data=result)

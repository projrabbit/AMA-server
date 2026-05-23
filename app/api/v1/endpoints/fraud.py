from __future__ import annotations

import math
from datetime import date

from fastapi import APIRouter, Query

from app.api.dependencies import DbSession, HROrAdminAccount
from app.schemas.common import SuccessResponse
from app.schemas.fraud import (
    EvaluateFraudRequest,
    EvaluateFraudResult,
    FraudRecordDetailData,
    FraudRecordItem,
)
from app.services import fraud_service

internal_fraud_router = APIRouter()
fraud_router = APIRouter()


@internal_fraud_router.post(
    "/fraud/evaluate",
    response_model=SuccessResponse[EvaluateFraudResult],
)
def evaluate_fraud(
    payload: EvaluateFraudRequest,
    db: DbSession,
):
    result = fraud_service.evaluate_fraud(db=db, payload=payload)
    return SuccessResponse(data=result)


@fraud_router.get(
    "/records",
    response_model=SuccessResponse[list[FraudRecordItem]],
)
def list_fraud_records(
    account: HROrAdminAccount,
    db: DbSession,
    employee_id: int | None = None,
    from_: date | None = Query(None, alias="from"),
    to: date | None = None,
    mock_location: bool | None = None,
    gps_spoofing: bool | None = None,
    buddy_punch: bool | None = None,
    unknown_device: bool | None = None,
    face_mismatch: bool | None = None,
    min_confidence_score: float | None = None,
    max_confidence_score: float | None = None,
    page: int = 1,
    limit: int = Query(default=20, le=100),
):
    items, total = fraud_service.list_fraud_records(
        db,
        employee_id=employee_id,
        from_date=from_,
        to_date=to,
        mock_location=mock_location,
        gps_spoofing=gps_spoofing,
        buddy_punch=buddy_punch,
        unknown_device=unknown_device,
        face_mismatch=face_mismatch,
        min_confidence_score=min_confidence_score,
        max_confidence_score=max_confidence_score,
        page=page,
        limit=limit,
    )
    total_pages = math.ceil(total / limit) if limit > 0 else 0
    return SuccessResponse(
        data=items,
        meta={"page": page, "limit": limit, "total": total, "total_pages": total_pages},
    )


@fraud_router.get(
    "/records/{fraud_id}",
    response_model=SuccessResponse[FraudRecordDetailData],
)
def get_fraud_record(
    fraud_id: int,
    account: HROrAdminAccount,
    db: DbSession,
):
    result = fraud_service.get_fraud_record_detail(db=db, fraud_id=fraud_id)
    return SuccessResponse(data=result)

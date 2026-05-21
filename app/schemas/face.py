from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FaceStatusData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: int
    face_registered: bool
    face_object_key: str | None
    registered_at: datetime | None


class RegisterFaceData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: int
    face_registered: bool
    face_object_key: str
    registered_at: datetime


class DeleteFaceData(BaseModel):
    employee_id: int
    face_removed: bool


class VerifyFaceData(BaseModel):
    face_match_score: float
    liveness_score: float
    face_matched: bool
    liveness_passed: bool

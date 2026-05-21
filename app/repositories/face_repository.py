from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.business import FaceReference


def get_face_reference(db: Session, employee_id: int) -> FaceReference | None:
    return db.query(FaceReference).filter(FaceReference.employee_id == employee_id).first()


def upsert_face_reference(db: Session, employee_id: int, face_object_key: str) -> FaceReference:
    ref = get_face_reference(db, employee_id)
    if ref is None:
        ref = FaceReference(employee_id=employee_id, face_object_key=face_object_key)
        db.add(ref)
    else:
        ref.face_object_key = face_object_key
        ref.registered_at = datetime.now(tz=timezone.utc)
    db.commit()
    db.refresh(ref)
    return ref


def delete_face_reference(db: Session, employee_id: int) -> None:
    ref = get_face_reference(db, employee_id)
    if ref is not None:
        db.delete(ref)
        db.commit()

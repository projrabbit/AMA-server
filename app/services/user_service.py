from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User
from app.repositories.user_repository import create_user as create_user_record
from app.repositories.user_repository import get_user_by_email
from app.schemas.user import UserCreate


def create_user(db: Session, user_in: UserCreate) -> User:
    existing_user = get_user_by_email(db, email=str(user_in.email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    return create_user_record(
        db,
        user_in=user_in,
        hashed_password=get_password_hash(user_in.password),
    )

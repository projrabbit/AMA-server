from fastapi import APIRouter, status

from app.api.dependencies import CurrentUser, DbSession
from app.models.user import User
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import create_user


router = APIRouter()


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: DbSession) -> User:
    return create_user(db, user_in=user_in)


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: CurrentUser) -> User:
    return current_user

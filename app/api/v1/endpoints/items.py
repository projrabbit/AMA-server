from fastapi import APIRouter, status

from app.api.dependencies import CurrentUser, DbSession
from app.models.item import Item
from app.repositories.item_repository import create_item, list_user_items
from app.schemas.item import ItemCreate, ItemRead


router = APIRouter()


@router.get("/", response_model=list[ItemRead])
def read_items(
    db: DbSession,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> list[Item]:
    return list_user_items(db, owner_id=current_user.id, skip=skip, limit=limit)


@router.post("/", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def add_item(
    item_in: ItemCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> Item:
    return create_item(db, item_in=item_in, owner_id=current_user.id)

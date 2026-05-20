from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.item import Item
from app.schemas.item import ItemCreate


def list_user_items(
    db: Session,
    owner_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[Item]:
    statement = select(Item).where(Item.owner_id == owner_id).offset(skip).limit(limit)
    return list(db.scalars(statement).all())


def create_item(db: Session, item_in: ItemCreate, owner_id: int) -> Item:
    item = Item(**item_in.model_dump(), owner_id=owner_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

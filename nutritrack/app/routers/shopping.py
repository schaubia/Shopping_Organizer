from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.models import ShoppingList, ShoppingItem, User
from app.schemas.schemas import (
    ShoppingListCreate, ShoppingListOut,
    ShoppingItemCreate, ShoppingItemUpdate, ShoppingItemOut,
)
from app.services.auth import get_current_user

router = APIRouter()


# ── Lists ─────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[ShoppingListOut])
def get_lists(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(ShoppingList).filter(ShoppingList.user_id == user.id).all()


@router.post("/", response_model=ShoppingListOut, status_code=201)
def create_list(
    payload: ShoppingListCreate,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    lst = ShoppingList(user_id=user.id, name=payload.name)
    db.add(lst)
    db.commit()
    db.refresh(lst)
    return lst


@router.delete("/{list_id}", status_code=204)
def delete_list(list_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    lst = _get_list_or_404(list_id, user.id, db)
    db.delete(lst)
    db.commit()


# ── Items ─────────────────────────────────────────────────────────────────────

@router.post("/{list_id}/items", response_model=ShoppingItemOut, status_code=201)
def add_item(
    list_id: int,
    payload: ShoppingItemCreate,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    _get_list_or_404(list_id, user.id, db)
    item = ShoppingItem(shopping_list_id=list_id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/{list_id}/items/bulk", response_model=List[ShoppingItemOut], status_code=201)
def add_items_bulk(
    list_id: int,
    payloads: List[ShoppingItemCreate],
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """Add multiple items at once — used when importing ingredients from a scan."""
    _get_list_or_404(list_id, user.id, db)
    items = [ShoppingItem(shopping_list_id=list_id, **p.model_dump()) for p in payloads]
    db.add_all(items)
    db.commit()
    for item in items:
        db.refresh(item)
    return items


@router.patch("/{list_id}/items/{item_id}", response_model=ShoppingItemOut)
def update_item(
    list_id: int,
    item_id: int,
    payload: ShoppingItemUpdate,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    _get_list_or_404(list_id, user.id, db)
    item = db.query(ShoppingItem).filter(
        ShoppingItem.id == item_id,
        ShoppingItem.shopping_list_id == list_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{list_id}/items/{item_id}", status_code=204)
def delete_item(
    list_id: int,
    item_id: int,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    _get_list_or_404(list_id, user.id, db)
    item = db.query(ShoppingItem).filter(
        ShoppingItem.id == item_id,
        ShoppingItem.shopping_list_id == list_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()


# ── Helper ────────────────────────────────────────────────────────────────────

def _get_list_or_404(list_id: int, user_id: int, db: Session) -> ShoppingList:
    lst = db.query(ShoppingList).filter(
        ShoppingList.id == list_id,
        ShoppingList.user_id == user_id,
    ).first()
    if not lst:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    return lst

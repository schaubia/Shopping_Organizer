from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import datetime


# ── Auth ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email:     EmailStr
    password:  str
    full_name: Optional[str] = None

class UserOut(BaseModel):
    id:         int
    email:      str
    full_name:  Optional[str]
    plan:       str
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type:   str = "bearer"


# ── Food recognition ─────────────────────────────────────────────────────────

class AllergenOut(BaseModel):
    allergen: str
    severity: str   # high | medium | low

class PredictOut(BaseModel):
    food_name:    str
    confidence:   float
    model_used:   str
    health_score: Optional[float]
    nutrients:    dict
    allergens:    List[AllergenOut]
    ingredients:  List[str]


# ── Ingredients ──────────────────────────────────────────────────────────────

class IngredientsOut(BaseModel):
    food_name:   str
    ingredients: List[str]


# ── Shopping list ─────────────────────────────────────────────────────────────

class ShoppingItemCreate(BaseModel):
    name:            str
    quantity:        float         = 1.0
    unit:            str           = "pcs"
    category:        str           = "other"
    estimated_price: Optional[float] = None
    notes:           Optional[str]  = None
    source_food:     Optional[str]  = None

class ShoppingItemUpdate(BaseModel):
    name:            Optional[str]   = None
    quantity:        Optional[float] = None
    unit:            Optional[str]   = None
    category:        Optional[str]   = None
    estimated_price: Optional[float] = None
    actual_price:    Optional[float] = None
    is_checked:      Optional[bool]  = None
    notes:           Optional[str]   = None

class ShoppingItemOut(BaseModel):
    id:              int
    name:            str
    quantity:        float
    unit:            str
    category:        str
    estimated_price: Optional[float]
    actual_price:    Optional[float]
    is_checked:      bool
    notes:           Optional[str]
    source_food:     Optional[str]
    class Config:
        from_attributes = True

class ShoppingListCreate(BaseModel):
    name: str = "My List"

class ShoppingListOut(BaseModel):
    id:         int
    name:       str
    created_at: datetime
    items:      List[ShoppingItemOut] = []
    class Config:
        from_attributes = True


# ── Spending ──────────────────────────────────────────────────────────────────

class SpendingItemIn(BaseModel):
    name:  str
    qty:   float = 1.0
    price: float

class SpendingLogCreate(BaseModel):
    store_name:   Optional[str]  = None
    total_spent:  float
    currency:     str            = "BGN"
    items:        List[SpendingItemIn] = []
    receipt_note: Optional[str]  = None

class SpendingLogOut(BaseModel):
    id:          int
    store_name:  Optional[str]
    total_spent: float
    currency:    str
    items:       Any
    bought_at:   datetime
    class Config:
        from_attributes = True

class SpendingSummary(BaseModel):
    total_spent:       float
    average_per_trip:  float
    num_trips:         int
    top_categories:    List[dict]
    currency:          str

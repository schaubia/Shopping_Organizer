from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    email         = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name     = Column(String, nullable=True)
    is_active     = Column(Boolean, default=True)
    plan          = Column(String, default="free")   # free | personal | family
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    shopping_lists = relationship("ShoppingList", back_populates="owner")
    spending_logs  = relationship("SpendingLog",  back_populates="owner")
    food_scans     = relationship("FoodScan",     back_populates="owner")


class FoodScan(Base):
    """Every image scan result — for history and personalisation."""
    __tablename__ = "food_scans"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=True)
    food_name    = Column(String, nullable=False)
    confidence   = Column(Float)
    health_score = Column(Float)
    nutrients    = Column(JSON)      # raw USDA nutrient dict
    allergens    = Column(JSON)      # list of detected allergens
    model_used   = Column(String)    # "vit" | "resnet" | "both"
    scanned_at   = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="food_scans")


class ShoppingList(Base):
    __tablename__ = "shopping_lists"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    name       = Column(String, default="My List")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User",         back_populates="shopping_lists")
    items = relationship("ShoppingItem", back_populates="shopping_list", cascade="all, delete-orphan")


class ShoppingItem(Base):
    __tablename__ = "shopping_items"

    id               = Column(Integer, primary_key=True, index=True)
    shopping_list_id = Column(Integer, ForeignKey("shopping_lists.id"), nullable=False)
    name             = Column(String, nullable=False)
    quantity         = Column(Float, default=1.0)
    unit             = Column(String, default="pcs")     # pcs | g | kg | ml | l
    category         = Column(String, default="other")   # produce | dairy | meat | grains | other
    estimated_price  = Column(Float, nullable=True)      # user-entered or suggested
    actual_price     = Column(Float, nullable=True)      # filled in after purchase
    is_checked       = Column(Boolean, default=False)
    notes            = Column(Text, nullable=True)
    source_food      = Column(String, nullable=True)     # which scanned food suggested this item

    shopping_list = relationship("ShoppingList", back_populates="items")


class SpendingLog(Base):
    """One entry per shopping trip."""
    __tablename__ = "spending_logs"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    store_name   = Column(String, nullable=True)
    total_spent  = Column(Float, nullable=False)
    currency     = Column(String, default="BGN")
    items        = Column(JSON)       # snapshot of items bought [{name, qty, price}]
    receipt_note = Column(Text, nullable=True)
    bought_at    = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="spending_logs")

from fastapi import APIRouter
from app.schemas.schemas import IngredientsOut
from app.services.food_recognition import INGREDIENT_DB, _get_ingredients

router = APIRouter()


@router.get("/{food_name}", response_model=IngredientsOut)
def get_ingredients(food_name: str):
    """
    Return ingredient list for a food name.
    Used to auto-populate a shopping list after a scan.
    """
    ingredients = _get_ingredients(food_name)
    return {"food_name": food_name, "ingredients": ingredients}


@router.get("/", response_model=list)
def list_known_foods():
    """List all foods that have a known ingredient profile."""
    return sorted(INGREDIENT_DB.keys())

import io
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from PIL import Image

from app.schemas.schemas import PredictOut
from app.services.food_recognition import predict_food
from app.services.auth import get_optional_user
from app.models.models import User, FoodScan
from app.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/", response_model=PredictOut)
async def predict(
    file: UploadFile = File(...),
    db:   Session    = Depends(get_db),
    user: User       = Depends(get_optional_user),
):
    """
    Upload a food image — returns food name, health score, nutrients, allergens and ingredients.
    Works without authentication (guest mode); logged-in users get scan history saved.
    """
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=415, detail="Only JPEG / PNG / WebP images are accepted.")

    contents = await file.read()
    try:
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=422, detail="Could not read image file.")

    result = predict_food(image)

    # Persist scan for authenticated users
    if user:
        scan = FoodScan(
            user_id      = user.id,
            food_name    = result["food_name"],
            confidence   = result["confidence"],
            health_score = result["health_score"],
            nutrients    = result["nutrients"],
            allergens    = result["allergens"],
            model_used   = result["model_used"],
        )
        db.add(scan)
        db.commit()

    return result


@router.get("/history")
def scan_history(
    db:   Session = Depends(get_db),
    user: User    = Depends(__import__("app.services.auth", fromlist=["get_current_user"]).get_current_user),
):
    """Return last 50 food scans for the authenticated user."""
    scans = (
        db.query(FoodScan)
        .filter(FoodScan.user_id == user.id)
        .order_by(FoodScan.scanned_at.desc())
        .limit(50)
        .all()
    )
    return scans

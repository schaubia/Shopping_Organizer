from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from collections import defaultdict

from app.database import get_db
from app.models.models import SpendingLog, User
from app.schemas.schemas import SpendingLogCreate, SpendingLogOut, SpendingSummary
from app.services.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[SpendingLogOut])
def get_logs(
    limit: int    = 50,
    db:    Session = Depends(get_db),
    user:  User    = Depends(get_current_user),
):
    return (
        db.query(SpendingLog)
        .filter(SpendingLog.user_id == user.id)
        .order_by(SpendingLog.bought_at.desc())
        .limit(limit)
        .all()
    )


@router.post("/", response_model=SpendingLogOut, status_code=201)
def log_spending(
    payload: SpendingLogCreate,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    log = SpendingLog(
        user_id      = user.id,
        store_name   = payload.store_name,
        total_spent  = payload.total_spent,
        currency     = payload.currency,
        items        = [i.model_dump() for i in payload.items],
        receipt_note = payload.receipt_note,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/summary", response_model=SpendingSummary)
def spending_summary(
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """
    Aggregated stats: total spend, average per trip, top categories.
    This powers the spending optimisation dashboard.
    """
    logs = db.query(SpendingLog).filter(SpendingLog.user_id == user.id).all()
    if not logs:
        return SpendingSummary(
            total_spent=0, average_per_trip=0,
            num_trips=0, top_categories=[], currency="BGN"
        )

    total  = sum(l.total_spent for l in logs)
    avg    = total / len(logs)
    currency = logs[0].currency

    # Aggregate item spend by name across all trips
    item_totals: dict[str, float] = defaultdict(float)
    for log in logs:
        for item in (log.items or []):
            item_totals[item.get("name", "other")] += item.get("price", 0) * item.get("qty", 1)

    top_categories = sorted(
        [{"name": k, "total": round(v, 2)} for k, v in item_totals.items()],
        key=lambda x: x["total"],
        reverse=True,
    )[:10]

    return SpendingSummary(
        total_spent      = round(total, 2),
        average_per_trip = round(avg, 2),
        num_trips        = len(logs),
        top_categories   = top_categories,
        currency         = currency,
    )

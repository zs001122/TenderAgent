from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db.session import get_session
from app.services.feedback_learner import FeedbackLearner

router = APIRouter()


class BidFeedbackRequest(BaseModel):
    tender_id: int
    bid_date: Optional[datetime] = None
    bid_price: float = 0.0
    score: float = 0.0
    recommendation: str = ""
    grade: str = "D"


class BidResultUpdateRequest(BaseModel):
    is_won: bool
    win_date: Optional[datetime] = None
    lose_reason: Optional[str] = None
    notes: Optional[str] = None


@router.post("/bid", response_model=Dict[str, Any])
def record_bid_feedback(
    request: BidFeedbackRequest,
    session=Depends(get_session),
):
    learner = FeedbackLearner(session)
    record = learner.record_bid(
        tender_id=request.tender_id,
        bid_info={
            "bid_date": request.bid_date or datetime.now(),
            "bid_price": request.bid_price,
        },
        prediction={
            "score": request.score,
            "recommendation": request.recommendation,
            "grade": request.grade,
        },
    )
    return {
        "id": record.id,
        "tender_id": record.tender_id,
        "actual_result": record.actual_result,
    }


@router.put("/result/{record_id}", response_model=Dict[str, Any])
def update_bid_result(
    record_id: int,
    request: BidResultUpdateRequest,
    session=Depends(get_session),
):
    learner = FeedbackLearner(session)
    record = learner.record_result(
        record_id=record_id,
        result={
            "is_won": request.is_won,
            "win_date": request.win_date,
            "lose_reason": request.lose_reason,
            "notes": request.notes,
        },
    )
    if not record:
        raise HTTPException(status_code=404, detail="投标记录不存在")
    return {
        "id": record.id,
        "tender_id": record.tender_id,
        "actual_result": record.actual_result,
        "is_won": record.is_won,
    }


@router.get("/stats", response_model=Dict[str, Any])
def get_feedback_stats(session=Depends(get_session)):
    learner = FeedbackLearner(session)
    return learner.get_accuracy_stats()


@router.get("/records", response_model=Dict[str, List[Dict[str, Any]]])
def get_recent_feedback_records(
    limit: int = 10,
    session=Depends(get_session),
):
    learner = FeedbackLearner(session)
    records = learner.get_recent_records(limit=max(limit, 1))
    return {
        "items": [
            {
                "id": item.id,
                "tender_id": item.tender_id,
                "bid_date": item.bid_date.isoformat() if item.bid_date else None,
                "bid_price": item.bid_price,
                "predicted_score": item.predicted_score,
                "predicted_recommendation": item.predicted_recommendation,
                "actual_result": item.actual_result,
                "is_won": item.is_won,
                "lose_reason": item.lose_reason,
            }
            for item in records
        ]
    }

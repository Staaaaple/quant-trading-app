"""用户反馈收集 API."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.models.user_feedback import UserFeedback

router = APIRouter()


class FeedbackCreate(BaseModel):
    portfolio_id: Optional[int] = None
    strategy_id: Optional[str] = None
    feedback_type: str = "general"
    overall_rating: Optional[int] = None
    return_rating: Optional[int] = None
    risk_rating: Optional[int] = None
    usability_rating: Optional[int] = None
    actual_return_pct: Optional[float] = None
    period_days: Optional[int] = None
    pros: Optional[str] = None
    cons: Optional[str] = None
    suggestion: Optional[str] = None
    willing_to_interview: int = 0


@router.post("", response_model=dict)
def create_feedback(
    payload: FeedbackCreate,
    user_id: int,
    db: Session = Depends(get_db),
):
    """提交用户反馈."""
    feedback = UserFeedback(
        user_id=user_id,
        portfolio_id=payload.portfolio_id,
        strategy_id=payload.strategy_id,
        feedback_type=payload.feedback_type,
        overall_rating=payload.overall_rating,
        return_rating=payload.return_rating,
        risk_rating=payload.risk_rating,
        usability_rating=payload.usability_rating,
        actual_return_pct=payload.actual_return_pct,
        period_days=payload.period_days,
        pros=payload.pros,
        cons=payload.cons,
        suggestion=payload.suggestion,
        willing_to_interview=payload.willing_to_interview,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return {"id": feedback.id, "message": "反馈提交成功"}


@router.get("/summary", response_model=dict)
def get_feedback_summary(db: Session = Depends(get_db)):
    """获取反馈汇总统计."""
    total = db.query(UserFeedback).count()
    avg_overall = db.query(UserFeedback.overall_rating).filter(
        UserFeedback.overall_rating.isnot(None)
    ).scalar()

    from sqlalchemy import func
    avg = db.query(func.avg(UserFeedback.overall_rating)).filter(
        UserFeedback.overall_rating.isnot(None)
    ).scalar()

    return {
        "total_feedbacks": total,
        "avg_overall_rating": round(avg, 2) if avg else None,
        "breakdown": {
            "general": db.query(UserFeedback).filter(UserFeedback.feedback_type == "general").count(),
            "strategy": db.query(UserFeedback).filter(UserFeedback.feedback_type == "strategy").count(),
            "portfolio": db.query(UserFeedback).filter(UserFeedback.feedback_type == "portfolio").count(),
            "service": db.query(UserFeedback).filter(UserFeedback.feedback_type == "service").count(),
        },
    }

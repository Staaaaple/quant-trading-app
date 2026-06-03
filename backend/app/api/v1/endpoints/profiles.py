from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any

from app.db.session import get_db
from app.models.investor_profile import InvestorProfile
from app.schemas.investor_profile import (
    InvestorProfileCreate,
    InvestorProfileRead,
    InvestorProfileVector,
)
from app.services import profile_service

router = APIRouter()


@router.post("", response_model=InvestorProfileRead)
def create_profile(payload: InvestorProfileCreate, db: Session = Depends(get_db)):
    """创建投资者画像（自动计算15维向量）."""
    profile = profile_service.create_profile(
        db=db,
        user_id=payload.user_id,
        answers=payload.answers_json,
    )
    return profile


@router.get("/questions")
def get_questions():
    """获取问卷题目定义（前端用）."""
    return profile_service.QUESTIONS


@router.post("/preview")
def preview_profile_vector(answers: dict[str, Any]):
    """预览画像向量（不保存）."""
    vector = profile_service.compute_profile_vector(answers)
    labels = profile_service.derive_labels(vector)
    return {
        "vector": vector,
        "labels": labels,
    }


@router.get("/user/{user_id}", response_model=InvestorProfileRead | None)
def get_profile_by_user(user_id: int, db: Session = Depends(get_db)):
    """获取用户最新画像."""
    return profile_service.get_profile_by_user(db, user_id)


@router.put("/{profile_id}", response_model=InvestorProfileRead)
def update_profile(
    profile_id: int,
    payload: InvestorProfileCreate,
    db: Session = Depends(get_db),
):
    """更新画像（重新计算向量）."""
    profile = profile_service.update_profile(
        db=db,
        profile_id=profile_id,
        answers=payload.answers_json,
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.delete("/{profile_id}")
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(InvestorProfile).filter(InvestorProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile.is_active = False
    db.commit()
    return {"ok": True}

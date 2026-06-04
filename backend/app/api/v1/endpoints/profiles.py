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
from app.api.deps import get_current_user_id, require_user_id

router = APIRouter()


@router.post("", response_model=InvestorProfileRead)
def create_profile(
    payload: InvestorProfileCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
):
    """创建投资者画像（自动计算15维向量）."""
    # 使用 header 中的 user_id 覆盖 payload 中的（确保隔离）
    profile = profile_service.create_profile(
        db=db,
        user_id=user_id,
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


@router.get("/me", response_model=InvestorProfileRead | None)
def get_my_profile(
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
):
    """获取当前用户的最新画像."""
    return profile_service.get_profile_by_user(db, user_id)


@router.get("/user/{target_user_id}", response_model=InvestorProfileRead | None)
def get_profile_by_user(
    target_user_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
):
    """获取指定用户的画像（只能查看自己的）."""
    if target_user_id != user_id:
        raise HTTPException(status_code=403, detail="Can only access your own profile")
    return profile_service.get_profile_by_user(db, user_id)


@router.put("/{profile_id}", response_model=InvestorProfileRead)
def update_profile(
    profile_id: int,
    payload: InvestorProfileCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
):
    """更新画像（重新计算向量）."""
    # 先验证这个 profile 属于当前用户
    existing = db.query(InvestorProfile).filter(
        InvestorProfile.id == profile_id,
        InvestorProfile.user_id == user_id,
        InvestorProfile.is_active == True,
    ).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile = profile_service.update_profile(
        db=db,
        profile_id=profile_id,
        answers=payload.answers_json,
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.delete("/{profile_id}")
def delete_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
):
    profile = db.query(InvestorProfile).filter(
        InvestorProfile.id == profile_id,
        InvestorProfile.user_id == user_id,
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile.is_active = False
    db.commit()
    return {"ok": True}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_user_id
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.demo_user_service import ensure_demo_user, is_demo_user, reset_demo_user_data

router = APIRouter()


@router.post("", response_model=UserRead)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = User(name=payload.name, avatar_url=payload.avatar_url)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("", response_model=list[UserRead])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # 自动保证演示用户存在
    ensure_demo_user(db)
    return db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserRead)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.name is not None:
        user.name = payload.name
    if payload.avatar_url is not None:
        user.avatar_url = payload.avatar_url
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_demo:
        raise HTTPException(status_code=403, detail="Cannot delete demo user")
    user.is_active = False
    db.commit()
    return {"ok": True}


@router.post("/demo/reset")
def reset_demo_user(
    db: Session = Depends(get_db),
    user_id: int = Depends(require_user_id),
):
    """重置演示用户业务数据. 仅允许演示用户调用."""
    if not is_demo_user(db, user_id):
        raise HTTPException(status_code=403, detail="Only demo user can be reset")
    try:
        result = reset_demo_user_data(db, user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

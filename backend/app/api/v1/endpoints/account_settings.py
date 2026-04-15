from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.account_settings import AccountSettingsRead, AccountSettingsCreate
from app.services import account_settings_service

router = APIRouter()


@router.get("", response_model=AccountSettingsRead)
def get_settings(
    *,
    db: Session = Depends(get_db),
):
    return account_settings_service.get_or_create_settings(db)


@router.put("", response_model=AccountSettingsRead)
def update_settings(
    *,
    db: Session = Depends(get_db),
    obj_in: AccountSettingsCreate,
):
    return account_settings_service.update_settings(db, obj_in)

from sqlalchemy.orm import Session

from app.models.account_settings import AccountSettings
from app.schemas.account_settings import AccountSettingsCreate


def get_or_create_settings(db: Session) -> AccountSettings:
    settings = db.query(AccountSettings).first()
    if not settings:
        settings = AccountSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def update_settings(db: Session, obj_in: AccountSettingsCreate) -> AccountSettings:
    settings = get_or_create_settings(db)
    settings.commission_rate = obj_in.commission_rate
    settings.min_commission = obj_in.min_commission
    settings.stamp_tax_rate = obj_in.stamp_tax_rate
    settings.transfer_fee_rate = obj_in.transfer_fee_rate
    settings.is_sh_market = obj_in.is_sh_market
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Any


class InvestorProfileBase(BaseModel):
    user_id: int
    answers_json: dict[str, Any]


class InvestorProfileCreate(InvestorProfileBase):
    pass


class InvestorProfileUpdate(BaseModel):
    answers_json: dict[str, Any] | None = None


class InvestorProfileVector(BaseModel):
    risk_tolerance: float
    loss_aversion: float
    herding_tendency: float
    overconfidence: float
    delayed_gratification: float
    security_need: float
    time_horizon_score: float
    experience_level: float
    capital_tier: float
    income_stability: float
    debt_pressure: float
    information_processing: float
    social_pressure: float
    emergency_response: float
    anchoring_effect: float


class InvestorProfileRead(InvestorProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    risk_tolerance: float
    loss_aversion: float
    herding_tendency: float
    overconfidence: float
    delayed_gratification: float
    security_need: float
    time_horizon_score: float
    experience_level: float
    capital_tier: float
    income_stability: float
    debt_pressure: float
    information_processing: float
    social_pressure: float
    emergency_response: float
    anchoring_effect: float
    risk_label: str | None = None
    time_horizon_label: str | None = None
    experience_label: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

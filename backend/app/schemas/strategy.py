from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Any


# ── Pipeline Stage Schemas ──

class IndicatorDef(BaseModel):
    name: str
    type: str = Field(..., pattern=r"^(MA|EMA|RSI|MACD|KDJ|BOLL|PRICE|VOLUME)$")
    period: int = 5
    field: str = "close"


class RiskCheck(BaseModel):
    type: str = Field(..., pattern=r"^(max_drawdown|max_position)$")
    threshold: float
    action: str = Field("block_buy", pattern=r"^(block_buy|block_all|warn)$")


class ConditionOperand(BaseModel):
    indicator: str | None = None
    value: float | None = None


class Condition(BaseModel):
    left: ConditionOperand
    op: str = Field(..., pattern=r"^(cross_up|cross_down|gt|gte|lt|lte|eq)$")
    right: ConditionOperand


class SignalGroup(BaseModel):
    id: str
    direction: str = Field(..., pattern=r"^(buy|sell)$")
    logic: str = Field("AND", pattern=r"^(AND|OR)$")
    conditions: list[Condition]


class ActionRule(BaseModel):
    signal_group: str
    action: str = Field("order_target_percent", pattern=r"^order_target_percent$")
    weight: float


class StageConfig(BaseModel):
    history_depth: int = 30
    max_position_pct: float = 0.95
    indicators: list[IndicatorDef] | None = None
    checks: list[RiskCheck] | None = None
    groups: list[SignalGroup] | None = None
    rules: list[ActionRule] | None = None


class PipelineStage(BaseModel):
    id: str
    type: str = Field(..., pattern=r"^(init|indicator|risk|signal|action)$")
    config: StageConfig


class PipelineConfig(BaseModel):
    version: str = "1.0"
    stages: list[PipelineStage]


# ── Strategy Schemas ──

class StrategyBase(BaseModel):
    strategy_id: str
    name: str
    type: str = "trade"
    description: str | None = None


class StrategyCreate(StrategyBase):
    code: str | None = None
    pipeline_config: PipelineConfig | dict[str, Any] | None = None


class StrategyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    code: str | None = None
    pipeline_config: PipelineConfig | dict[str, Any] | None = None


class StrategyRead(StrategyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    pipeline_config: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class CodePreviewPayload(BaseModel):
    pipeline_config: PipelineConfig | dict[str, Any]


class CodePreviewResponse(BaseModel):
    code: str

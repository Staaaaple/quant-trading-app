"""策略模板库 — 经典技术指标家族.

所有模板遵循统一接口:
  run(symbol: str, df: pd.DataFrame, params: dict) -> list[dict]

返回信号格式:
  {
    "symbol": str,
    "date": str,
    "signal": int,       # -1(卖出) / 0(持有) / 1(买入)
    "confidence": float, # 0-1
    "expected_return": float,
    "risk_estimate": float,
  }
"""

from .technical_indicators import (
    tmpl_ma_crossover,
    tmpl_rsi_reversal,
    tmpl_boll_breakout,
    tmpl_macd_divergence,
    tmpl_volume_price,
)

__all__ = [
    "tmpl_ma_crossover",
    "tmpl_rsi_reversal",
    "tmpl_boll_breakout",
    "tmpl_macd_divergence",
    "tmpl_volume_price",
]

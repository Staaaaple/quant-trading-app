#!/usr/bin/env python3
"""Seed script: import preset strategies into the database.

Usage:
    cd backend && python seed_strategies.py

This script reads strategy code from seed_strategies/ directory and creates
Strategy + StrategyDNA records in the database.
"""

import os
import sys

# Ensure app is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.strategy import Strategy
from app.services.strategy_service import create_strategy
from app.schemas.strategy import StrategyCreate

SEED_DIR = os.path.join(os.path.dirname(__file__), "app", "seed_strategies")

PRESET_STRATEGIES = [
    # ===== Trend Following Family =====
    {
        "strategy_id": "preset_dual_ma",
        "name": "双均线突破策略",
        "type": "trade",
        "description": "MA5上穿MA20金叉买入，MA5下穿MA20死叉卖出。最经典的趋势跟踪策略。",
        "family": "趋势跟踪家族",
        "source_file": "trend_following.py",
        "class_name": "DualMACrossover",
    },
    {
        "strategy_id": "preset_triple_ma",
        "name": "三均线多头排列",
        "type": "trade",
        "description": "MA5 > MA20 > MA60 且价格 > MA5 时满仓。更强的趋势确认，过滤更多震荡噪音。",
        "family": "趋势跟踪家族",
        "source_file": "trend_following.py",
        "class_name": "TripleMATrend",
    },
    {
        "strategy_id": "preset_macd_trend",
        "name": "MACD趋势策略",
        "type": "trade",
        "description": "MACD柱状线 > 0 且持续扩大时买入，< 0 时卖出。捕捉趋势启动和衰竭。",
        "family": "趋势跟踪家族",
        "source_file": "trend_following.py",
        "class_name": "MACDTrend",
    },
    {
        "strategy_id": "preset_momentum_breakout",
        "name": "动量突破策略",
        "type": "trade",
        "description": "价格突破20日高点买入，跌破10日低点卖出。强势趋势启动时介入。",
        "family": "趋势跟踪家族",
        "source_file": "trend_following.py",
        "class_name": "MomentumBreakout",
    },
    {
        "strategy_id": "preset_ema_channel",
        "name": "EMA通道跟踪",
        "type": "trade",
        "description": "价格在EMA20上方且EMA20 > EMA60时持多。平滑的趋势跟踪，减少频繁信号。",
        "family": "趋势跟踪家族",
        "source_file": "trend_following.py",
        "class_name": "EMAChannelTrend",
    },

    # ===== Momentum Family =====
    {
        "strategy_id": "preset_rsi_reversion",
        "name": "RSI超买超卖",
        "type": "trade",
        "description": "RSI < 30 超卖买入，RSI > 70 超买卖出。经典的均值回归策略。",
        "family": "动量家族",
        "source_file": "momentum.py",
        "class_name": "RSIMeanReversion",
    },
    {
        "strategy_id": "preset_kdj_crossover",
        "name": "KDJ金叉死叉",
        "type": "trade",
        "description": "K线上穿D线(金叉)买入，K线下穿D线(死叉)卖出。中短线波段操作。",
        "family": "动量家族",
        "source_file": "momentum.py",
        "class_name": "KDJCrossover",
    },
    {
        "strategy_id": "preset_volume_price",
        "name": "量价齐升策略",
        "type": "trade",
        "description": "价格上涨 + 成交量放大(超过20日均量1.5倍)时买入。捕捉资金流入的启动点。",
        "family": "动量家族",
        "source_file": "momentum.py",
        "class_name": "VolumePriceSurge",
    },
    {
        "strategy_id": "preset_momentum_20d",
        "name": "20日动量策略",
        "type": "trade",
        "description": "过去20日涨幅排名前10%买入，排名掉到后50%卖出。强者恒强。",
        "family": "动量家族",
        "source_file": "momentum.py",
        "class_name": "Momentum20D",
    },

    # ===== Mean Reversion Family =====
    {
        "strategy_id": "preset_boll_reversion",
        "name": "布林带回归策略",
        "type": "trade",
        "description": "价格跌破下轨买入，触及上轨卖出。区间震荡市场的经典策略。",
        "family": "均值回归家族",
        "source_file": "mean_reversion.py",
        "class_name": "BollingerReversion",
    },
    {
        "strategy_id": "preset_rsi_bounce",
        "name": "RSI超卖反弹",
        "type": "trade",
        "description": "RSI < 20 且连续2日超卖时买入，RSI > 60 卖出。急跌后的反弹机会。",
        "family": "均值回归家族",
        "source_file": "mean_reversion.py",
        "class_name": "RSIOversoldBounce",
    },
    {
        "strategy_id": "preset_boll_rsi_combo",
        "name": "布林带+RSI组合",
        "type": "trade",
        "description": "价格跌破布林带下轨且RSI < 30时买入。双重确认，高胜率但信号较少。",
        "family": "均值回归家族",
        "source_file": "mean_reversion.py",
        "class_name": "BollRSICombo",
    },
    {
        "strategy_id": "preset_low_volatility",
        "name": "低波动率策略",
        "type": "trade",
        "description": "20日波动率处于近120日最低20%分位时买入。波动率压缩后的突破。",
        "family": "均值回归家族",
        "source_file": "mean_reversion.py",
        "class_name": "LowVolatility",
    },

    # ===== Multi-Factor Family =====
    {
        "strategy_id": "preset_pe_pb_value",
        "name": "PE/PB估值策略",
        "type": "trade",
        "description": "低估值选股。PE < 15 且 PB < 2 时买入。价值投资风格。",
        "family": "多因子家族",
        "source_file": "multi_factor.py",
        "class_name": "PEPBValue",
    },
    {
        "strategy_id": "preset_roe_growth",
        "name": "ROE+营收增长",
        "type": "trade",
        "description": "ROE > 15% 且营收增长 > 20% 时买入。优质成长股策略。",
        "family": "多因子家族",
        "source_file": "multi_factor.py",
        "class_name": "ROEGrowth",
    },
    {
        "strategy_id": "preset_small_cap_roe",
        "name": "小市值高ROE",
        "type": "trade",
        "description": "小市值(流通市值<100亿) + 高ROE(>12%)选股。小而美的公司。",
        "family": "多因子家族",
        "source_file": "multi_factor.py",
        "class_name": "SmallCapROE",
    },
    {
        "strategy_id": "preset_momentum_value",
        "name": "动量+价值双因子",
        "type": "trade",
        "description": "动量排名前30%且估值低于行业中位数时买入。价值+动量结合。",
        "family": "多因子家族",
        "source_file": "multi_factor.py",
        "class_name": "MomentumValue",
    },

    # ===== Risk-Enhanced Family =====
    {
        "strategy_id": "preset_atr_stop_ma",
        "name": "ATR止损双均线",
        "type": "trade",
        "description": "双均线信号 + ATR动态止损(2倍ATR)。趋势跟踪但控制单笔亏损。",
        "family": "风控增强家族",
        "source_file": "risk_enhanced.py",
        "class_name": "ATRStopDualMA",
    },
    {
        "strategy_id": "preset_position_sizing",
        "name": "仓位管理趋势",
        "type": "trade",
        "description": "趋势信号 + 波动率越大仓位越小。资金量较大时控制回撤。",
        "family": "风控增强家族",
        "source_file": "risk_enhanced.py",
        "class_name": "PositionSizingTrend",
    },
    {
        "strategy_id": "preset_dynamic_stop",
        "name": "动态止损均线",
        "type": "trade",
        "description": "价格在MA20上方持多，移动止损为MA20下方1个ATR。让利润奔跑。",
        "family": "风控增强家族",
        "source_file": "risk_enhanced.py",
        "class_name": "DynamicStopMA",
    },
]


def _extract_class_code(filepath: str, class_name: str) -> str:
    """Extract a specific class definition from a Python file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()
    start_idx = None
    indent = None
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(f"class {class_name}("):
            start_idx = i
            indent = len(line) - len(stripped)
            break

    if start_idx is None:
        raise ValueError(f"Class {class_name} not found in {filepath}")

    # Collect lines until next top-level definition or end of file
    result_lines = []
    for j in range(start_idx, len(lines)):
        line = lines[j]
        if j > start_idx:
            stripped = line.lstrip()
            if stripped and not line.startswith(" ") and not line.startswith("\t"):
                break
        result_lines.append(line)

    return "\n".join(result_lines)


def seed_strategies():
    db = SessionLocal()
    try:
        created = 0
        skipped = 0

        for preset in PRESET_STRATEGIES:
            # Check if already exists
            existing = db.query(Strategy).filter(
                Strategy.strategy_id == preset["strategy_id"]
            ).first()
            if existing:
                print(f"  SKIP: {preset['strategy_id']} already exists")
                skipped += 1
                continue

            # Extract code from source file
            filepath = os.path.join(SEED_DIR, preset["source_file"])
            code = _extract_class_code(filepath, preset["class_name"])

            # Create strategy
            payload = StrategyCreate(
                strategy_id=preset["strategy_id"],
                name=preset["name"],
                code=code,
                type=preset["type"],
                description=preset["description"],
            )
            strategy = create_strategy(db, payload)
            print(f"  OK: {strategy.strategy_id} ({strategy.name})")
            created += 1

        print(f"\nDone. Created: {created}, Skipped: {skipped}, Total: {len(PRESET_STRATEGIES)}")

    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding preset strategies...")
    seed_strategies()

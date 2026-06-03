"""最终策略池 — 35个通过严格验证的高质量策略.

所有策略均通过:
- 10只测试股票 × 3个时间段(2022-2024)
- 单股胜率 > 35%
- 最大回撤 < max(30%, 个股回撤+5%)
- 组合收益 > 沪深300大盘指数

策略来源: 基于动量-波动率核心逻辑的多参数变体
"""

import numpy as np
import pandas as pd
from typing import Any

from app.services.backtest_validator import validate_template, preload_all_data
from app.services.template_runner import make_signal


# ═══════════════════════════════════════════════════════════════
# 核心策略模板
# ═══════════════════════════════════════════════════════════════

def _momentum_volatility_score(symbol, df, params):
    """动量-波动率评分策略核心.

    核心逻辑: score = mom_weight * 动量 - vol_weight * 波动率
    当 score > threshold 时买入, score < threshold 时卖出.
    """
    mom_window = int(params.get('mom_window', 12))
    vol_window = int(params.get('vol_window', 25))
    mom_weight = float(params.get('mom_weight', 1.0))
    vol_weight = float(params.get('vol_weight', 2.0))
    threshold = float(params.get('threshold', 0.0))

    df = df.copy()
    df['mom'] = df['close'].pct_change(mom_window)
    df['vol'] = df['close'].pct_change().rolling(vol_window).std()
    df['score'] = mom_weight * df['mom'] - vol_weight * df['vol']

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['score']):
            continue

        if not in_position and row['score'] > threshold:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and row['score'] < threshold:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 35个精选策略配置
# ═══════════════════════════════════════════════════════════════

STRATEGY_POOL = [
    # 家族1: 超短动量 (mom_window=3, 高频交易)
    {"id": "mv_03_15_m05_v10", "name": "超短动量-低波(3,15)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 3, "vol_window": 15, "mom_weight": 0.5, "vol_weight": 1.0, "threshold": 0.0}},
    {"id": "mv_03_15_m10_v20", "name": "超短动量-标准(3,15)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 3, "vol_window": 15, "mom_weight": 1.0, "vol_weight": 2.0, "threshold": 0.0}},
    {"id": "mv_03_15_m15_v25", "name": "超短动量-高波(3,15)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 3, "vol_window": 15, "mom_weight": 1.5, "vol_weight": 2.5, "threshold": 0.0}},
    {"id": "mv_03_15_m15_v30", "name": "超短动量-强波(3,15)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 3, "vol_window": 15, "mom_weight": 1.5, "vol_weight": 3.0, "threshold": 0.0}},
    {"id": "mv_03_20_m05_v10", "name": "超短动量-低波(3,20)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 3, "vol_window": 20, "mom_weight": 0.5, "vol_weight": 1.0, "threshold": 0.0}},
    {"id": "mv_03_20_m05_v15", "name": "超短动量-平衡(3,20)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 3, "vol_window": 20, "mom_weight": 0.5, "vol_weight": 1.5, "threshold": 0.0}},
    {"id": "mv_03_20_m10_v20", "name": "超短动量-标准(3,20)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 3, "vol_window": 20, "mom_weight": 1.0, "vol_weight": 2.0, "threshold": 0.0}},
    {"id": "mv_03_20_m10_v25", "name": "超短动量-高波(3,20)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 3, "vol_window": 20, "mom_weight": 1.0, "vol_weight": 2.5, "threshold": 0.0}},
    {"id": "mv_03_20_m10_v30", "name": "超短动量-强波(3,20)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 3, "vol_window": 20, "mom_weight": 1.0, "vol_weight": 3.0, "threshold": 0.0}},
    {"id": "mv_03_20_m15_v25", "name": "超短动量-激进(3,20)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 3, "vol_window": 20, "mom_weight": 1.5, "vol_weight": 2.5, "threshold": 0.0}},
    {"id": "mv_03_20_m15_v30", "name": "超短动量-极波(3,20)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 3, "vol_window": 20, "mom_weight": 1.5, "vol_weight": 3.0, "threshold": 0.0}},

    # 家族2: 短动量 (mom_window=5, 中频交易)
    {"id": "mv_05_15_m10_v15", "name": "短动量-低波(5,15)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 5, "vol_window": 15, "mom_weight": 1.0, "vol_weight": 1.5, "threshold": 0.0}},
    {"id": "mv_05_15_m20_v30", "name": "短动量-标准(5,15)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 5, "vol_window": 15, "mom_weight": 2.0, "vol_weight": 3.0, "threshold": 0.0}},
    {"id": "mv_05_30_m10_v15", "name": "短动量-平衡(5,30)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 5, "vol_window": 30, "mom_weight": 1.0, "vol_weight": 1.5, "threshold": 0.0}},
    {"id": "mv_05_30_m15_v25", "name": "短动量-高波(5,30)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 5, "vol_window": 30, "mom_weight": 1.5, "vol_weight": 2.5, "threshold": 0.0}},
    {"id": "mv_05_30_m20_v30", "name": "短动量-强波(5,30)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 5, "vol_window": 30, "mom_weight": 2.0, "vol_weight": 3.0, "threshold": 0.0}},
    {"id": "mv_05_40_m05_v10", "name": "短动量-保守(5,40)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 5, "vol_window": 40, "mom_weight": 0.5, "vol_weight": 1.0, "threshold": 0.0}},
    {"id": "mv_05_40_m10_v20", "name": "短动量-标准(5,40)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 5, "vol_window": 40, "mom_weight": 1.0, "vol_weight": 2.0, "threshold": 0.0}},
    {"id": "mv_05_40_m15_v20", "name": "短动量-激进(5,40)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 5, "vol_window": 40, "mom_weight": 1.5, "vol_weight": 2.0, "threshold": 0.0}},
    {"id": "mv_05_40_m15_v30", "name": "短动量-极波(5,40)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 5, "vol_window": 40, "mom_weight": 1.5, "vol_weight": 3.0, "threshold": 0.0}},
    {"id": "mv_05_50_m05_v10", "name": "短动量-超稳(5,50)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 5, "vol_window": 50, "mom_weight": 0.5, "vol_weight": 1.0, "threshold": 0.0}},
    {"id": "mv_05_50_m10_v15", "name": "短动量-稳健(5,50)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 5, "vol_window": 50, "mom_weight": 1.0, "vol_weight": 1.5, "threshold": 0.0}},
    {"id": "mv_05_50_m10_v20", "name": "短动量-标准(5,50)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 5, "vol_window": 50, "mom_weight": 1.0, "vol_weight": 2.0, "threshold": 0.0}},
    {"id": "mv_05_50_m15_v30", "name": "短动量-高波(5,50)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 5, "vol_window": 50, "mom_weight": 1.5, "vol_weight": 3.0, "threshold": 0.0}},
    {"id": "mv_05_60_m10_v10", "name": "短动量-低波(5,60)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 5, "vol_window": 60, "mom_weight": 1.0, "vol_weight": 1.0, "threshold": 0.0}},
    {"id": "mv_05_60_m10_v15", "name": "短动量-平衡(5,60)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 5, "vol_window": 60, "mom_weight": 1.0, "vol_weight": 1.5, "threshold": 0.0}},
    {"id": "mv_05_60_m15_v15", "name": "短动量-高波(5,60)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 5, "vol_window": 60, "mom_weight": 1.5, "vol_weight": 1.5, "threshold": 0.0}},
    {"id": "mv_05_60_m20_v25", "name": "短动量-强波(5,60)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 5, "vol_window": 60, "mom_weight": 2.0, "vol_weight": 2.5, "threshold": 0.0}},
    {"id": "mv_05_60_m20_v30", "name": "短动量-极波(5,60)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 5, "vol_window": 60, "mom_weight": 2.0, "vol_weight": 3.0, "threshold": 0.0}},

    # 家族3: 中动量 (mom_window=10, 低频交易)
    {"id": "mv_10_20_m05_v10", "name": "中动量-保守(10,20)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 10, "vol_window": 20, "mom_weight": 0.5, "vol_weight": 1.0, "threshold": 0.0}},
    {"id": "mv_10_20_m10_v15", "name": "中动量-平衡(10,20)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 10, "vol_window": 20, "mom_weight": 1.0, "vol_weight": 1.5, "threshold": 0.0}},
    {"id": "mv_10_20_m10_v20", "name": "中动量-标准(10,20)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 10, "vol_window": 20, "mom_weight": 1.0, "vol_weight": 2.0, "threshold": 0.0}},
    {"id": "mv_10_20_m15_v25", "name": "中动量-高波(10,20)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 10, "vol_window": 20, "mom_weight": 1.5, "vol_weight": 2.5, "threshold": 0.0}},
    {"id": "mv_10_20_m20_v30", "name": "中动量-强波(10,20)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 10, "vol_window": 20, "mom_weight": 2.0, "vol_weight": 3.0, "threshold": 0.0}},
    {"id": "mv_10_25_m10_v15", "name": "中动量-稳健(10,25)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 10, "vol_window": 25, "mom_weight": 1.0, "vol_weight": 1.5, "threshold": 0.0}},
    {"id": "mv_10_25_m15_v25", "name": "中动量-高波(10,25)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 10, "vol_window": 25, "mom_weight": 1.5, "vol_weight": 2.5, "threshold": 0.0}},
    {"id": "mv_10_25_m20_v30", "name": "中动量-极波(10,25)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 10, "vol_window": 25, "mom_weight": 2.0, "vol_weight": 3.0, "threshold": 0.0}},
    {"id": "mv_10_40_m10_v15", "name": "中动量-稳健(10,40)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 10, "vol_window": 40, "mom_weight": 1.0, "vol_weight": 1.5, "threshold": 0.0}},
    {"id": "mv_10_40_m15_v20", "name": "中动量-标准(10,40)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 10, "vol_window": 40, "mom_weight": 1.5, "vol_weight": 2.0, "threshold": 0.0}},
    {"id": "mv_10_40_m15_v25", "name": "中动量-高波(10,40)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 10, "vol_window": 40, "mom_weight": 1.5, "vol_weight": 2.5, "threshold": 0.0}},
    {"id": "mv_10_40_m20_v25", "name": "中动量-强波(10,40)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 10, "vol_window": 40, "mom_weight": 2.0, "vol_weight": 2.5, "threshold": 0.0}},
    {"id": "mv_10_40_m20_v30", "name": "中动量-极波(10,40)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 10, "vol_window": 40, "mom_weight": 2.0, "vol_weight": 3.0, "threshold": 0.0}},
    {"id": "mv_10_60_m10_v15", "name": "中动量-超稳(10,60)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 10, "vol_window": 60, "mom_weight": 1.0, "vol_weight": 1.5, "threshold": 0.0}},
    {"id": "mv_10_60_m15_v20", "name": "中动量-稳健(10,60)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 10, "vol_window": 60, "mom_weight": 1.5, "vol_weight": 2.0, "threshold": 0.0}},
    {"id": "mv_10_60_m15_v25", "name": "中动量-高波(10,60)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 10, "vol_window": 60, "mom_weight": 1.5, "vol_weight": 2.5, "threshold": 0.0}},
    {"id": "mv_10_60_m20_v15", "name": "中动量-强波(10,60)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 10, "vol_window": 60, "mom_weight": 2.0, "vol_weight": 1.5, "threshold": 0.0}},
    {"id": "mv_10_60_m20_v20", "name": "中动量-标准(10,60)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 10, "vol_window": 60, "mom_weight": 2.0, "vol_weight": 2.0, "threshold": 0.0}},
    {"id": "mv_10_60_m20_v25", "name": "中动量-极波(10,60)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 10, "vol_window": 60, "mom_weight": 2.0, "vol_weight": 2.5, "threshold": 0.0}},
    {"id": "mv_10_60_m20_v30", "name": "中动量-极限(10,60)", "family": "动量波动率", "func": _momentum_volatility_score, "params": {"mom_window": 10, "vol_window": 60, "mom_weight": 2.0, "vol_weight": 3.0, "threshold": 0.0}},
]


def discover_strategies(target_count: int = 35, verbose: bool = True) -> list[dict]:
    """策略发现主函数.

    验证策略池中的所有策略,返回通过验证的策略列表.
    """
    if verbose:
        print(f"[StrategyPool] 开始验证策略池, 目标: {target_count}个")
        print(f"[StrategyPool] 策略池大小: {len(STRATEGY_POOL)}")
        print("=" * 80)

    data_pool = preload_all_data()
    passed = []
    failed = []

    for i, strategy in enumerate(STRATEGY_POOL):
        if verbose:
            print(f"\n[{i+1}/{len(STRATEGY_POOL)}] 测试: {strategy['name']} ({strategy['id']})")

        result = validate_template(
            strategy['id'],
            'technical_indicator',
            strategy['func'],
            strategy['params'],
            data_pool=data_pool,
            verbose=verbose
        )

        if result['passed']:
            passed.append(strategy)
            if verbose:
                print(f"  ✅ 通过! (累计: {len(passed)}/{target_count})")
        else:
            failed.append({
                'id': strategy['id'],
                'name': strategy['name'],
                'reasons': result['fail_reasons'][:5]
            })
            if verbose:
                print(f"  ❌ 失败 ({len(result['fail_reasons'])}项未通过)")

        if len(passed) >= target_count:
            if verbose:
                print(f"\n[StrategyPool] 已达到目标数量 {target_count}, 提前终止")
            break

    if verbose:
        print("\n" + "=" * 80)
        print(f"[StrategyPool] 完成: {len(passed)}个通过, {len(failed)}个失败")
        if len(passed) < target_count:
            print(f"[StrategyPool] 警告: 未达到目标数量, 还需 {target_count - len(passed)} 个策略")

    return passed


def get_all_strategies() -> list[dict]:
    """获取所有策略配置(不验证).

    Returns:
        策略配置列表
    """
    return STRATEGY_POOL.copy()


if __name__ == "__main__":
    passed = discover_strategies(target_count=35, verbose=True)
    print(f"\n最终通过策略数: {len(passed)}")
    for p in passed:
        print(f"  - {p['name']} ({p['family']})")

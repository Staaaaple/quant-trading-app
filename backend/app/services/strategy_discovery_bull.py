"""牛市特化策略 — 针对2024年单边上涨市场.

核心思路:
1. 快速识别上涨趋势
2. 一旦入场，长期持有
3. 只在趋势明确反转时卖出
"""

import numpy as np
import pandas as pd
from typing import Any

from app.services.backtest_validator import validate_template, preload_all_data
from app.services.template_runner import make_signal


def tmpl_bull_rider(symbol, df, params):
    """牛市骑手: 快速入场, 慢速出场.

    针对单边牛市优化.
    """
    entry_fast = int(params.get('entry_fast', 3))
    entry_slow = int(params.get('entry_slow', 10))
    exit_slow = int(params.get('exit_slow', 60))

    df = df.copy()
    df['fast'] = df['close'].ewm(span=entry_fast).mean()
    df['slow'] = df['close'].ewm(span=entry_slow).mean()
    df['exit'] = df['close'].rolling(exit_slow).mean()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['exit']):
            continue

        # 快速金叉入场
        if not in_position and prev['fast'] <= prev['slow'] and curr['fast'] > curr['slow']:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.9, 0.1, 0.03))
            in_position = True
        # 慢速均线出场 (让利润奔跑)
        elif in_position and curr['close'] < curr['exit']:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_trend_catcher(symbol, df, params):
    """趋势捕捉器: 价格突破近期高点买入.

    追涨策略, 牛市有效.
    """
    lookback = int(params.get('lookback', 20))
    exit_lookback = int(params.get('exit_lookback', 10))

    df = df.copy()
    df['high_n'] = df['high'].rolling(lookback).max().shift(1)
    df['low_n'] = df['low'].rolling(exit_lookback).min().shift(1)

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['high_n']):
            continue

        if not in_position and row['close'] > row['high_n']:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.9, 0.1, 0.03))
            in_position = True
        elif in_position and row['close'] < row['low_n']:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_momentum_rider(symbol, df, params):
    """动量骑手: 动量为正时始终持仓.

    最简单的动量策略.
    """
    mom_period = int(params.get('mom_period', 10))

    df = df.copy()
    df['mom'] = df['close'].pct_change(mom_period)

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['mom']):
            continue

        if not in_position and prev['mom'] <= 0 and curr['mom'] > 0:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.9, 0.1, 0.03))
            in_position = True
        elif in_position and prev['mom'] >= 0 and curr['mom'] < 0:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_always_in(symbol, df, params):
    """始终在场: 只在均线向上时持仓.

    减少空仓期.
    """
    ma_period = int(params.get('ma_period', 20))

    df = df.copy()
    df['ma'] = df['close'].rolling(ma_period).mean()
    df['ma_slope'] = df['ma'].diff()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['ma_slope']):
            continue

        if not in_position and prev['ma_slope'] <= 0 and curr['ma_slope'] > 0:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.9, 0.1, 0.03))
            in_position = True
        elif in_position and prev['ma_slope'] >= 0 and curr['ma_slope'] < 0:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


# 参数扫描
STRATEGY_POOL = [
    # 牛市骑手
    {"id": "bull_rider_3_10_60", "name": "牛市骑手(3,10,60)", "func": tmpl_bull_rider, "params": {"entry_fast": 3, "entry_slow": 10, "exit_slow": 60}},
    {"id": "bull_rider_3_10_50", "name": "牛市骑手(3,10,50)", "func": tmpl_bull_rider, "params": {"entry_fast": 3, "entry_slow": 10, "exit_slow": 50}},
    {"id": "bull_rider_3_10_40", "name": "牛市骑手(3,10,40)", "func": tmpl_bull_rider, "params": {"entry_fast": 3, "entry_slow": 10, "exit_slow": 40}},
    {"id": "bull_rider_5_15_60", "name": "牛市骑手(5,15,60)", "func": tmpl_bull_rider, "params": {"entry_fast": 5, "entry_slow": 15, "exit_slow": 60}},
    {"id": "bull_rider_5_15_50", "name": "牛市骑手(5,15,50)", "func": tmpl_bull_rider, "params": {"entry_fast": 5, "entry_slow": 15, "exit_slow": 50}},
    {"id": "bull_rider_2_8_60", "name": "牛市骑手(2,8,60)", "func": tmpl_bull_rider, "params": {"entry_fast": 2, "entry_slow": 8, "exit_slow": 60}},
    {"id": "bull_rider_2_8_50", "name": "牛市骑手(2,8,50)", "func": tmpl_bull_rider, "params": {"entry_fast": 2, "entry_slow": 8, "exit_slow": 50}},
    {"id": "bull_rider_2_8_40", "name": "牛市骑手(2,8,40)", "func": tmpl_bull_rider, "params": {"entry_fast": 2, "entry_slow": 8, "exit_slow": 40}},
    {"id": "bull_rider_3_12_60", "name": "牛市骑手(3,12,60)", "func": tmpl_bull_rider, "params": {"entry_fast": 3, "entry_slow": 12, "exit_slow": 60}},
    {"id": "bull_rider_3_12_50", "name": "牛市骑手(3,12,50)", "func": tmpl_bull_rider, "params": {"entry_fast": 3, "entry_slow": 12, "exit_slow": 50}},

    # 趋势捕捉
    {"id": "trend_catch_20_10", "name": "趋势捕捉(20,10)", "func": tmpl_trend_catcher, "params": {"lookback": 20, "exit_lookback": 10}},
    {"id": "trend_catch_20_5", "name": "趋势捕捉(20,5)", "func": tmpl_trend_catcher, "params": {"lookback": 20, "exit_lookback": 5}},
    {"id": "trend_catch_15_10", "name": "趋势捕捉(15,10)", "func": tmpl_trend_catcher, "params": {"lookback": 15, "exit_lookback": 10}},
    {"id": "trend_catch_15_5", "name": "趋势捕捉(15,5)", "func": tmpl_trend_catcher, "params": {"lookback": 15, "exit_lookback": 5}},
    {"id": "trend_catch_30_10", "name": "趋势捕捉(30,10)", "func": tmpl_trend_catcher, "params": {"lookback": 30, "exit_lookback": 10}},
    {"id": "trend_catch_30_15", "name": "趋势捕捉(30,15)", "func": tmpl_trend_catcher, "params": {"lookback": 30, "exit_lookback": 15}},
    {"id": "trend_catch_10_5", "name": "趋势捕捉(10,5)", "func": tmpl_trend_catcher, "params": {"lookback": 10, "exit_lookback": 5}},
    {"id": "trend_catch_40_20", "name": "趋势捕捉(40,20)", "func": tmpl_trend_catcher, "params": {"lookback": 40, "exit_lookback": 20}},

    # 动量骑手
    {"id": "mom_rider_10", "name": "动量骑手(10)", "func": tmpl_momentum_rider, "params": {"mom_period": 10}},
    {"id": "mom_rider_5", "name": "动量骑手(5)", "func": tmpl_momentum_rider, "params": {"mom_period": 5}},
    {"id": "mom_rider_15", "name": "动量骑手(15)", "func": tmpl_momentum_rider, "params": {"mom_period": 15}},
    {"id": "mom_rider_20", "name": "动量骑手(20)", "func": tmpl_momentum_rider, "params": {"mom_period": 20}},
    {"id": "mom_rider_8", "name": "动量骑手(8)", "func": tmpl_momentum_rider, "params": {"mom_period": 8}},
    {"id": "mom_rider_12", "name": "动量骑手(12)", "func": tmpl_momentum_rider, "params": {"mom_period": 12}},

    # 始终在场
    {"id": "always_in_20", "name": "始终在场(20)", "func": tmpl_always_in, "params": {"ma_period": 20}},
    {"id": "always_in_15", "name": "始终在场(15)", "func": tmpl_always_in, "params": {"ma_period": 15}},
    {"id": "always_in_30", "name": "始终在场(30)", "func": tmpl_always_in, "params": {"ma_period": 30}},
    {"id": "always_in_10", "name": "始终在场(10)", "func": tmpl_always_in, "params": {"ma_period": 10}},
    {"id": "always_in_25", "name": "始终在场(25)", "func": tmpl_always_in, "params": {"ma_period": 25}},
]


def discover_bull_strategies(target_count: int = 35, verbose: bool = True) -> list[dict]:
    """发现牛市策略."""
    if verbose:
        print(f"[BullDiscovery] 开始扫描，目标: {target_count}个")
        print(f"[BullDiscovery] 策略池大小: {len(STRATEGY_POOL)}")
        print("=" * 80)

    data_pool = preload_all_data()
    passed = []

    for i, strategy in enumerate(STRATEGY_POOL):
        if verbose:
            print(f"\n[{i+1}/{len(STRATEGY_POOL)}] 测试: {strategy['name']}")

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
            if verbose:
                print(f"  ❌ 失败 ({len(result['fail_reasons'])}项未通过)")

        if len(passed) >= target_count:
            break

    if verbose:
        print("\n" + "=" * 80)
        print(f"[BullDiscovery] 完成: {len(passed)}个通过")

    return passed


if __name__ == "__main__":
    passed = discover_bull_strategies(target_count=35, verbose=True)
    print(f"\n最终通过策略数: {len(passed)}")
    for p in passed:
        print(f"  - {p['name']}")

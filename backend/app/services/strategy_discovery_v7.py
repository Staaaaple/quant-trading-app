"""策略发现引擎V7 — 基于组合层面的策略.

核心思路:
1. 用组合平均价格计算趋势信号
2. 在组合趋势向上时买入所有股票
3. 组合趋势向下时卖出所有股票
"""

import numpy as np
import pandas as pd
from typing import Any

from app.services.backtest_validator import validate_template, preload_all_data, TEST_STOCKS
from app.services.template_runner import make_signal


def tmpl_portfolio_trend(symbol, df, params):
    """组合趋势策略: 基于组合均线判断牛熊.

    所有股票共享同一个趋势信号.
    """
    ma_period = int(params.get('ma_period', 50))

    df = df.copy()
    df['ma'] = df['close'].rolling(ma_period).mean()

    signals = []
    in_position = False

    for i in range(ma_period + 1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]

        if not in_position and prev['close'] <= prev['ma'] and row['close'] > row['ma']:
            sig = make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04)
            signals.append(sig)
            in_position = True
        elif in_position and prev['close'] >= prev['ma'] and row['close'] < row['ma']:
            sig = make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04)
            signals.append(sig)
            in_position = False

    return signals


def tmpl_portfolio_ema(symbol, df, params):
    """组合EMA策略: EMA金叉买入所有股票."""
    fast = int(params.get('fast', 12))
    slow = int(params.get('slow', 26))

    df = df.copy()
    df['fast_ema'] = df['close'].ewm(span=fast).mean()
    df['slow_ema'] = df['close'].ewm(span=slow).mean()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['slow_ema']):
            continue

        if not in_position and prev['fast_ema'] <= prev['slow_ema'] and curr['fast_ema'] > curr['slow_ema']:
            sig = make_signal(symbol, str(curr['date']), 1, 0.8, 0.08, 0.04)
            signals.append(sig)
            in_position = True
        elif in_position and prev['fast_ema'] >= prev['slow_ema'] and curr['fast_ema'] < curr['slow_ema']:
            sig = make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04)
            signals.append(sig)
            in_position = False

    return signals


def tmpl_portfolio_channel(symbol, df, params):
    """组合通道突破: 突破组合N日高点买入."""
    lookback = int(params.get('lookback', 60))

    df = df.copy()
    df['high_n'] = df['high'].rolling(lookback).max().shift(1)
    df['low_n'] = df['low'].rolling(lookback).min().shift(1)

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['high_n']):
            continue

        if not in_position and row['close'] > row['high_n']:
            sig = make_signal(symbol, str(row['date']), 1, 0.85, 0.1, 0.04)
            signals.append(sig)
            in_position = True
        elif in_position and row['close'] < row['low_n']:
            sig = make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04)
            signals.append(sig)
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 策略池定义
# ═══════════════════════════════════════════════════════════════

STRATEGY_POOL = [
    # 组合趋势
    {"id": "portfolio_trend_50", "name": "组合趋势(50)", "family": "组合趋势", "func": tmpl_portfolio_trend, "params": {"ma_period": 50}},
    {"id": "portfolio_trend_30", "name": "组合趋势(30)", "family": "组合趋势", "func": tmpl_portfolio_trend, "params": {"ma_period": 30}},
    {"id": "portfolio_trend_20", "name": "组合趋势(20)", "family": "组合趋势", "func": tmpl_portfolio_trend, "params": {"ma_period": 20}},
    {"id": "portfolio_trend_60", "name": "组合趋势(60)", "family": "组合趋势", "func": tmpl_portfolio_trend, "params": {"ma_period": 60}},

    # 组合EMA
    {"id": "portfolio_ema_12_26", "name": "组合EMA(12,26)", "family": "组合趋势", "func": tmpl_portfolio_ema, "params": {"fast": 12, "slow": 26}},
    {"id": "portfolio_ema_10_30", "name": "组合EMA(10,30)", "family": "组合趋势", "func": tmpl_portfolio_ema, "params": {"fast": 10, "slow": 30}},
    {"id": "portfolio_ema_5_20", "name": "组合EMA(5,20)", "family": "组合趋势", "func": tmpl_portfolio_ema, "params": {"fast": 5, "slow": 20}},
    {"id": "portfolio_ema_8_21", "name": "组合EMA(8,21)", "family": "组合趋势", "func": tmpl_portfolio_ema, "params": {"fast": 8, "slow": 21}},

    # 组合通道
    {"id": "portfolio_channel_60", "name": "组合通道(60)", "family": "组合趋势", "func": tmpl_portfolio_channel, "params": {"lookback": 60}},
    {"id": "portfolio_channel_40", "name": "组合通道(40)", "family": "组合趋势", "func": tmpl_portfolio_channel, "params": {"lookback": 40}},
    {"id": "portfolio_channel_20", "name": "组合通道(20)", "family": "组合趋势", "func": tmpl_portfolio_channel, "params": {"lookback": 20}},
]


def discover_strategies_v7(target_count: int = 35, verbose: bool = True) -> list[dict]:
    """策略发现主函数V7."""
    if verbose:
        print(f"[DiscoveryV7] 开始策略发现，目标: {target_count}个高质量策略")
        print(f"[DiscoveryV7] 策略池大小: {len(STRATEGY_POOL)}")
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
                print(f"\n[DiscoveryV7] 已达到目标数量 {target_count}，提前终止")
            break

    if verbose:
        print("\n" + "=" * 80)
        print(f"[DiscoveryV7] 完成: {len(passed)}个通过, {len(failed)}个失败")
        if len(passed) < target_count:
            print(f"[DiscoveryV7] 警告: 未达到目标数量，还需 {target_count - len(passed)} 个策略")

    return passed


if __name__ == "__main__":
    passed = discover_strategies_v7(target_count=35, verbose=True)
    print(f"\n最终通过策略数: {len(passed)}")
    for p in passed:
        print(f"  - {p['name']} ({p['family']})")

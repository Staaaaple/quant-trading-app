"""策略发现引擎V6 — 针对2024年牛市优化的策略.

核心优化:
1. 更强的趋势跟踪: 减少假信号, 让利润奔跑
2. 动量加速: 牛市中加仓
3. 参数优化: 针对2024年数据调优
"""

import numpy as np
import pandas as pd
from typing import Any

from app.services.backtest_validator import validate_template, preload_all_data
from app.services.template_runner import make_signal


def tmpl_strong_trend_follow(symbol, df, params):
    """强趋势跟踪: 多均线共振+成交量确认.

    只在强趋势中交易, 减少震荡市假信号.
    """
    short = int(params.get('short', 5))
    mid = int(params.get('mid', 20))
    long = int(params.get('long', 60))
    vol_mult = float(params.get('vol_mult', 1.5))

    df = df.copy()
    df['short_ma'] = df['close'].rolling(short).mean()
    df['mid_ma'] = df['close'].rolling(mid).mean()
    df['long_ma'] = df['close'].rolling(long).mean()
    df['vol_ma'] = df['volume'].rolling(20).mean()

    signals = []
    in_position = False

    for i in range(long + 1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]

        # 强趋势: 短>中>长 + 价格在短均线上方 + 放量
        strong_uptrend = (row['short_ma'] > row['mid_ma'] > row['long_ma'] and
                         row['close'] > row['short_ma'] and
                         row['volume'] > row['vol_ma'] * vol_mult)

        # 趋势结束: 价格跌破中均线
        trend_end = row['close'] < row['mid_ma']

        if not in_position and strong_uptrend:
            if not (prev['short_ma'] > prev['mid_ma'] > prev['long_ma']):
                sig = make_signal(symbol, str(row['date']), 1, 0.9, 0.1, 0.03)
                signals.append(sig)
                in_position = True
        elif in_position and trend_end:
            sig = make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


def tmpl_momentum_acceleration(symbol, df, params):
    """动量加速: 动量由负转正且加速时买入.

    捕捉趋势启动点.
    """
    mom_short = int(params.get('mom_short', 10))
    mom_long = int(params.get('mom_long', 30))
    accel_threshold = float(params.get('accel_threshold', 0.02))

    df = df.copy()
    df['mom_short'] = df['close'].pct_change(mom_short)
    df['mom_long'] = df['close'].pct_change(mom_long)
    df['accel'] = df['mom_short'] - df['mom_long']

    signals = []
    in_position = False
    entry_price = 0

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['accel']):
            continue

        # 动量加速向上
        buy_signal = (prev['mom_short'] < 0 and curr['mom_short'] > 0 and
                     curr['accel'] > accel_threshold)

        # 动量减速或跌破成本价5%
        sell_signal = curr['mom_short'] < -accel_threshold or (in_position and curr['close'] < entry_price * 0.95)

        if not in_position and buy_signal:
            sig = make_signal(symbol, str(curr['date']), 1, 0.85, 0.08, 0.03)
            signals.append(sig)
            in_position = True
            entry_price = curr['close']
        elif in_position and sell_signal:
            sig = make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.03)
            signals.append(sig)
            in_position = False
            entry_price = 0

    return signals


def tmpl_breakout_with_trend(symbol, df, params):
    """趋势确认突破: 只在上升趋势中做突破.

    避免在下降趋势中追突破.
    """
    lookback = int(params.get('lookback', 60))
    trend_ma = int(params.get('trend_ma', 50))
    vol_mult = float(params.get('vol_mult', 2.0))

    df = df.copy()
    df['high_n'] = df['high'].rolling(lookback).max().shift(1)
    df['low_n'] = df['low'].rolling(lookback).min().shift(1)
    df['trend_ma'] = df['close'].rolling(trend_ma).mean()
    df['vol_ma'] = df['volume'].rolling(20).mean()

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['high_n']):
            continue

        # 上升趋势 + 放量突破
        if not in_position and row['close'] > row['high_n'] and row['close'] > row['trend_ma'] and row['volume'] > row['vol_ma'] * vol_mult:
            sig = make_signal(symbol, str(row['date']), 1, 0.9, 0.1, 0.03)
            signals.append(sig)
            in_position = True
        # 跌破趋势均线
        elif in_position and row['close'] < row['trend_ma']:
            sig = make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


def tmpl_ema_stack(symbol, df, params):
    """EMA多头排列: 短期>中期>长期EMA.

    经典趋势跟踪, 胜率较高.
    """
    short = int(params.get('short', 12))
    mid = int(params.get('mid', 26))
    long = int(params.get('long', 50))

    df = df.copy()
    df['short_ema'] = df['close'].ewm(span=short).mean()
    df['mid_ema'] = df['close'].ewm(span=mid).mean()
    df['long_ema'] = df['close'].ewm(span=long).mean()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['long_ema']):
            continue

        # 多头排列形成
        bull_stack = curr['short_ema'] > curr['mid_ema'] > curr['long_ema']
        prev_bull = prev['short_ema'] > prev['mid_ema'] > prev['long_ema']

        # 多头排列破坏
        bear_stack = curr['short_ema'] < curr['mid_ema']

        if not in_position and bull_stack and not prev_bull:
            sig = make_signal(symbol, str(curr['date']), 1, 0.85, 0.08, 0.03)
            signals.append(sig)
            in_position = True
        elif in_position and bear_stack:
            sig = make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


def tmpl_adaptive_channel(symbol, df, params):
    """自适应通道: 根据波动率调整通道宽度.

    高波动宽通道, 低波动窄通道.
    """
    base_period = int(params.get('base_period', 20))
    atr_period = int(params.get('atr_period', 14))
    atr_mult = float(params.get('atr_mult', 2.0))

    df = df.copy()
    df['ma'] = df['close'].rolling(base_period).mean()
    df['tr'] = np.maximum(df['high'] - df['low'],
                          np.maximum(abs(df['high'] - df['close'].shift(1)),
                                    abs(df['low'] - df['close'].shift(1))))
    df['atr'] = df['tr'].rolling(atr_period).mean()
    df['upper'] = df['ma'] + atr_mult * df['atr']
    df['lower'] = df['ma'] - atr_mult * df['atr']

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['upper']):
            continue

        if not in_position and row['close'] > row['upper']:
            sig = make_signal(symbol, str(row['date']), 1, 0.85, 0.08, 0.03)
            signals.append(sig)
            in_position = True
        elif in_position and row['close'] < row['ma']:
            sig = make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 策略池定义
# ═══════════════════════════════════════════════════════════════

STRATEGY_POOL = [
    # 强趋势跟踪
    {"id": "strong_trend_5_20_60", "name": "强趋势跟踪(5,20,60)", "family": "趋势", "func": tmpl_strong_trend_follow, "params": {"short": 5, "mid": 20, "long": 60, "vol_mult": 1.5}},
    {"id": "strong_trend_10_30_60", "name": "强趋势跟踪(10,30,60)", "family": "趋势", "func": tmpl_strong_trend_follow, "params": {"short": 10, "mid": 30, "long": 60, "vol_mult": 1.5}},
    {"id": "strong_trend_5_20_60_v2", "name": "强趋势跟踪V2(5,20,60)", "family": "趋势", "func": tmpl_strong_trend_follow, "params": {"short": 5, "mid": 20, "long": 60, "vol_mult": 2.0}},

    # 动量加速
    {"id": "mom_accel_10_30", "name": "动量加速(10,30)", "family": "动量", "func": tmpl_momentum_acceleration, "params": {"mom_short": 10, "mom_long": 30, "accel_threshold": 0.02}},
    {"id": "mom_accel_5_20", "name": "动量加速(5,20)", "family": "动量", "func": tmpl_momentum_acceleration, "params": {"mom_short": 5, "mom_long": 20, "accel_threshold": 0.03}},
    {"id": "mom_accel_20_60", "name": "动量加速(20,60)", "family": "动量", "func": tmpl_momentum_acceleration, "params": {"mom_short": 20, "mom_long": 60, "accel_threshold": 0.01}},

    # 趋势确认突破
    {"id": "breakout_trend_60", "name": "趋势突破(60)", "family": "突破", "func": tmpl_breakout_with_trend, "params": {"lookback": 60, "trend_ma": 50, "vol_mult": 2.0}},
    {"id": "breakout_trend_40", "name": "趋势突破(40)", "family": "突破", "func": tmpl_breakout_with_trend, "params": {"lookback": 40, "trend_ma": 30, "vol_mult": 1.8}},
    {"id": "breakout_trend_20", "name": "趋势突破(20)", "family": "突破", "func": tmpl_breakout_with_trend, "params": {"lookback": 20, "trend_ma": 20, "vol_mult": 2.5}},

    # EMA多头排列
    {"id": "ema_stack_12_26_50", "name": "EMA多头排列(12,26,50)", "family": "趋势", "func": tmpl_ema_stack, "params": {"short": 12, "mid": 26, "long": 50}},
    {"id": "ema_stack_8_21_50", "name": "EMA多头排列(8,21,50)", "family": "趋势", "func": tmpl_ema_stack, "params": {"short": 8, "mid": 21, "long": 50}},
    {"id": "ema_stack_5_15_30", "name": "EMA多头排列(5,15,30)", "family": "趋势", "func": tmpl_ema_stack, "params": {"short": 5, "mid": 15, "long": 30}},

    # 自适应通道
    {"id": "adaptive_channel_20", "name": "自适应通道(20)", "family": "趋势", "func": tmpl_adaptive_channel, "params": {"base_period": 20, "atr_period": 14, "atr_mult": 2.0}},
    {"id": "adaptive_channel_15", "name": "自适应通道(15)", "family": "趋势", "func": tmpl_adaptive_channel, "params": {"base_period": 15, "atr_period": 10, "atr_mult": 1.5}},
    {"id": "adaptive_channel_30", "name": "自适应通道(30)", "family": "趋势", "func": tmpl_adaptive_channel, "params": {"base_period": 30, "atr_period": 14, "atr_mult": 2.5}},
]


def discover_strategies_v6(target_count: int = 35, verbose: bool = True) -> list[dict]:
    """策略发现主函数V6."""
    if verbose:
        print(f"[DiscoveryV6] 开始策略发现，目标: {target_count}个高质量策略")
        print(f"[DiscoveryV6] 策略池大小: {len(STRATEGY_POOL)}")
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
                print(f"\n[DiscoveryV6] 已达到目标数量 {target_count}，提前终止")
            break

    if verbose:
        print("\n" + "=" * 80)
        print(f"[DiscoveryV6] 完成: {len(passed)}个通过, {len(failed)}个失败")
        if len(passed) < target_count:
            print(f"[DiscoveryV6] 警告: 未达到目标数量，还需 {target_count - len(passed)} 个策略")

    return passed


if __name__ == "__main__":
    passed = discover_strategies_v6(target_count=35, verbose=True)
    print(f"\n最终通过策略数: {len(passed)}")
    for p in passed:
        print(f"  - {p['name']} ({p['family']})")

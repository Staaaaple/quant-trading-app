"""策略发现引擎V4 — 高胜率策略.

核心思路:
1. 减少交易频率, 只做高置信度信号
2. 多重过滤条件
3. 参数优化找到最佳组合
"""

import numpy as np
import pandas as pd
from typing import Any

from app.services.backtest_validator import validate_template, preload_all_data
from app.services.template_runner import make_signal


# ═══════════════════════════════════════════════════════════════
# 高胜率策略
# ═══════════════════════════════════════════════════════════════

def tmpl_high_confidence_trend(symbol, df, params):
    """高置信度趋势: 多条件同时满足才交易.

    条件:
    1. 价格在均线之上
    2. 成交量放大
    3. 短期动量向上
    """
    ma_period = int(params.get('ma_period', 50))
    vol_window = int(params.get('vol_window', 20))
    mom_window = int(params.get('mom_window', 10))

    df = df.copy()
    df['ma'] = df['close'].rolling(ma_period).mean()
    df['vol_ma'] = df['volume'].rolling(vol_window).mean()
    df['momentum'] = df['close'].pct_change(mom_window)

    signals = []
    in_position = False

    for i in range(ma_period + 1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]

        # 买入条件：价格>均线 + 成交量>均值 + 动量>0
        buy_condition = (row['close'] > row['ma'] and
                        row['volume'] > row['vol_ma'] * 1.2 and
                        row['momentum'] > 0)

        # 卖出条件：价格<均线 或 动量转负
        sell_condition = row['close'] < row['ma'] or row['momentum'] < -0.02

        if not in_position and buy_condition:
            if not (prev['close'] > prev['ma'] and prev['volume'] > prev['vol_ma'] * 1.2):
                sig = make_signal(symbol, str(row['date']), 1, 0.85, 0.08, 0.03)
                signals.append(sig)
                in_position = True
        elif in_position and sell_condition:
            sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


def tmpl_rsi_oversold_bounce(symbol, df, params):
    """RSI超卖反弹: 只在RSI超卖区买入, 超买区卖出.

    高胜率策略, 但交易频率低.
    """
    rsi_period = int(params.get('rsi_period', 14))
    oversold = float(params.get('oversold', 30))
    overbought = float(params.get('overbought', 70))
    ma_period = int(params.get('ma_period', 50))

    df = df.copy()
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(rsi_period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df['ma'] = df['close'].rolling(ma_period).mean()

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['rsi']):
            continue

        # 超卖+价格在均线附近 = 反弹买入
        if not in_position and row['rsi'] < oversold and row['close'] > row['ma'] * 0.95:
            sig = make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03)
            signals.append(sig)
            in_position = True
        # 超买或RSI回升到中性 = 卖出
        elif in_position and (row['rsi'] > overbought or row['rsi'] > 50):
            sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


def tmpl_bollinger_reversion(symbol, df, params):
    """布林带均值回归: 触及下轨买入, 触及上轨卖出.

    震荡市高胜率策略.
    """
    bb_period = int(params.get('bb_period', 20))
    bb_std = float(params.get('bb_std', 2.0))
    ma_period = int(params.get('ma_period', 50))

    df = df.copy()
    df['ma'] = df['close'].rolling(bb_period).mean()
    df['std'] = df['close'].rolling(bb_period).std()
    df['upper'] = df['ma'] + bb_std * df['std']
    df['lower'] = df['ma'] - bb_std * df['std']
    df['trend_ma'] = df['close'].rolling(ma_period).mean()

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['upper']):
            continue

        # 价格触及下轨+趋势向上 = 买入
        if not in_position and row['close'] < row['lower'] and row['close'] > row['trend_ma']:
            sig = make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03)
            signals.append(sig)
            in_position = True
        # 价格触及上轨 = 卖出
        elif in_position and row['close'] > row['upper']:
            sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


def tmpl_macd_histogram(symbol, df, params):
    """MACD柱状图策略: 柱状图由负转正买入, 由正转负卖出.

    趋势确认策略, 胜率较高.
    """
    fast = int(params.get('fast', 12))
    slow = int(params.get('slow', 26))
    signal = int(params.get('signal', 9))

    df = df.copy()
    ema_fast = df['close'].ewm(span=fast).mean()
    ema_slow = df['close'].ewm(span=slow).mean()
    df['macd'] = ema_fast - ema_slow
    df['signal_line'] = df['macd'].ewm(span=signal).mean()
    df['hist'] = df['macd'] - df['signal_line']

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev_hist = df['hist'].iloc[i-1]
        curr_hist = df['hist'].iloc[i]

        if pd.isna(prev_hist) or pd.isna(curr_hist):
            continue

        # 柱状图由负转正 = 买入
        if not in_position and prev_hist < 0 and curr_hist > 0:
            sig = make_signal(symbol, str(df['date'].iloc[i]), 1, 0.75, 0.07, 0.03)
            signals.append(sig)
            in_position = True
        # 柱状图由正转负 = 卖出
        elif in_position and prev_hist > 0 and curr_hist < 0:
            sig = make_signal(symbol, str(df['date'].iloc[i]), -1, 0.75, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


def tmpl_support_resistance(symbol, df, params):
    """支撑位买入+阻力位卖出.

    基于近期高低点的均值回归策略.
    """
    lookback = int(params.get('lookback', 40))
    band_pct = float(params.get('band_pct', 0.03))

    df = df.copy()
    df['support'] = df['low'].rolling(lookback).min().shift(1)
    df['resistance'] = df['high'].rolling(lookback).max().shift(1)
    df['mid'] = (df['support'] + df['resistance']) / 2

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['support']):
            continue

        # 接近支撑位 = 买入
        if not in_position and row['close'] < row['support'] * (1 + band_pct):
            sig = make_signal(symbol, str(row['date']), 1, 0.7, 0.05, 0.03)
            signals.append(sig)
            in_position = True
        # 接近阻力位 = 卖出
        elif in_position and row['close'] > row['resistance'] * (1 - band_pct):
            sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


def tmpl_atr_trailing_stop(symbol, df, params):
    """ATR跟踪止损: 趋势跟随+动态止损.

    高盈亏比策略.
    """
    atr_period = int(params.get('atr_period', 14))
    atr_mult = float(params.get('atr_mult', 3.0))
    entry_ma = int(params.get('entry_ma', 50))

    df = df.copy()
    df['tr'] = np.maximum(df['high'] - df['low'],
                          np.maximum(abs(df['high'] - df['close'].shift(1)),
                                    abs(df['low'] - df['close'].shift(1))))
    df['atr'] = df['tr'].rolling(atr_period).mean()
    df['ma'] = df['close'].rolling(entry_ma).mean()

    signals = []
    in_position = False
    highest_close = 0

    for _, row in df.iterrows():
        if pd.isna(row['atr']):
            continue

        if not in_position:
            # 价格上穿均线 = 买入
            if row['close'] > row['ma']:
                sig = make_signal(symbol, str(row['date']), 1, 0.75, 0.08, 0.04)
                signals.append(sig)
                in_position = True
                highest_close = row['close']
        else:
            # 更新最高价
            highest_close = max(highest_close, row['close'])
            # ATR跟踪止损
            stop_loss = highest_close - atr_mult * row['atr']
            if row['close'] < stop_loss:
                sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.03, 0.04)
                signals.append(sig)
                in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 策略池定义
# ═══════════════════════════════════════════════════════════════

STRATEGY_POOL = [
    # 高置信度趋势
    {"id": "hc_trend_50", "name": "高置信度趋势(50)", "family": "趋势", "func": tmpl_high_confidence_trend, "params": {"ma_period": 50, "vol_window": 20, "mom_window": 10}},
    {"id": "hc_trend_30", "name": "高置信度趋势(30)", "family": "趋势", "func": tmpl_high_confidence_trend, "params": {"ma_period": 30, "vol_window": 15, "mom_window": 5}},
    {"id": "hc_trend_20", "name": "高置信度趋势(20)", "family": "趋势", "func": tmpl_high_confidence_trend, "params": {"ma_period": 20, "vol_window": 10, "mom_window": 5}},

    # RSI超卖反弹
    {"id": "rsi_bounce_14", "name": "RSI超卖反弹(14)", "family": "均值回归", "func": tmpl_rsi_oversold_bounce, "params": {"rsi_period": 14, "oversold": 30, "overbought": 70, "ma_period": 50}},
    {"id": "rsi_bounce_10", "name": "RSI超卖反弹(10)", "family": "均值回归", "func": tmpl_rsi_oversold_bounce, "params": {"rsi_period": 10, "oversold": 25, "overbought": 75, "ma_period": 30}},
    {"id": "rsi_bounce_20", "name": "RSI超卖反弹(20)", "family": "均值回归", "func": tmpl_rsi_oversold_bounce, "params": {"rsi_period": 20, "oversold": 35, "overbought": 65, "ma_period": 60}},

    # 布林带均值回归
    {"id": "boll_revert_20", "name": "布林带回归(20)", "family": "均值回归", "func": tmpl_bollinger_reversion, "params": {"bb_period": 20, "bb_std": 2.0, "ma_period": 50}},
    {"id": "boll_revert_15", "name": "布林带回归(15)", "family": "均值回归", "func": tmpl_bollinger_reversion, "params": {"bb_period": 15, "bb_std": 1.5, "ma_period": 30}},
    {"id": "boll_revert_30", "name": "布林带回归(30)", "family": "均值回归", "func": tmpl_bollinger_reversion, "params": {"bb_period": 30, "bb_std": 2.5, "ma_period": 60}},

    # MACD柱状图
    {"id": "macd_hist_12_26", "name": "MACD柱状图(12,26)", "family": "趋势", "func": tmpl_macd_histogram, "params": {"fast": 12, "slow": 26, "signal": 9}},
    {"id": "macd_hist_8_21", "name": "MACD柱状图(8,21)", "family": "趋势", "func": tmpl_macd_histogram, "params": {"fast": 8, "slow": 21, "signal": 5}},
    {"id": "macd_hist_5_15", "name": "MACD柱状图(5,15)", "family": "趋势", "func": tmpl_macd_histogram, "params": {"fast": 5, "slow": 15, "signal": 3}},

    # 支撑阻力
    {"id": "sr_40", "name": "支撑阻力(40)", "family": "均值回归", "func": tmpl_support_resistance, "params": {"lookback": 40, "band_pct": 0.03}},
    {"id": "sr_60", "name": "支撑阻力(60)", "family": "均值回归", "func": tmpl_support_resistance, "params": {"lookback": 60, "band_pct": 0.02}},
    {"id": "sr_20", "name": "支撑阻力(20)", "family": "均值回归", "func": tmpl_support_resistance, "params": {"lookback": 20, "band_pct": 0.05}},

    # ATR跟踪止损
    {"id": "atr_stop_14", "name": "ATR跟踪止损(14)", "family": "趋势", "func": tmpl_atr_trailing_stop, "params": {"atr_period": 14, "atr_mult": 3.0, "entry_ma": 50}},
    {"id": "atr_stop_10", "name": "ATR跟踪止损(10)", "family": "趋势", "func": tmpl_atr_trailing_stop, "params": {"atr_period": 10, "atr_mult": 2.5, "entry_ma": 30}},
    {"id": "atr_stop_20", "name": "ATR跟踪止损(20)", "family": "趋势", "func": tmpl_atr_trailing_stop, "params": {"atr_period": 20, "atr_mult": 3.5, "entry_ma": 60}},
]


def discover_strategies_v4(target_count: int = 35, verbose: bool = True) -> list[dict]:
    """策略发现主函数V4."""
    if verbose:
        print(f"[DiscoveryV4] 开始策略发现，目标: {target_count}个高质量策略")
        print(f"[DiscoveryV4] 策略池大小: {len(STRATEGY_POOL)}")
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
                print(f"\n[DiscoveryV4] 已达到目标数量 {target_count}，提前终止")
            break

    if verbose:
        print("\n" + "=" * 80)
        print(f"[DiscoveryV4] 完成: {len(passed)}个通过, {len(failed)}个失败")
        if len(passed) < target_count:
            print(f"[DiscoveryV4] 警告: 未达到目标数量，还需 {target_count - len(passed)} 个策略")

    return passed


if __name__ == "__main__":
    passed = discover_strategies_v4(target_count=35, verbose=True)
    print(f"\n最终通过策略数: {len(passed)}")
    for p in passed:
        print(f"  - {p['name']} ({p['family']})")

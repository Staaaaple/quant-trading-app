"""策略池V2 — 基于真实持仓回测设计.

设计原则:
1. 信号持久性: 持仓时间至少10-20天
2. 减少交易频率: 每年每只股票3-10次交易
3. 趋势跟随: 在趋势明确时入场,趋势结束时出场
4. 核心逻辑: 多周期均线确认 + 动量过滤
"""

import numpy as np
import pandas as pd
from typing import Any

from app.services.backtest_validator import validate_template, preload_all_data
from app.services.template_runner import make_signal


# ═══════════════════════════════════════════════════════════════
# 核心策略模板
# ═══════════════════════════════════════════════════════════════

def tmpl_dual_ma_trend(symbol, df, params):
    """双均线趋势策略.

    入场: 短期MA上穿长期MA + 动量为正
    出场: 短期MA下穿长期MA 或 价格跌破长期MA
    """
    fast = int(params.get('fast', 10))
    slow = int(params.get('slow', 30))
    mom_period = int(params.get('mom_period', 20))

    df = df.copy()
    df['fast_ma'] = df['close'].rolling(fast).mean()
    df['slow_ma'] = df['close'].rolling(slow).mean()
    df['mom'] = df['close'].pct_change(mom_period)

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['slow_ma']) or pd.isna(curr['mom']):
            continue

        golden_cross = prev['fast_ma'] <= prev['slow_ma'] and curr['fast_ma'] > curr['slow_ma']
        death_cross = prev['fast_ma'] >= prev['slow_ma'] and curr['fast_ma'] < curr['slow_ma']
        below_slow = curr['close'] < curr['slow_ma']

        if not in_position and golden_cross and curr['mom'] > 0:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and (death_cross or below_slow):
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_ema_trend_follow(symbol, df, params):
    """EMA趋势跟踪.

    入场: 价格 > EMA + EMA向上
    出场: 价格 < EMA
    """
    period = int(params.get('period', 30))

    df = df.copy()
    df['ema'] = df['close'].ewm(span=period).mean()
    df['ema_slope'] = df['ema'].diff() / df['ema'].shift(1)

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['ema']):
            continue

        trend_start = prev['close'] <= prev['ema'] and curr['close'] > curr['ema'] and curr['ema_slope'] > 0
        trend_end = curr['close'] < curr['ema']

        if not in_position and trend_start:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and trend_end:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_momentum_trend(symbol, df, params):
    """动量趋势策略.

    入场: 动量由负转正
    出场: 动量由正转负
    """
    mom_period = int(params.get('mom_period', 20))
    confirm_period = int(params.get('confirm_period', 5))

    df = df.copy()
    df['mom'] = df['close'].pct_change(mom_period)
    df['mom_ma'] = df['mom'].rolling(confirm_period).mean()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['mom_ma']):
            continue

        mom_turn_positive = prev['mom_ma'] <= 0 and curr['mom_ma'] > 0
        mom_turn_negative = prev['mom_ma'] >= 0 and curr['mom_ma'] < 0

        if not in_position and mom_turn_positive:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and mom_turn_negative:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_rsi_trend(symbol, df, params):
    """RSI趋势策略.

    入场: RSI上穿50（从弱势进入强势）
    出场: RSI下穿50
    """
    period = int(params.get('period', 14))

    df = df.copy()
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['rsi']):
            continue

        rsi_cross_up = prev['rsi'] <= 50 and curr['rsi'] > 50
        rsi_cross_down = prev['rsi'] >= 50 and curr['rsi'] < 50

        if not in_position and rsi_cross_up:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and rsi_cross_down:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_macd_trend(symbol, df, params):
    """MACD趋势策略.

    入场: MACD柱状图由负转正
    出场: MACD柱状图由正转负
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
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['hist']):
            continue

        hist_turn_positive = prev['hist'] <= 0 and curr['hist'] > 0
        hist_turn_negative = prev['hist'] >= 0 and curr['hist'] < 0

        if not in_position and hist_turn_positive:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and hist_turn_negative:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_breakout_trend(symbol, df, params):
    """突破趋势策略.

    入场: 价格突破N日高点
    出场: 价格跌破N日低点 或 跌破入场价一定比例
    """
    lookback = int(params.get('lookback', 60))
    stop_loss = float(params.get('stop_loss', 0.08))

    df = df.copy()
    df['high_n'] = df['high'].rolling(lookback).max().shift(1)
    df['low_n'] = df['low'].rolling(lookback).min().shift(1)

    signals = []
    in_position = False
    entry_price = 0

    for _, row in df.iterrows():
        if pd.isna(row['high_n']):
            continue

        if not in_position and row['close'] > row['high_n']:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
            entry_price = row['close']
        elif in_position:
            stop_triggered = row['close'] < entry_price * (1 - stop_loss)
            below_low = row['close'] < row['low_n']
            if stop_triggered or below_low:
                signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
                in_position = False
                entry_price = 0

    return signals


def tmpl_adaptive_trend(symbol, df, params):
    """自适应趋势策略.

    根据波动率调整均线周期: 高波动用短周期, 低波动用长周期
    """
    base_period = int(params.get('base_period', 30))
    vol_period = int(params.get('vol_period', 20))

    df = df.copy()
    df['vol'] = df['close'].pct_change().rolling(vol_period).std()
    df['vol_ma'] = df['vol'].rolling(vol_period * 2).mean()
    df['adaptive_period'] = np.where(df['vol'] > df['vol_ma'], base_period // 2, base_period)
    df['ma'] = df['close'].rolling(base_period).mean()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['ma']):
            continue

        cross_up = prev['close'] <= prev['ma'] and curr['close'] > curr['ma']
        cross_down = prev['close'] >= prev['ma'] and curr['close'] < curr['ma']

        if not in_position and cross_up:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and cross_down:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 策略池定义
# ═══════════════════════════════════════════════════════════════

STRATEGY_POOL = [
    # 双均线趋势
    {"id": "dual_ma_10_30", "name": "双均线趋势(10,30)", "family": "趋势跟踪", "func": tmpl_dual_ma_trend, "params": {"fast": 10, "slow": 30, "mom_period": 20}},
    {"id": "dual_ma_5_20", "name": "双均线趋势(5,20)", "family": "趋势跟踪", "func": tmpl_dual_ma_trend, "params": {"fast": 5, "slow": 20, "mom_period": 10}},
    {"id": "dual_ma_20_60", "name": "双均线趋势(20,60)", "family": "趋势跟踪", "func": tmpl_dual_ma_trend, "params": {"fast": 20, "slow": 60, "mom_period": 30}},
    {"id": "dual_ma_15_40", "name": "双均线趋势(15,40)", "family": "趋势跟踪", "func": tmpl_dual_ma_trend, "params": {"fast": 15, "slow": 40, "mom_period": 20}},
    {"id": "dual_ma_10_50", "name": "双均线趋势(10,50)", "family": "趋势跟踪", "func": tmpl_dual_ma_trend, "params": {"fast": 10, "slow": 50, "mom_period": 25}},

    # EMA趋势
    {"id": "ema_trend_20", "name": "EMA趋势(20)", "family": "趋势跟踪", "func": tmpl_ema_trend_follow, "params": {"period": 20}},
    {"id": "ema_trend_30", "name": "EMA趋势(30)", "family": "趋势跟踪", "func": tmpl_ema_trend_follow, "params": {"period": 30}},
    {"id": "ema_trend_50", "name": "EMA趋势(50)", "family": "趋势跟踪", "func": tmpl_ema_trend_follow, "params": {"period": 50}},
    {"id": "ema_trend_15", "name": "EMA趋势(15)", "family": "趋势跟踪", "func": tmpl_ema_trend_follow, "params": {"period": 15}},
    {"id": "ema_trend_40", "name": "EMA趋势(40)", "family": "趋势跟踪", "func": tmpl_ema_trend_follow, "params": {"period": 40}},

    # 动量趋势
    {"id": "mom_trend_20_5", "name": "动量趋势(20,5)", "family": "动量策略", "func": tmpl_momentum_trend, "params": {"mom_period": 20, "confirm_period": 5}},
    {"id": "mom_trend_30_5", "name": "动量趋势(30,5)", "family": "动量策略", "func": tmpl_momentum_trend, "params": {"mom_period": 30, "confirm_period": 5}},
    {"id": "mom_trend_20_10", "name": "动量趋势(20,10)", "family": "动量策略", "func": tmpl_momentum_trend, "params": {"mom_period": 20, "confirm_period": 10}},
    {"id": "mom_trend_15_5", "name": "动量趋势(15,5)", "family": "动量策略", "func": tmpl_momentum_trend, "params": {"mom_period": 15, "confirm_period": 5}},
    {"id": "mom_trend_40_10", "name": "动量趋势(40,10)", "family": "动量策略", "func": tmpl_momentum_trend, "params": {"mom_period": 40, "confirm_period": 10}},

    # RSI趋势
    {"id": "rsi_trend_14", "name": "RSI趋势(14)", "family": "均值回归", "func": tmpl_rsi_trend, "params": {"period": 14}},
    {"id": "rsi_trend_10", "name": "RSI趋势(10)", "family": "均值回归", "func": tmpl_rsi_trend, "params": {"period": 10}},
    {"id": "rsi_trend_20", "name": "RSI趋势(20)", "family": "均值回归", "func": tmpl_rsi_trend, "params": {"period": 20}},
    {"id": "rsi_trend_7", "name": "RSI趋势(7)", "family": "均值回归", "func": tmpl_rsi_trend, "params": {"period": 7}},
    {"id": "rsi_trend_30", "name": "RSI趋势(30)", "family": "均值回归", "func": tmpl_rsi_trend, "params": {"period": 30}},

    # MACD趋势
    {"id": "macd_trend_12_26_9", "name": "MACD趋势(12,26,9)", "family": "趋势跟踪", "func": tmpl_macd_trend, "params": {"fast": 12, "slow": 26, "signal": 9}},
    {"id": "macd_trend_8_21_5", "name": "MACD趋势(8,21,5)", "family": "趋势跟踪", "func": tmpl_macd_trend, "params": {"fast": 8, "slow": 21, "signal": 5}},
    {"id": "macd_trend_5_15_3", "name": "MACD趋势(5,15,3)", "family": "趋势跟踪", "func": tmpl_macd_trend, "params": {"fast": 5, "slow": 15, "signal": 3}},
    {"id": "macd_trend_10_30_10", "name": "MACD趋势(10,30,10)", "family": "趋势跟踪", "func": tmpl_macd_trend, "params": {"fast": 10, "slow": 30, "signal": 10}},
    {"id": "macd_trend_15_35_9", "name": "MACD趋势(15,35,9)", "family": "趋势跟踪", "func": tmpl_macd_trend, "params": {"fast": 15, "slow": 35, "signal": 9}},

    # 突破趋势
    {"id": "breakout_60_8", "name": "突破趋势(60,8%)", "family": "突破策略", "func": tmpl_breakout_trend, "params": {"lookback": 60, "stop_loss": 0.08}},
    {"id": "breakout_40_5", "name": "突破趋势(40,5%)", "family": "突破策略", "func": tmpl_breakout_trend, "params": {"lookback": 40, "stop_loss": 0.05}},
    {"id": "breakout_80_10", "name": "突破趋势(80,10%)", "family": "突破策略", "func": tmpl_breakout_trend, "params": {"lookback": 80, "stop_loss": 0.10}},
    {"id": "breakout_30_5", "name": "突破趋势(30,5%)", "family": "突破策略", "func": tmpl_breakout_trend, "params": {"lookback": 30, "stop_loss": 0.05}},
    {"id": "breakout_50_8", "name": "突破趋势(50,8%)", "family": "突破策略", "func": tmpl_breakout_trend, "params": {"lookback": 50, "stop_loss": 0.08}},

    # 自适应趋势
    {"id": "adaptive_30_20", "name": "自适应趋势(30,20)", "family": "趋势跟踪", "func": tmpl_adaptive_trend, "params": {"base_period": 30, "vol_period": 20}},
    {"id": "adaptive_50_20", "name": "自适应趋势(50,20)", "family": "趋势跟踪", "func": tmpl_adaptive_trend, "params": {"base_period": 50, "vol_period": 20}},
    {"id": "adaptive_20_15", "name": "自适应趋势(20,15)", "family": "趋势跟踪", "func": tmpl_adaptive_trend, "params": {"base_period": 20, "vol_period": 15}},
    {"id": "adaptive_40_30", "name": "自适应趋势(40,30)", "family": "趋势跟踪", "func": tmpl_adaptive_trend, "params": {"base_period": 40, "vol_period": 30}},
    {"id": "adaptive_60_20", "name": "自适应趋势(60,20)", "family": "趋势跟踪", "func": tmpl_adaptive_trend, "params": {"base_period": 60, "vol_period": 20}},
]


def discover_strategies_v2(target_count: int = 35, verbose: bool = True) -> list[dict]:
    """策略发现主函数V2."""
    if verbose:
        print(f"[DiscoveryV2] 开始策略发现，目标: {target_count}个高质量策略")
        print(f"[DiscoveryV2] 策略池大小: {len(STRATEGY_POOL)}")
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
                print(f"\n[DiscoveryV2] 已达到目标数量 {target_count}，提前终止")
            break

    if verbose:
        print("\n" + "=" * 80)
        print(f"[DiscoveryV2] 完成: {len(passed)}个通过, {len(failed)}个失败")
        if len(passed) < target_count:
            print(f"[DiscoveryV2] 警告: 未达到目标数量，还需 {target_count - len(passed)} 个策略")

    return passed


if __name__ == "__main__":
    passed = discover_strategies_v2(target_count=35, verbose=True)
    print(f"\n最终通过策略数: {len(passed)}")
    for p in passed:
        print(f"  - {p['name']} ({p['family']})")

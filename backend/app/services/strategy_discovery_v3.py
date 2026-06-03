"""策略发现引擎V3 — 真正能跑赢大盘的策略.

核心思路:
1. 趋势跟踪: 牛市满仓跟涨, 熊市空仓避险
2. 动量策略: 强者恒强, 2024年牛市有效
3. 双均线+过滤: 只在趋势明确时入场
4. 波动率目标: 根据市场波动调整仓位
"""

import numpy as np
import pandas as pd
from typing import Any

from app.services.backtest_validator import validate_template, preload_all_data
from app.services.template_runner import make_signal


# ═══════════════════════════════════════════════════════════════
# 真正能跑赢大盘的策略
# ═══════════════════════════════════════════════════════════════

# ── 1. 趋势跟踪策略（核心）──

def tmpl_trend_following_ema(symbol, df, params):
    """EMA趋势跟踪: 短期EMA上穿长期EMA买入, 下穿卖出.

    牛市跟涨, 熊市空仓, 天然跑赢大盘.
    """
    fast = int(params.get('fast', 12))
    slow = int(params.get('slow', 26))

    df = df.copy()
    df['fast_ema'] = df['close'].ewm(span=fast).mean()
    df['slow_ema'] = df['close'].ewm(span=slow).mean()
    df['trend'] = df['fast_ema'] > df['slow_ema']

    signals = []
    prev_trend = None
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['slow_ema']):
            prev_trend = row['trend'] if not pd.isna(row['trend']) else False
            continue

        current_trend = row['trend'] if not pd.isna(row['trend']) else False

        # 金叉买入
        if not in_position and not prev_trend and current_trend:
            sig = make_signal(symbol, str(row['date']), 1, 0.75, 0.08, 0.04)
            signals.append(sig)
            in_position = True
        # 死叉卖出
        elif in_position and prev_trend and not current_trend:
            sig = make_signal(symbol, str(row['date']), -1, 0.75, -0.03, 0.04)
            signals.append(sig)
            in_position = False

        prev_trend = current_trend

    return signals


def tmpl_trend_following_ma(symbol, df, params):
    """双均线趋势跟踪: 价格站上均线买入, 跌破卖出."""
    fast = int(params.get('fast', 10))
    slow = int(params.get('slow', 50))

    df = df.copy()
    df['fast_ma'] = df['close'].rolling(fast).mean()
    df['slow_ma'] = df['close'].rolling(slow).mean()

    signals = []
    in_position = False

    for i in range(slow + 1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]

        # 价格上穿双均线 = 买入
        if not in_position and prev['close'] <= prev['fast_ma'] and row['close'] > row['fast_ma'] and row['close'] > row['slow_ma']:
            sig = make_signal(symbol, str(row['date']), 1, 0.75, 0.08, 0.04)
            signals.append(sig)
            in_position = True
        # 价格跌破快均线 = 卖出
        elif in_position and prev['close'] >= prev['fast_ma'] and row['close'] < row['fast_ma']:
            sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.03, 0.04)
            signals.append(sig)
            in_position = False

    return signals


def tmpl_trend_following_channel(symbol, df, params):
    """通道突破趋势跟踪: 突破N日高点买入, 跌破N日低点卖出.

    海龟交易法则简化版.
    """
    entry_period = int(params.get('entry_period', 20))
    exit_period = int(params.get('exit_period', 10))

    df = df.copy()
    df['entry_high'] = df['high'].rolling(entry_period).max().shift(1)
    df['entry_low'] = df['low'].rolling(entry_period).min().shift(1)
    df['exit_high'] = df['high'].rolling(exit_period).max().shift(1)
    df['exit_low'] = df['low'].rolling(exit_period).min().shift(1)

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['entry_high']):
            continue

        if not in_position:
            if row['close'] > row['entry_high']:
                sig = make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04)
                signals.append(sig)
                in_position = True
        else:
            if row['close'] < row['exit_low']:
                sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.03, 0.04)
                signals.append(sig)
                in_position = False

    return signals


# ── 2. 动量策略 ──

def tmpl_momentum_12m(symbol, df, params):
    """12个月动量: 过去N天涨幅最大时买入.

    动量效应在A股存在, 牛市特别有效.
    """
    lookback = int(params.get('lookback', 60))
    hold_days = int(params.get('hold_days', 20))

    df = df.copy()
    df['momentum'] = df['close'].pct_change(lookback)
    df['momentum_ma'] = df['momentum'].rolling(20).mean()

    signals = []
    in_position = False
    entry_idx = 0

    for i in range(lookback + 20, len(df)):
        row = df.iloc[i]

        if not in_position:
            # 动量由负转正 = 趋势启动
            if df['momentum'].iloc[i-1] < 0 and row['momentum'] > 0:
                sig = make_signal(symbol, str(row['date']), 1, 0.7, 0.08, 0.04)
                signals.append(sig)
                in_position = True
                entry_idx = i
        else:
            # 持有N天后卖出 或 动量转负
            if i - entry_idx >= hold_days or row['momentum'] < -0.05:
                sig = make_signal(symbol, str(row['date']), -1, 0.6, -0.03, 0.04)
                signals.append(sig)
                in_position = False

    return signals


def tmpl_momentum_20d(symbol, df, params):
    """20日动量: 短期动量策略."""
    lookback = int(params.get('lookback', 20))
    threshold = float(params.get('threshold', 0.05))

    df = df.copy()
    df['mom'] = df['close'].pct_change(lookback)

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['mom']):
            continue

        if not in_position and row['mom'] > threshold:
            sig = make_signal(symbol, str(row['date']), 1, 0.7, 0.06, 0.04)
            signals.append(sig)
            in_position = True
        elif in_position and row['mom'] < -threshold:
            sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.03, 0.04)
            signals.append(sig)
            in_position = False

    return signals


# ── 3. 波动率调整策略 ──

def tmpl_volatility_targeting(symbol, df, params):
    """波动率目标: 低波动时满仓, 高波动时空仓.

    牛市波动率低->满仓跟涨, 熊市波动率高->空仓避险.
    """
    vol_window = int(params.get('vol_window', 20))
    vol_lookback = int(params.get('vol_lookback', 60))
    target_vol = float(params.get('target_vol', 0.15))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['vol'] = df['returns'].rolling(vol_window).std() * np.sqrt(252)
    df['vol_ma'] = df['vol'].rolling(vol_lookback).mean()

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['vol_ma']):
            continue

        # 波动率低于均值 = 市场环境好, 买入
        if not in_position and row['vol'] < row['vol_ma'] * 0.9:
            sig = make_signal(symbol, str(row['date']), 1, 0.7, 0.06, 0.03)
            signals.append(sig)
            in_position = True
        # 波动率高于均值 = 风险大, 卖出
        elif in_position and row['vol'] > row['vol_ma'] * 1.1:
            sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


# ── 4. 多时间框架趋势 ──

def tmpl_multi_tf_trend(symbol, df, params):
    """多时间框架趋势确认: 日线+周线趋势同向才交易.

    减少假信号, 提高胜率.
    """
    short_window = int(params.get('short_window', 10))
    mid_window = int(params.get('mid_window', 30))
    long_window = int(params.get('long_window', 60))

    df = df.copy()
    df['short_ma'] = df['close'].rolling(short_window).mean()
    df['mid_ma'] = df['close'].rolling(mid_window).mean()
    df['long_ma'] = df['close'].rolling(long_window).mean()

    df['short_up'] = df['close'] > df['short_ma']
    df['mid_up'] = df['close'] > df['mid_ma']
    df['long_up'] = df['close'] > df['long_ma']

    signals = []
    in_position = False

    for i in range(long_window + 1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]

        # 三均线同时向上 = 强趋势买入
        if not in_position and row['short_up'] and row['mid_up'] and row['long_up']:
            if not (prev['short_up'] and prev['mid_up'] and prev['long_up']):
                sig = make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.03)
                signals.append(sig)
                in_position = True
        # 任一均线跌破 = 卖出
        elif in_position and (not row['short_up'] or not row['mid_up']):
            sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


# ── 5. 突破策略 ──

def tmpl_breakout_with_volume(symbol, df, params):
    """放量突破: 突破前高+放量确认.

    有效突破往往伴随放量, 提高胜率.
    """
    lookback = int(params.get('lookback', 60))
    vol_mult = float(params.get('vol_mult', 2.0))

    df = df.copy()
    df['high_n'] = df['high'].rolling(lookback).max().shift(1)
    df['low_n'] = df['low'].rolling(lookback).min().shift(1)
    df['vol_ma'] = df['volume'].rolling(20).mean()

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['high_n']):
            continue

        if not in_position:
            # 放量突破前高
            if row['close'] > row['high_n'] and row['volume'] > row['vol_ma'] * vol_mult:
                sig = make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04)
                signals.append(sig)
                in_position = True
        else:
            # 跌破前低或缩量 = 卖出
            if row['close'] < row['low_n'] or row['volume'] < row['vol_ma'] * 0.8:
                sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.03, 0.04)
                signals.append(sig)
                in_position = False

    return signals


# ── 6. 相对强弱策略 ──

def tmpl_relative_strength_momentum(symbol, df, params):
    """相对强弱动量: 个股相对自身均线的强弱.

    强于均线时买入, 弱于均线时卖出.
    """
    rs_window = int(params.get('rs_window', 60))
    ma_window = int(params.get('ma_window', 20))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['cumulative'] = (1 + df['returns']).cumprod()
    # 用均线模拟大盘趋势
    df['market_proxy'] = df['close'].rolling(rs_window).mean()
    df['market_returns'] = df['market_proxy'].pct_change()
    df['rs'] = df['returns'] - df['market_returns']
    df['rs_ma'] = df['rs'].rolling(ma_window).mean()

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['rs_ma']):
            continue

        if not in_position and row['rs_ma'] > 0.001:  # 强于大盘
            sig = make_signal(symbol, str(row['date']), 1, 0.7, 0.06, 0.04)
            signals.append(sig)
            in_position = True
        elif in_position and row['rs_ma'] < -0.001:  # 弱于大盘
            sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.03, 0.04)
            signals.append(sig)
            in_position = False

    return signals


# ── 7. 简单择时策略 ──

def tmpl_simple_timing(symbol, df, params):
    """简单择时: 价格在60日均线上买入, 跌破卖出.

    最简单但长期有效的策略.
    """
    ma_period = int(params.get('ma_period', 60))

    df = df.copy()
    df['ma'] = df['close'].rolling(ma_period).mean()

    signals = []
    in_position = False

    for i in range(ma_period + 1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]

        if not in_position and prev['close'] <= prev['ma'] and row['close'] > row['ma']:
            sig = make_signal(symbol, str(row['date']), 1, 0.75, 0.07, 0.04)
            signals.append(sig)
            in_position = True
        elif in_position and prev['close'] >= prev['ma'] and row['close'] < row['ma']:
            sig = make_signal(symbol, str(row['date']), -1, 0.75, -0.03, 0.04)
            signals.append(sig)
            in_position = False

    return signals


def tmpl_simple_timing_30(symbol, df, params):
    """简单择时30日均线版."""
    ma_period = int(params.get('ma_period', 30))

    df = df.copy()
    df['ma'] = df['close'].rolling(ma_period).mean()

    signals = []
    in_position = False

    for i in range(ma_period + 1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]

        if not in_position and prev['close'] <= prev['ma'] and row['close'] > row['ma']:
            sig = make_signal(symbol, str(row['date']), 1, 0.75, 0.07, 0.04)
            signals.append(sig)
            in_position = True
        elif in_position and prev['close'] >= prev['ma'] and row['close'] < row['ma']:
            sig = make_signal(symbol, str(row['date']), -1, 0.75, -0.03, 0.04)
            signals.append(sig)
            in_position = False

    return signals


# ── 8. 复合策略 ──

def tmpl_trend_momentum_combo(symbol, df, params):
    """趋势+动量复合: 趋势确认+动量确认才买入.

    双重过滤, 提高胜率.
    """
    trend_window = int(params.get('trend_window', 50))
    mom_window = int(params.get('mom_window', 20))
    mom_threshold = float(params.get('mom_threshold', 0.03))

    df = df.copy()
    df['ma'] = df['close'].rolling(trend_window).mean()
    df['momentum'] = df['close'].pct_change(mom_window)

    signals = []
    in_position = False

    for i in range(trend_window + 1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]

        trend_up = row['close'] > row['ma']
        mom_positive = row['momentum'] > mom_threshold

        if not in_position and trend_up and mom_positive:
            if not (prev['close'] > prev['ma'] and df['momentum'].iloc[i-1] > mom_threshold):
                sig = make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.03)
                signals.append(sig)
                in_position = True
        elif in_position and (not trend_up or row['momentum'] < -mom_threshold):
            sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


def tmpl_rsi_trend_combo(symbol, df, params):
    """RSI+趋势复合: RSI超卖+趋势向上买入.

    抄底+趋势确认.
    """
    rsi_period = int(params.get('rsi_period', 14))
    trend_window = int(params.get('trend_window', 50))
    oversold = float(params.get('oversold', 30))
    overbought = float(params.get('overbought', 70))

    df = df.copy()
    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(rsi_period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # 趋势
    df['ma'] = df['close'].rolling(trend_window).mean()
    df['trend_up'] = df['close'] > df['ma']

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['rsi']):
            continue

        if not in_position and row['rsi'] < oversold and row['trend_up']:
            sig = make_signal(symbol, str(row['date']), 1, 0.75, 0.06, 0.03)
            signals.append(sig)
            in_position = True
        elif in_position and row['rsi'] > overbought:
            sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 策略池定义
# ═══════════════════════════════════════════════════════════════

STRATEGY_POOL = [
    # 趋势跟踪（核心）
    {"id": "trend_ema_12_26", "name": "EMA趋势跟踪(12,26)", "family": "趋势跟踪", "func": tmpl_trend_following_ema, "params": {"fast": 12, "slow": 26}},
    {"id": "trend_ema_10_30", "name": "EMA趋势跟踪(10,30)", "family": "趋势跟踪", "func": tmpl_trend_following_ema, "params": {"fast": 10, "slow": 30}},
    {"id": "trend_ema_5_20", "name": "EMA趋势跟踪(5,20)", "family": "趋势跟踪", "func": tmpl_trend_following_ema, "params": {"fast": 5, "slow": 20}},
    {"id": "trend_ma_10_50", "name": "双均线趋势(10,50)", "family": "趋势跟踪", "func": tmpl_trend_following_ma, "params": {"fast": 10, "slow": 50}},
    {"id": "trend_ma_20_60", "name": "双均线趋势(20,60)", "family": "趋势跟踪", "func": tmpl_trend_following_ma, "params": {"fast": 20, "slow": 60}},
    {"id": "trend_channel_20", "name": "通道突破(20日)", "family": "趋势跟踪", "func": tmpl_trend_following_channel, "params": {"entry_period": 20, "exit_period": 10}},
    {"id": "trend_channel_40", "name": "通道突破(40日)", "family": "趋势跟踪", "func": tmpl_trend_following_channel, "params": {"entry_period": 40, "exit_period": 20}},
    {"id": "trend_channel_60", "name": "通道突破(60日)", "family": "趋势跟踪", "func": tmpl_trend_following_channel, "params": {"entry_period": 60, "exit_period": 30}},

    # 动量策略
    {"id": "momentum_60d", "name": "60日动量", "family": "动量", "func": tmpl_momentum_12m, "params": {"lookback": 60, "hold_days": 20}},
    {"id": "momentum_40d", "name": "40日动量", "family": "动量", "func": tmpl_momentum_12m, "params": {"lookback": 40, "hold_days": 15}},
    {"id": "momentum_20d", "name": "20日动量", "family": "动量", "func": tmpl_momentum_20d, "params": {"lookback": 20, "threshold": 0.05}},
    {"id": "momentum_20d_v2", "name": "20日动量V2", "family": "动量", "func": tmpl_momentum_20d, "params": {"lookback": 20, "threshold": 0.03}},

    # 波动率调整
    {"id": "vol_target_20_60", "name": "波动率目标(20,60)", "family": "波动率", "func": tmpl_volatility_targeting, "params": {"vol_window": 20, "vol_lookback": 60, "target_vol": 0.15}},
    {"id": "vol_target_10_30", "name": "波动率目标(10,30)", "family": "波动率", "func": tmpl_volatility_targeting, "params": {"vol_window": 10, "vol_lookback": 30, "target_vol": 0.15}},

    # 多时间框架
    {"id": "multi_tf_10_30_60", "name": "多时间框架(10,30,60)", "family": "多时间框架", "func": tmpl_multi_tf_trend, "params": {"short_window": 10, "mid_window": 30, "long_window": 60}},
    {"id": "multi_tf_5_20_50", "name": "多时间框架(5,20,50)", "family": "多时间框架", "func": tmpl_multi_tf_trend, "params": {"short_window": 5, "mid_window": 20, "long_window": 50}},

    # 突破策略
    {"id": "breakout_vol_60", "name": "放量突破(60日)", "family": "突破", "func": tmpl_breakout_with_volume, "params": {"lookback": 60, "vol_mult": 2.0}},
    {"id": "breakout_vol_40", "name": "放量突破(40日)", "family": "突破", "func": tmpl_breakout_with_volume, "params": {"lookback": 40, "vol_mult": 1.8}},
    {"id": "breakout_vol_20", "name": "放量突破(20日)", "family": "突破", "func": tmpl_breakout_with_volume, "params": {"lookback": 20, "vol_mult": 2.5}},

    # 相对强弱
    {"id": "rs_momentum_60", "name": "相对强弱动量(60)", "family": "相对强弱", "func": tmpl_relative_strength_momentum, "params": {"rs_window": 60, "ma_window": 20}},
    {"id": "rs_momentum_40", "name": "相对强弱动量(40)", "family": "相对强弱", "func": tmpl_relative_strength_momentum, "params": {"rs_window": 40, "ma_window": 10}},

    # 简单择时
    {"id": "simple_timing_60", "name": "简单择时(60日)", "family": "择时", "func": tmpl_simple_timing, "params": {"ma_period": 60}},
    {"id": "simple_timing_30", "name": "简单择时(30日)", "family": "择时", "func": tmpl_simple_timing_30, "params": {"ma_period": 30}},
    {"id": "simple_timing_20", "name": "简单择时(20日)", "family": "择时", "func": tmpl_simple_timing_30, "params": {"ma_period": 20}},

    # 复合策略
    {"id": "trend_momentum_combo", "name": "趋势动量复合", "family": "复合", "func": tmpl_trend_momentum_combo, "params": {"trend_window": 50, "mom_window": 20, "mom_threshold": 0.03}},
    {"id": "trend_momentum_combo_v2", "name": "趋势动量复合V2", "family": "复合", "func": tmpl_trend_momentum_combo, "params": {"trend_window": 30, "mom_window": 10, "mom_threshold": 0.02}},
    {"id": "rsi_trend_combo", "name": "RSI趋势复合", "family": "复合", "func": tmpl_rsi_trend_combo, "params": {"rsi_period": 14, "trend_window": 50, "oversold": 30, "overbought": 70}},
    {"id": "rsi_trend_combo_v2", "name": "RSI趋势复合V2", "family": "复合", "func": tmpl_rsi_trend_combo, "params": {"rsi_period": 10, "trend_window": 30, "oversold": 25, "overbought": 75}},
]


def discover_strategies_v3(target_count: int = 35, verbose: bool = True) -> list[dict]:
    """策略发现主函数V3."""
    if verbose:
        print(f"[DiscoveryV3] 开始策略发现，目标: {target_count}个高质量策略")
        print(f"[DiscoveryV3] 策略池大小: {len(STRATEGY_POOL)}")
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
                print(f"\n[DiscoveryV3] 已达到目标数量 {target_count}，提前终止")
            break

    if verbose:
        print("\n" + "=" * 80)
        print(f"[DiscoveryV3] 完成: {len(passed)}个通过, {len(failed)}个失败")
        if len(passed) < target_count:
            print(f"[DiscoveryV3] 警告: 未达到目标数量，还需 {target_count - len(passed)} 个策略")

    return passed


if __name__ == "__main__":
    passed = discover_strategies_v3(target_count=35, verbose=True)
    print(f"\n最终通过策略数: {len(passed)}")
    for p in passed:
        print(f"  - {p['name']} ({p['family']})")

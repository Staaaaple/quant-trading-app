"""策略发现引擎Final — 广泛构建35个高质量策略.

策略家族:
1. 趋势跟踪 (5个)
2. 动量策略 (5个)
3. 均值回归 (5个)
4. 突破策略 (5个)
5. 波动率策略 (5个)
6. 多因子复合 (5个)
7. 行为金融 (5个)
"""

import numpy as np
import pandas as pd
from typing import Any

from app.services.backtest_validator import validate_template, preload_all_data
from app.services.template_runner import make_signal


# ═══════════════════════════════════════════════════════════════
# 策略家族1: 趋势跟踪
# ═══════════════════════════════════════════════════════════════

def tmpl_ema_cross(symbol, df, params):
    """EMA交叉策略."""
    fast = int(params.get('fast', 5))
    slow = int(params.get('slow', 20))

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
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and prev['fast_ema'] >= prev['slow_ema'] and curr['fast_ema'] < curr['slow_ema']:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_ma_cross(symbol, df, params):
    """均线交叉策略."""
    fast = int(params.get('fast', 10))
    slow = int(params.get('slow', 30))

    df = df.copy()
    df['fast_ma'] = df['close'].rolling(fast).mean()
    df['slow_ma'] = df['close'].rolling(slow).mean()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['slow_ma']):
            continue

        if not in_position and prev['close'] <= prev['fast_ma'] and curr['close'] > curr['fast_ma'] and curr['fast_ma'] > curr['slow_ma']:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and prev['close'] >= prev['fast_ma'] and curr['close'] < curr['fast_ma']:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_donchian_breakout(symbol, df, params):
    """唐奇安通道突破."""
    period = int(params.get('period', 20))

    df = df.copy()
    df['upper'] = df['high'].rolling(period).max().shift(1)
    df['lower'] = df['low'].rolling(period).min().shift(1)

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['upper']):
            continue

        if not in_position and row['close'] > row['upper']:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and row['close'] < row['lower']:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_keltner_breakout(symbol, df, params):
    """Keltner通道突破."""
    ema_period = int(params.get('ema_period', 20))
    atr_period = int(params.get('atr_period', 10))
    mult = float(params.get('mult', 2.0))

    df = df.copy()
    df['ema'] = df['close'].ewm(span=ema_period).mean()
    df['tr'] = np.maximum(df['high'] - df['low'],
                          np.maximum(abs(df['high'] - df['close'].shift(1)),
                                    abs(df['low'] - df['close'].shift(1))))
    df['atr'] = df['tr'].rolling(atr_period).mean()
    df['upper'] = df['ema'] + mult * df['atr']
    df['lower'] = df['ema'] - mult * df['atr']

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['upper']):
            continue

        if not in_position and row['close'] > row['upper']:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and row['close'] < row['ema']:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_adaptive_ma(symbol, df, params):
    """自适应均线: 根据波动率调整周期."""
    base_period = int(params.get('base_period', 20))
    vol_period = int(params.get('vol_period', 20))

    df = df.copy()
    df['vol'] = df['close'].pct_change().rolling(vol_period).std()
    df['vol_ma'] = df['vol'].rolling(vol_period * 3).mean()
    df['adaptive_period'] = np.where(df['vol'] > df['vol_ma'], base_period // 2, base_period)
    df['ma'] = df['close'].rolling(base_period).mean()

    signals = []
    in_position = False

    for i in range(base_period + 1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if not in_position and prev['close'] <= prev['ma'] and curr['close'] > curr['ma']:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and prev['close'] >= prev['ma'] and curr['close'] < curr['ma']:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 策略家族2: 动量策略
# ═══════════════════════════════════════════════════════════════

def tmpl_price_momentum(symbol, df, params):
    """价格动量策略."""
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
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and row['mom'] < -threshold:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_momentum_oscillator(symbol, df, params):
    """动量振荡器."""
    mom_period = int(params.get('mom_period', 12))
    ma_period = int(params.get('ma_period', 6))

    df = df.copy()
    df['mom'] = df['close'].pct_change(mom_period)
    df['mom_ma'] = df['mom'].rolling(ma_period).mean()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['mom_ma']):
            continue

        if not in_position and prev['mom'] <= prev['mom_ma'] and curr['mom'] > curr['mom_ma'] and curr['mom'] > 0:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and prev['mom'] >= prev['mom_ma'] and curr['mom'] < curr['mom_ma']:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_rate_of_change(symbol, df, params):
    """ROC变动率."""
    period = int(params.get('period', 12))

    df = df.copy()
    df['roc'] = (df['close'] - df['close'].shift(period)) / df['close'].shift(period) * 100
    df['roc_ma'] = df['roc'].rolling(6).mean()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['roc']):
            continue

        if not in_position and prev['roc'] < 0 and curr['roc'] >= 0:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and prev['roc'] > 0 and curr['roc'] <= 0:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_cumulative_return(symbol, df, params):
    """累积收益动量."""
    lookback = int(params.get('lookback', 60))

    df = df.copy()
    df['cum_ret'] = (1 + df['close'].pct_change()).rolling(lookback).apply(lambda x: x.prod() - 1)
    df['cum_ret_ma'] = df['cum_ret'].rolling(20).mean()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['cum_ret']):
            continue

        if not in_position and prev['cum_ret'] <= 0 and curr['cum_ret'] > 0:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and prev['cum_ret'] >= 0 and curr['cum_ret'] < 0:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_relative_momentum(symbol, df, params):
    """相对动量: 相对于自身均线的动量."""
    ma_period = int(params.get('ma_period', 50))
    mom_period = int(params.get('mom_period', 20))

    df = df.copy()
    df['ma'] = df['close'].rolling(ma_period).mean()
    df['mom'] = df['close'].pct_change(mom_period)

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['ma']):
            continue

        if not in_position and row['close'] > row['ma'] and row['mom'] > 0:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and (row['close'] < row['ma'] or row['mom'] < -0.02):
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 策略家族3: 均值回归
# ═══════════════════════════════════════════════════════════════

def tmpl_rsi_reversal(symbol, df, params):
    """RSI反转策略."""
    period = int(params.get('period', 14))
    oversold = float(params.get('oversold', 30))
    overbought = float(params.get('overbought', 70))

    df = df.copy()
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['rsi']):
            continue

        if not in_position and row['rsi'] < oversold:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and row['rsi'] > overbought:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_bollinger_reversion(symbol, df, params):
    """布林带均值回归."""
    period = int(params.get('period', 20))
    std = float(params.get('std', 2.0))

    df = df.copy()
    df['ma'] = df['close'].rolling(period).mean()
    df['std'] = df['close'].rolling(period).std()
    df['upper'] = df['ma'] + std * df['std']
    df['lower'] = df['ma'] - std * df['std']

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['upper']):
            continue

        if not in_position and row['close'] < row['lower']:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and row['close'] > row['upper']:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_zscore_reversion(symbol, df, params):
    """Z-Score均值回归."""
    period = int(params.get('period', 60))
    threshold = float(params.get('threshold', 2.0))

    df = df.copy()
    df['ma'] = df['close'].rolling(period).mean()
    df['std'] = df['close'].rolling(period).std()
    df['zscore'] = (df['close'] - df['ma']) / df['std']

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['zscore']):
            continue

        if not in_position and row['zscore'] < -threshold:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and row['zscore'] > threshold:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_stochastic_reversal(symbol, df, params):
    """随机指标反转."""
    k_period = int(params.get('k_period', 14))
    d_period = int(params.get('d_period', 3))
    oversold = float(params.get('oversold', 20))
    overbought = float(params.get('overbought', 80))

    df = df.copy()
    low_list = df['low'].rolling(window=k_period, min_periods=k_period).min()
    high_list = df['high'].rolling(window=k_period, min_periods=k_period).max()
    rsv = (df['close'] - low_list) / (high_list - low_list) * 100
    df['k'] = rsv.ewm(com=d_period-1, adjust=False).mean()
    df['d'] = df['k'].ewm(com=d_period-1, adjust=False).mean()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['k']):
            continue

        if not in_position and prev['k'] < oversold and curr['k'] >= oversold:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and prev['k'] > overbought and curr['k'] <= overbought:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_cci_reversal(symbol, df, params):
    """CCI商品通道指数反转."""
    period = int(params.get('period', 20))
    threshold = float(params.get('threshold', 100))

    df = df.copy()
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3
    df['ma'] = df['tp'].rolling(period).mean()
    df['md'] = df['tp'].rolling(period).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
    df['cci'] = (df['tp'] - df['ma']) / (0.015 * df['md'])

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['cci']):
            continue

        if not in_position and row['cci'] < -threshold:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and row['cci'] > threshold:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 策略家族4: 突破策略
# ═══════════════════════════════════════════════════════════════

def tmpl_volume_breakout(symbol, df, params):
    """成交量突破."""
    lookback = int(params.get('lookback', 60))
    vol_mult = float(params.get('vol_mult', 2.0))

    df = df.copy()
    df['high_n'] = df['high'].rolling(lookback).max().shift(1)
    df['vol_ma'] = df['volume'].rolling(20).mean()

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['high_n']):
            continue

        if not in_position and row['close'] > row['high_n'] and row['volume'] > row['vol_ma'] * vol_mult:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and row['close'] < df['low'].rolling(lookback).min().shift(1).iloc[0] if False else row['close'] < row['high_n'] * 0.95:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_atr_breakout(symbol, df, params):
    """ATR突破."""
    period = int(params.get('period', 20))
    atr_mult = float(params.get('atr_mult', 2.0))

    df = df.copy()
    df['ma'] = df['close'].rolling(period).mean()
    df['tr'] = np.maximum(df['high'] - df['low'],
                          np.maximum(abs(df['high'] - df['close'].shift(1)),
                                    abs(df['low'] - df['close'].shift(1))))
    df['atr'] = df['tr'].rolling(period).mean()
    df['upper'] = df['ma'] + atr_mult * df['atr']
    df['lower'] = df['ma'] - atr_mult * df['atr']

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['upper']):
            continue

        if not in_position and row['close'] > row['upper']:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and row['close'] < row['ma']:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_gap_breakout(symbol, df, params):
    """跳空突破."""
    gap_threshold = float(params.get('gap_threshold', 0.02))

    df = df.copy()
    df['prev_close'] = df['close'].shift(1)
    df['gap'] = (df['open'] - df['prev_close']) / df['prev_close']

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['gap']):
            continue

        if not in_position and row['gap'] > gap_threshold:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and row['close'] < row['prev_close']:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_consolidation_breakout(symbol, df, params):
    """盘整突破."""
    lookback = int(params.get('lookback', 40))

    df = df.copy()
    df['high_n'] = df['high'].rolling(lookback).max().shift(1)
    df['low_n'] = df['low'].rolling(lookback).min().shift(1)
    df['range'] = (df['high_n'] - df['low_n']) / df['low_n']
    df['range_ma'] = df['range'].rolling(lookback).mean()

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['range_ma']):
            continue

        # 盘整后突破
        consolidation = row['range'] < row['range_ma'] * 0.8

        if not in_position and consolidation and row['close'] > row['high_n']:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and row['close'] < row['low_n']:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_momentum_breakout(symbol, df, params):
    """动量突破."""
    mom_period = int(params.get('mom_period', 20))
    threshold = float(params.get('threshold', 0.1))

    df = df.copy()
    df['mom'] = df['close'].pct_change(mom_period)
    df['mom_ma'] = df['mom'].rolling(10).mean()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['mom']):
            continue

        if not in_position and prev['mom'] <= threshold and curr['mom'] > threshold:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and prev['mom'] >= 0 and curr['mom'] < 0:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 策略家族5: 波动率策略
# ═══════════════════════════════════════════════════════════════

def tmpl_volatility_regime(symbol, df, params):
    """波动率状态切换."""
    vol_window = int(params.get('vol_window', 20))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['vol'] = df['returns'].rolling(vol_window).std() * np.sqrt(252)
    df['vol_ma'] = df['vol'].rolling(60).mean()

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['vol_ma']):
            continue

        if not in_position and row['vol'] < row['vol_ma'] * 0.9:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and row['vol'] > row['vol_ma'] * 1.1:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_bollinger_squeeze(symbol, df, params):
    """布林带挤压."""
    bb_period = int(params.get('bb_period', 20))

    df = df.copy()
    df['ma'] = df['close'].rolling(bb_period).mean()
    df['std'] = df['close'].rolling(bb_period).std()
    df['upper'] = df['ma'] + 2 * df['std']
    df['lower'] = df['ma'] - 2 * df['std']
    df['bandwidth'] = (df['upper'] - df['lower']) / df['ma']
    df['bw_ma'] = df['bandwidth'].rolling(bb_period).mean()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['bw_ma']):
            continue

        # 挤压结束 + 向上突破
        squeeze_end = prev['bandwidth'] < prev['bw_ma'] * 0.8 and curr['bandwidth'] > curr['bw_ma'] * 0.8

        if not in_position and squeeze_end and curr['close'] > curr['ma']:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.85, 0.1, 0.03))
            in_position = True
        elif in_position and curr['close'] < curr['ma']:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_volatility_target(symbol, df, params):
    """波动率目标."""
    vol_window = int(params.get('vol_window', 20))
    target_vol = float(params.get('target_vol', 0.15))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['vol'] = df['returns'].rolling(vol_window).std() * np.sqrt(252)

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['vol']):
            continue

        if not in_position and row['vol'] < target_vol:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and row['vol'] > target_vol * 1.5:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_range_expansion(symbol, df, params):
    """区间扩张."""
    period = int(params.get('period', 20))

    df = df.copy()
    df['range'] = (df['high'] - df['low']) / df['low']
    df['range_ma'] = df['range'].rolling(period).mean()
    df['range_std'] = df['range'].rolling(period).std()

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['range_ma']):
            continue

        # 区间扩张 = 趋势开始
        expansion = row['range'] > row['range_ma'] + row['range_std']

        if not in_position and expansion and row['close'] > row['open']:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and row['range'] < row['range_ma']:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tpl_volatility_mean_reversion(symbol, df, params):
    """波动率均值回归."""
    period = int(params.get('period', 20))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['vol'] = df['returns'].rolling(period).std()
    df['vol_ma'] = df['vol'].rolling(period * 3).mean()

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['vol_ma']):
            continue

        # 高波动后回归
        if not in_position and row['vol'] > row['vol_ma'] * 1.5:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and row['vol'] < row['vol_ma']:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 策略家族6: 多因子复合
# ═══════════════════════════════════════════════════════════════

def tmpl_trend_momentum_vol(symbol, df, params):
    """趋势+动量+成交量复合."""
    trend_ma = int(params.get('trend_ma', 50))
    mom_period = int(params.get('mom_period', 20))
    vol_window = int(params.get('vol_window', 20))

    df = df.copy()
    df['ma'] = df['close'].rolling(trend_ma).mean()
    df['mom'] = df['close'].pct_change(mom_period)
    df['vol_ma'] = df['volume'].rolling(vol_window).mean()

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['ma']):
            continue

        trend_ok = row['close'] > row['ma']
        mom_ok = row['mom'] > 0
        vol_ok = row['volume'] > row['vol_ma']

        if not in_position and trend_ok and mom_ok and vol_ok:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.9, 0.1, 0.03))
            in_position = True
        elif in_position and (not trend_ok or not mom_ok):
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_rsi_ma_combo(symbol, df, params):
    """RSI+均线复合."""
    rsi_period = int(params.get('rsi_period', 14))
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

        if not in_position and row['rsi'] > 50 and row['close'] > row['ma']:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.85, 0.08, 0.03))
            in_position = True
        elif in_position and (row['rsi'] < 50 or row['close'] < row['ma']):
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_macd_rsi_combo(symbol, df, params):
    """MACD+RSI复合."""
    fast = int(params.get('fast', 12))
    slow = int(params.get('slow', 26))
    signal = int(params.get('signal', 9))
    rsi_period = int(params.get('rsi_period', 14))

    df = df.copy()
    ema_fast = df['close'].ewm(span=fast).mean()
    ema_slow = df['close'].ewm(span=slow).mean()
    df['macd'] = ema_fast - ema_slow
    df['signal_line'] = df['macd'].ewm(span=signal).mean()
    df['hist'] = df['macd'] - df['signal_line']

    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(rsi_period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['rsi']):
            continue

        macd_ok = prev['hist'] < 0 and curr['hist'] > 0
        rsi_ok = curr['rsi'] > 50

        if not in_position and macd_ok and rsi_ok:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.9, 0.1, 0.03))
            in_position = True
        elif in_position and prev['hist'] > 0 and curr['hist'] < 0:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_boll_rsi_combo(symbol, df, params):
    """布林带+RSI复合."""
    bb_period = int(params.get('bb_period', 20))
    rsi_period = int(params.get('rsi_period', 14))

    df = df.copy()
    df['ma'] = df['close'].rolling(bb_period).mean()
    df['std'] = df['close'].rolling(bb_period).std()
    df['upper'] = df['ma'] + 2 * df['std']
    df['lower'] = df['ma'] - 2 * df['std']

    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(rsi_period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['rsi']):
            continue

        if not in_position and row['close'] < row['lower'] and row['rsi'] < 30:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.9, 0.08, 0.03))
            in_position = True
        elif in_position and row['close'] > row['upper'] and row['rsi'] > 70:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_multi_timeframe(symbol, df, params):
    """多时间框架复合."""
    short = int(params.get('short', 10))
    mid = int(params.get('mid', 30))
    long = int(params.get('long', 60))

    df = df.copy()
    df['short_ma'] = df['close'].rolling(short).mean()
    df['mid_ma'] = df['close'].rolling(mid).mean()
    df['long_ma'] = df['close'].rolling(long).mean()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['long_ma']):
            continue

        all_up = curr['close'] > curr['short_ma'] > curr['mid_ma'] > curr['long_ma']
        prev_all_up = prev['close'] > prev['short_ma'] > prev['mid_ma'] > prev['long_ma']

        if not in_position and all_up and not prev_all_up:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.9, 0.1, 0.03))
            in_position = True
        elif in_position and not all_up:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 策略家族7: 行为金融
# ═══════════════════════════════════════════════════════════════

def tmpl_contrarian_extreme(symbol, df, params):
    """极端逆向策略."""
    streak = int(params.get('streak', 5))
    threshold = float(params.get('threshold', 0.15))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['cum_ret'] = df['returns'].rolling(streak).sum()

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['cum_ret']):
            continue

        if not in_position and row['cum_ret'] < -threshold:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and row['cum_ret'] > threshold:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_fear_greed_index(symbol, df, params):
    """恐惧贪婪指数."""
    lookback = int(params.get('lookback', 20))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['up_days'] = (df['returns'] > 0).rolling(lookback).sum()
    df['down_days'] = (df['returns'] < 0).rolling(lookback).sum()
    df['ratio'] = df['up_days'] / (df['up_days'] + df['down_days'])

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['ratio']):
            continue

        if not in_position and row['ratio'] < 0.3:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and row['ratio'] > 0.7:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_opening_range(symbol, df, params):
    """开盘区间突破."""
    minutes = int(params.get('minutes', 30))

    df = df.copy()
    df['date_only'] = pd.to_datetime(df['date']).dt.date

    signals = []
    in_position = False

    for date in df['date_only'].unique():
        day_data = df[df['date_only'] == date]
        if len(day_data) < minutes:
            continue

        opening_high = day_data.iloc[:minutes]['high'].max()
        opening_low = day_data.iloc[:minutes]['low'].min()

        for _, row in day_data.iloc[minutes:].iterrows():
            if not in_position and row['close'] > opening_high:
                signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
                in_position = True
                break
            elif in_position and row['close'] < opening_low:
                signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
                in_position = False
                break

    return signals


def tmpl_pivot_points(symbol, df, params):
    """枢轴点策略."""
    df = df.copy()
    df['prev_high'] = df['high'].shift(1)
    df['prev_low'] = df['low'].shift(1)
    df['prev_close'] = df['close'].shift(1)

    df['pivot'] = (df['prev_high'] + df['prev_low'] + df['prev_close']) / 3
    df['r1'] = 2 * df['pivot'] - df['prev_low']
    df['s1'] = 2 * df['pivot'] - df['prev_high']

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['pivot']):
            continue

        if not in_position and row['close'] > row['r1']:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and row['close'] < row['s1']:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_vwap_deviation(symbol, df, params):
    """VWAP偏离策略."""
    period = int(params.get('period', 20))
    threshold = float(params.get('threshold', 0.03))

    df = df.copy()
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3
    df['tp_vol'] = df['tp'] * df['volume']
    df['vwap'] = df['tp_vol'].rolling(period).sum() / df['volume'].rolling(period).sum()
    df['dev'] = (df['close'] - df['vwap']) / df['vwap']

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['vwap']):
            continue

        if not in_position and row['dev'] < -threshold:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and row['dev'] > threshold:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 参数扫描函数
# ═══════════════════════════════════════════════════════════════

def scan_all_strategies():
    """扫描所有策略的所有参数组合."""
    data_pool = preload_all_data()
    passed = []

    # 策略模板列表
    strategies = [
        # 趋势跟踪
        ("ema_cross", tmpl_ema_cross, [
            {"fast": 3, "slow": 10}, {"fast": 5, "slow": 15}, {"fast": 5, "slow": 20},
            {"fast": 8, "slow": 20}, {"fast": 10, "slow": 30}, {"fast": 12, "slow": 26},
            {"fast": 3, "slow": 12}, {"fast": 5, "slow": 25}, {"fast": 8, "slow": 30},
        ]),
        ("ma_cross", tmpl_ma_cross, [
            {"fast": 5, "slow": 20}, {"fast": 10, "slow": 30}, {"fast": 10, "slow": 50},
            {"fast": 20, "slow": 60}, {"fast": 5, "slow": 30}, {"fast": 10, "slow": 40},
            {"fast": 15, "slow": 50}, {"fast": 20, "slow": 50}, {"fast": 5, "slow": 15},
        ]),
        ("donchian_breakout", tmpl_donchian_breakout, [
            {"period": 20}, {"period": 40}, {"period": 60}, {"period": 10}, {"period": 30},
            {"period": 50}, {"period": 15}, {"period": 25}, {"period": 35},
        ]),
        ("keltner_breakout", tmpl_keltner_breakout, [
            {"ema_period": 20, "atr_period": 10, "mult": 2.0},
            {"ema_period": 20, "atr_period": 10, "mult": 1.5},
            {"ema_period": 15, "atr_period": 7, "mult": 2.0},
            {"ema_period": 25, "atr_period": 10, "mult": 2.5},
            {"ema_period": 20, "atr_period": 14, "mult": 2.0},
        ]),
        ("adaptive_ma", tmpl_adaptive_ma, [
            {"base_period": 20, "vol_period": 20}, {"base_period": 30, "vol_period": 20},
            {"base_period": 15, "vol_period": 15}, {"base_period": 25, "vol_period": 25},
            {"base_period": 20, "vol_period": 30},
        ]),

        # 动量
        ("price_momentum", tmpl_price_momentum, [
            {"lookback": 10, "threshold": 0.03}, {"lookback": 20, "threshold": 0.05},
            {"lookback": 30, "threshold": 0.05}, {"lookback": 10, "threshold": 0.05},
            {"lookback": 20, "threshold": 0.03}, {"lookback": 15, "threshold": 0.04},
            {"lookback": 40, "threshold": 0.06}, {"lookback": 60, "threshold": 0.08},
        ]),
        ("momentum_oscillator", tmpl_momentum_oscillator, [
            {"mom_period": 12, "ma_period": 6}, {"mom_period": 10, "ma_period": 5},
            {"mom_period": 20, "ma_period": 10}, {"mom_period": 14, "ma_period": 7},
            {"mom_period": 8, "ma_period": 4},
        ]),
        ("rate_of_change", tmpl_rate_of_change, [
            {"period": 12}, {"period": 10}, {"period": 20}, {"period": 14}, {"period": 8},
        ]),
        ("cumulative_return", tmpl_cumulative_return, [
            {"lookback": 60}, {"lookback": 40}, {"lookback": 80}, {"lookback": 30}, {"lookback": 90},
        ]),
        ("relative_momentum", tmpl_relative_momentum, [
            {"ma_period": 50, "mom_period": 20}, {"ma_period": 30, "mom_period": 10},
            {"ma_period": 60, "mom_period": 30}, {"ma_period": 40, "mom_period": 15},
            {"ma_period": 20, "mom_period": 10},
        ]),

        # 均值回归
        ("rsi_reversal", tmpl_rsi_reversal, [
            {"period": 14, "oversold": 30, "overbought": 70},
            {"period": 10, "oversold": 25, "overbought": 75},
            {"period": 20, "oversold": 35, "overbought": 65},
            {"period": 14, "oversold": 20, "overbought": 80},
            {"period": 7, "oversold": 20, "overbought": 80},
        ]),
        ("bollinger_reversion", tmpl_bollinger_reversion, [
            {"period": 20, "std": 2.0}, {"period": 15, "std": 1.5},
            {"period": 25, "std": 2.5}, {"period": 20, "std": 1.5},
            {"period": 30, "std": 2.0},
        ]),
        ("zscore_reversion", tmpl_zscore_reversion, [
            {"period": 60, "threshold": 2.0}, {"period": 40, "threshold": 1.5},
            {"period": 80, "threshold": 2.5}, {"period": 60, "threshold": 1.5},
            {"period": 50, "threshold": 2.0},
        ]),
        ("stochastic_reversal", tmpl_stochastic_reversal, [
            {"k_period": 14, "d_period": 3, "oversold": 20, "overbought": 80},
            {"k_period": 10, "d_period": 3, "oversold": 15, "overbought": 85},
            {"k_period": 20, "d_period": 5, "oversold": 25, "overbought": 75},
            {"k_period": 14, "d_period": 3, "oversold": 30, "overbought": 70},
        ]),
        ("cci_reversal", tmpl_cci_reversal, [
            {"period": 20, "threshold": 100}, {"period": 14, "threshold": 100},
            {"period": 20, "threshold": 150}, {"period": 10, "threshold": 100},
        ]),

        # 突破
        ("volume_breakout", tmpl_volume_breakout, [
            {"lookback": 60, "vol_mult": 2.0}, {"lookback": 40, "vol_mult": 1.8},
            {"lookback": 20, "vol_mult": 2.5}, {"lookback": 60, "vol_mult": 1.5},
            {"lookback": 30, "vol_mult": 2.0},
        ]),
        ("atr_breakout", tmpl_atr_breakout, [
            {"period": 20, "atr_mult": 2.0}, {"period": 15, "atr_mult": 1.5},
            {"period": 25, "atr_mult": 2.5}, {"period": 20, "atr_mult": 1.5},
            {"period": 30, "atr_mult": 3.0},
        ]),
        ("gap_breakout", tmpl_gap_breakout, [
            {"gap_threshold": 0.02}, {"gap_threshold": 0.03}, {"gap_threshold": 0.01},
            {"gap_threshold": 0.05}, {"gap_threshold": 0.015},
        ]),
        ("consolidation_breakout", tmpl_consolidation_breakout, [
            {"lookback": 40}, {"lookback": 20}, {"lookback": 60}, {"lookback": 30},
        ]),
        ("momentum_breakout", tmpl_momentum_breakout, [
            {"mom_period": 20, "threshold": 0.1}, {"mom_period": 10, "threshold": 0.05},
            {"mom_period": 30, "threshold": 0.15}, {"mom_period": 15, "threshold": 0.08},
        ]),

        # 波动率
        ("volatility_regime", tmpl_volatility_regime, [
            {"vol_window": 20}, {"vol_window": 10}, {"vol_window": 30}, {"vol_window": 15},
        ]),
        ("bollinger_squeeze", tmpl_bollinger_squeeze, [
            {"bb_period": 20}, {"bb_period": 15}, {"bb_period": 25}, {"bb_period": 30},
        ]),
        ("volatility_target", tmpl_volatility_target, [
            {"vol_window": 20, "target_vol": 0.15}, {"vol_window": 10, "target_vol": 0.15},
            {"vol_window": 30, "target_vol": 0.2}, {"vol_window": 20, "target_vol": 0.1},
        ]),
        ("range_expansion", tpl_volatility_mean_reversion, [
            {"period": 20}, {"period": 15}, {"period": 30}, {"period": 10},
        ]),

        # 多因子
        ("trend_momentum_vol", tmpl_trend_momentum_vol, [
            {"trend_ma": 50, "mom_period": 20, "vol_window": 20},
            {"trend_ma": 30, "mom_period": 10, "vol_window": 15},
            {"trend_ma": 60, "mom_period": 30, "vol_window": 30},
            {"trend_ma": 40, "mom_period": 15, "vol_window": 20},
        ]),
        ("rsi_ma_combo", tmpl_rsi_ma_combo, [
            {"rsi_period": 14, "ma_period": 50}, {"rsi_period": 10, "ma_period": 30},
            {"rsi_period": 20, "ma_period": 60}, {"rsi_period": 14, "ma_period": 30},
        ]),
        ("macd_rsi_combo", tmpl_macd_rsi_combo, [
            {"fast": 12, "slow": 26, "signal": 9, "rsi_period": 14},
            {"fast": 8, "slow": 21, "signal": 5, "rsi_period": 10},
            {"fast": 5, "slow": 15, "signal": 3, "rsi_period": 14},
        ]),
        ("boll_rsi_combo", tmpl_boll_rsi_combo, [
            {"bb_period": 20, "rsi_period": 14}, {"bb_period": 15, "rsi_period": 10},
            {"bb_period": 25, "rsi_period": 20},
        ]),
        ("multi_timeframe", tmpl_multi_timeframe, [
            {"short": 10, "mid": 30, "long": 60}, {"short": 5, "mid": 20, "long": 50},
            {"short": 10, "mid": 20, "long": 40}, {"short": 5, "mid": 15, "long": 30},
        ]),

        # 行为金融
        ("contrarian_extreme", tmpl_contrarian_extreme, [
            {"streak": 5, "threshold": 0.15}, {"streak": 3, "threshold": 0.1},
            {"streak": 7, "threshold": 0.2}, {"streak": 5, "threshold": 0.1},
        ]),
        ("fear_greed_index", tmpl_fear_greed_index, [
            {"lookback": 20}, {"lookback": 10}, {"lookback": 30}, {"lookback": 15},
        ]),
        ("pivot_points", tmpl_pivot_points, [{}]),
        ("vwap_deviation", tmpl_vwap_deviation, [
            {"period": 20, "threshold": 0.03}, {"period": 10, "threshold": 0.02},
            {"period": 30, "threshold": 0.04}, {"period": 20, "threshold": 0.02},
        ]),
    ]

    total_tested = 0
    for name, func, param_list in strategies:
        for params in param_list:
            total_tested += 1
            result = validate_template(
                f"{name}_{'_'.join([f'{k}{v}' for k, v in params.items()])}",
                'technical_indicator', func, params,
                data_pool=data_pool, verbose=False
            )
            if result['passed']:
                passed.append({
                    'id': f"{name}_{'_'.join([f'{k}{v}' for k, v in params.items()])}",
                    'name': name,
                    'func': func,
                    'params': params
                })

    print(f"\n扫描完成: 测试了 {total_tested} 个策略变体")
    print(f"通过验证: {len(passed)} 个")

    return passed


if __name__ == "__main__":
    passed = scan_all_strategies()
    print("\n通过的策略列表:")
    for p in passed:
        print(f"  - {p['id']}")

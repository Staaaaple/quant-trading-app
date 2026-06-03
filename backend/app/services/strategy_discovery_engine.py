"""策略发现引擎 — 系统性构建35个高质量策略.

核心设计原则:
1. 信号频率: 每个股票每年需要足够信号(>=3次)以通过交易次数检查
2. 信号质量: 每个信号后5天收益为正的概率 > 35%
3. 组合收益: 10只股票等权组合的年收益 > 沪深300基准
4. 回撤控制: 单只股票最大回撤 < 30%(或个股回撤+5%)

策略家族(7大类别,每类至少5个):
1. 趋势跟踪 — 跟随价格趋势
2. 动量策略 — 利用价格动量
3. 均值回归 — 价格偏离后回归
4. 突破策略 — 价格突破关键位
5. 波动率策略 — 基于波动率变化
6. 多因子复合 — 多条件叠加
7. 行为金融 — 利用市场非理性
"""

import numpy as np
import pandas as pd
from typing import Any

from app.services.backtest_validator import validate_template, preload_all_data
from app.services.template_runner import make_signal


# ═══════════════════════════════════════════════════════════════
# 策略家族1: 趋势跟踪 (Trend Following)
# ═══════════════════════════════════════════════════════════════

def tmpl_ema_cross(symbol, df, params):
    """EMA交叉: 快线上穿慢线买入,下穿卖出."""
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


def tmpl_ma_slope(symbol, df, params):
    """均线斜率: 均线向上斜率转正买入."""
    period = int(params.get('period', 20))
    slope_threshold = float(params.get('slope_threshold', 0.001))

    df = df.copy()
    df['ma'] = df['close'].rolling(period).mean()
    df['slope'] = df['ma'].diff() / df['ma'].shift(1)

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['slope']):
            continue

        if not in_position and prev['slope'] <= slope_threshold and curr['slope'] > slope_threshold:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and prev['slope'] >= -slope_threshold and curr['slope'] < -slope_threshold:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_price_above_ma(symbol, df, params):
    """价格在均线上方: 价格上穿均线买入,下穿卖出."""
    period = int(params.get('period', 20))

    df = df.copy()
    df['ma'] = df['close'].rolling(period).mean()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['ma']):
            continue

        if not in_position and prev['close'] <= prev['ma'] and curr['close'] > curr['ma']:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and prev['close'] >= prev['ma'] and curr['close'] < curr['ma']:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_higher_highs(symbol, df, params):
    """更高高点: 连续创出更高高点时买入."""
    lookback = int(params.get('lookback', 20))

    df = df.copy()
    df['high_n'] = df['high'].rolling(lookback).max()
    df['higher_high'] = df['high'] >= df['high_n']

    signals = []
    in_position = False
    hh_count = 0

    for _, row in df.iterrows():
        if pd.isna(row['high_n']):
            continue

        if row['higher_high']:
            hh_count += 1
        else:
            hh_count = 0

        if not in_position and hh_count >= 2:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and not row['higher_high']:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_trend_strength(symbol, df, params):
    """趋势强度: ADX确认强趋势时跟随."""
    period = int(params.get('period', 14))
    adx_threshold = float(params.get('adx_threshold', 25))

    df = df.copy()
    df['tr'] = np.maximum(df['high'] - df['low'],
                          np.maximum(abs(df['high'] - df['close'].shift(1)),
                                    abs(df['low'] - df['close'].shift(1))))
    df['plus_dm'] = np.where((df['high'] - df['high'].shift(1)) > (df['low'].shift(1) - df['low']),
                             np.maximum(df['high'] - df['high'].shift(1), 0), 0)
    df['minus_dm'] = np.where((df['low'].shift(1) - df['low']) > (df['high'] - df['high'].shift(1)),
                              np.maximum(df['low'].shift(1) - df['low'], 0), 0)
    df['atr'] = df['tr'].rolling(period).mean()
    df['plus_di'] = 100 * df['plus_dm'].rolling(period).mean() / df['atr']
    df['minus_di'] = 100 * df['minus_dm'].rolling(period).mean() / df['atr']
    df['dx'] = 100 * abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
    df['adx'] = df['dx'].rolling(period).mean()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['adx']):
            continue

        trend_up = curr['plus_di'] > curr['minus_di']
        strong_trend = curr['adx'] > adx_threshold

        if not in_position and strong_trend and trend_up and prev['adx'] <= adx_threshold:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and (not trend_up or curr['adx'] < adx_threshold * 0.7):
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 策略家族2: 动量策略 (Momentum)
# ═══════════════════════════════════════════════════════════════

def tmpl_momentum_cross(symbol, df, params):
    """动量交叉: 动量上穿零轴买入."""
    period = int(params.get('period', 12))

    df = df.copy()
    df['mom'] = df['close'].pct_change(period)

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['mom']):
            continue

        if not in_position and prev['mom'] <= 0 and curr['mom'] > 0:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and prev['mom'] >= 0 and curr['mom'] < 0:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_roc_ma(symbol, df, params):
    """ROC均线: ROC上穿均线买入."""
    roc_period = int(params.get('roc_period', 10))
    ma_period = int(params.get('ma_period', 5))

    df = df.copy()
    df['roc'] = (df['close'] - df['close'].shift(roc_period)) / df['close'].shift(roc_period) * 100
    df['roc_ma'] = df['roc'].rolling(ma_period).mean()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['roc_ma']):
            continue

        if not in_position and prev['roc'] <= prev['roc_ma'] and curr['roc'] > curr['roc_ma']:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and prev['roc'] >= prev['roc_ma'] and curr['roc'] < curr['roc_ma']:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_acceleration(symbol, df, params):
    """价格加速: 价格变化率加速时买入."""
    short_period = int(params.get('short_period', 5))
    long_period = int(params.get('long_period', 20))

    df = df.copy()
    df['short_ret'] = df['close'].pct_change(short_period)
    df['long_ret'] = df['close'].pct_change(long_period)
    df['accel'] = df['short_ret'] - df['long_ret']

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['accel']):
            continue

        if not in_position and prev['accel'] <= 0 and curr['accel'] > 0:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and prev['accel'] >= 0 and curr['accel'] < 0:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_momentum_divergence(symbol, df, params):
    """动量背离: 价格新高但动量未新高时卖出,反之买入."""
    mom_period = int(params.get('mom_period', 14))
    lookback = int(params.get('lookback', 20))

    df = df.copy()
    df['mom'] = df['close'].pct_change(mom_period)
    df['high_max'] = df['high'].rolling(lookback).max()
    df['mom_max'] = df['mom'].rolling(lookback).max()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['mom_max']):
            continue

        price_new_high = curr['high'] >= curr['high_max']
        mom_not_new_high = curr['mom'] < curr['mom_max'] * 0.95
        bearish_div = price_new_high and mom_not_new_high

        price_new_low = curr['low'] <= df['low'].rolling(lookback).min().iloc[i]
        mom_not_new_low = curr['mom'] > df['mom'].rolling(lookback).min().iloc[i] * 0.95
        bullish_div = price_new_low and mom_not_new_low

        if not in_position and bullish_div:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and bearish_div:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_volume_momentum(symbol, df, params):
    """成交量动量: 放量上涨买入."""
    price_period = int(params.get('price_period', 10))
    vol_period = int(params.get('vol_period', 20))

    df = df.copy()
    df['price_ma'] = df['close'].rolling(price_period).mean()
    df['vol_ma'] = df['volume'].rolling(vol_period).mean()
    df['price_above'] = df['close'] > df['price_ma']
    df['vol_above'] = df['volume'] > df['vol_ma']

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['vol_ma']):
            continue

        if not in_position and curr['price_above'] and curr['vol_above'] and not prev['vol_above']:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and not curr['price_above']:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 策略家族3: 均值回归 (Mean Reversion)
# ═══════════════════════════════════════════════════════════════

def tmpl_rsi_reversal(symbol, df, params):
    """RSI反转: 超卖买入,超买卖出."""
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

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['rsi']):
            continue

        if not in_position and prev['rsi'] < oversold and curr['rsi'] >= oversold:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and prev['rsi'] > overbought and curr['rsi'] <= overbought:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_bollinger_reversion(symbol, df, params):
    """布林带均值回归: 触及下轨买入,上轨卖出."""
    period = int(params.get('period', 20))
    std_mult = float(params.get('std_mult', 2.0))

    df = df.copy()
    df['ma'] = df['close'].rolling(period).mean()
    df['std'] = df['close'].rolling(period).std()
    df['upper'] = df['ma'] + std_mult * df['std']
    df['lower'] = df['ma'] - std_mult * df['std']

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['upper']):
            continue

        if not in_position and prev['close'] <= prev['lower'] and curr['close'] > curr['lower']:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and prev['close'] >= prev['upper'] and curr['close'] < curr['upper']:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_stochastic_reversal(symbol, df, params):
    """随机指标反转: K线上穿D线且在超卖区买入."""
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

        if pd.isna(curr['d']):
            continue

        if not in_position and prev['k'] < oversold and curr['k'] >= oversold and curr['k'] > curr['d']:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and prev['k'] > overbought and curr['k'] <= overbought:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_cci_reversal(symbol, df, params):
    """CCI反转: 低于-100买入,高于100卖出."""
    period = int(params.get('period', 20))
    threshold = float(params.get('threshold', 100))

    df = df.copy()
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3
    df['ma'] = df['tp'].rolling(period).mean()
    df['md'] = df['tp'].rolling(period).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
    df['cci'] = (df['tp'] - df['ma']) / (0.015 * df['md'])

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['cci']):
            continue

        if not in_position and prev['cci'] < -threshold and curr['cci'] >= -threshold:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and prev['cci'] > threshold and curr['cci'] <= threshold:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_williams_r(symbol, df, params):
    """威廉指标反转."""
    period = int(params.get('period', 14))
    oversold = float(params.get('oversold', -80))
    overbought = float(params.get('overbought', -20))

    df = df.copy()
    df['hh'] = df['high'].rolling(period).max()
    df['ll'] = df['low'].rolling(period).min()
    df['wr'] = (df['hh'] - df['close']) / (df['hh'] - df['ll']) * -100

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['wr']):
            continue

        if not in_position and prev['wr'] < oversold and curr['wr'] >= oversold:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and prev['wr'] > overbought and curr['wr'] <= overbought:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 策略家族4: 突破策略 (Breakout)
# ═══════════════════════════════════════════════════════════════

def tmpl_donchian_breakout(symbol, df, params):
    """唐奇安通道突破: 突破N日高点买入,跌破N日低点卖出."""
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


def tmpl_volume_breakout(symbol, df, params):
    """成交量突破: 放量突破买入."""
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

        vol_spike = row['volume'] > row['vol_ma'] * vol_mult

        if not in_position and row['close'] > row['high_n'] and vol_spike:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and row['close'] < df['low'].rolling(lookback).min().shift(1).iloc[0] if False else row['close'] < row['high_n'] * 0.95:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_consolidation_breakout(symbol, df, params):
    """盘整突破: 窄幅盘整后突破买入."""
    lookback = int(params.get('lookback', 40))
    contraction = float(params.get('contraction', 0.8))

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

        is_consolidation = row['range'] < row['range_ma'] * contraction

        if not in_position and is_consolidation and row['close'] > row['high_n']:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and row['close'] < row['low_n']:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_atr_breakout(symbol, df, params):
    """ATR突破: 基于波动率的突破."""
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


# ═══════════════════════════════════════════════════════════════
# 策略家族5: 波动率策略 (Volatility)
# ═══════════════════════════════════════════════════════════════

def tmpl_bollinger_squeeze(symbol, df, params):
    """布林带挤压: 带宽收窄后扩张买入."""
    bb_period = int(params.get('bb_period', 20))
    squeeze_threshold = float(params.get('squeeze_threshold', 0.8))

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

        was_squeezed = prev['bandwidth'] < prev['bw_ma'] * squeeze_threshold
        expanding = curr['bandwidth'] > prev['bandwidth']

        if not in_position and was_squeezed and expanding and curr['close'] > curr['ma']:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.85, 0.1, 0.03))
            in_position = True
        elif in_position and curr['close'] < curr['ma']:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_volatility_regime(symbol, df, params):
    """波动率状态: 低波动买入,高波动卖出."""
    vol_window = int(params.get('vol_window', 20))
    low_threshold = float(params.get('low_threshold', 0.9))
    high_threshold = float(params.get('high_threshold', 1.1))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['vol'] = df['returns'].rolling(vol_window).std() * np.sqrt(252)
    df['vol_ma'] = df['vol'].rolling(60).mean()

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['vol_ma']):
            continue

        if not in_position and row['vol'] < row['vol_ma'] * low_threshold:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and row['vol'] > row['vol_ma'] * high_threshold:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tpl_volatility_mean_reversion(symbol, df, params):
    """波动率均值回归: 极端波动后回归."""
    period = int(params.get('period', 20))
    extreme_mult = float(params.get('extreme_mult', 1.5))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['vol'] = df['returns'].rolling(period).std()
    df['vol_ma'] = df['vol'].rolling(period * 3).mean()

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['vol_ma']):
            continue

        if not in_position and row['vol'] > row['vol_ma'] * extreme_mult:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and row['vol'] < row['vol_ma']:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_range_expansion(symbol, df, params):
    """区间扩张: 波动率扩张时跟随趋势."""
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

        expansion = row['range'] > row['range_ma'] + row['range_std']

        if not in_position and expansion and row['close'] > row['open']:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and row['range'] < row['range_ma']:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tpl_atr_position(symbol, df, params):
    """ATR仓位管理: 基于ATR调整信号强度."""
    period = int(params.get('period', 14))
    atr_threshold = float(params.get('atr_threshold', 0.03))

    df = df.copy()
    df['tr'] = np.maximum(df['high'] - df['low'],
                          np.maximum(abs(df['high'] - df['close'].shift(1)),
                                    abs(df['low'] - df['close'].shift(1))))
    df['atr'] = df['tr'].rolling(period).mean()
    df['atr_pct'] = df['atr'] / df['close']

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['atr_pct']):
            continue

        if not in_position and curr['atr_pct'] < atr_threshold and curr['close'] > curr['open']:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and curr['atr_pct'] > atr_threshold * 2:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 策略家族6: 多因子复合 (Multi-Factor)
# ═══════════════════════════════════════════════════════════════

def tmpl_trend_momentum_vol(symbol, df, params):
    """趋势+动量+成交量三因子复合."""
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
    """RSI+均线复合: RSI>50且价格在均线上方买入."""
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
    """MACD+RSI复合: MACD金叉且RSI>50买入."""
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

        macd_cross = prev['hist'] < 0 and curr['hist'] > 0
        rsi_ok = curr['rsi'] > 50

        if not in_position and macd_cross and rsi_ok:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.9, 0.1, 0.03))
            in_position = True
        elif in_position and prev['hist'] > 0 and curr['hist'] < 0:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_boll_rsi_combo(symbol, df, params):
    """布林带+RSI复合: 触及下轨且RSI超卖买入."""
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
    """多时间框架: 短中长期均线多头排列买入."""
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
# 策略家族7: 行为金融 (Behavioral)
# ═══════════════════════════════════════════════════════════════

def tmpl_contrarian_extreme(symbol, df, params):
    """极端逆向: 连续大跌后买入,连续大涨后卖出."""
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
    """恐惧贪婪: 下跌天数比例<30%买入,>70%卖出."""
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


def tmpl_pivot_points(symbol, df, params):
    """枢轴点突破: 突破R1买入,跌破S1卖出."""
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
    """VWAP偏离: 价格低于VWAP时买入."""
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


def tmpl_support_resistance(symbol, df, params):
    """支撑阻力: 触及支撑买入,触及阻力卖出."""
    lookback = int(params.get('lookback', 40))
    touch_threshold = float(params.get('touch_threshold', 0.02))

    df = df.copy()
    df['support'] = df['low'].rolling(lookback).min()
    df['resistance'] = df['high'].rolling(lookback).max()

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['support']):
            continue

        near_support = abs(row['close'] - row['support']) / row['support'] < touch_threshold
        near_resistance = abs(row['close'] - row['resistance']) / row['resistance'] < touch_threshold

        if not in_position and near_support and row['close'] > row['open']:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and near_resistance and row['close'] < row['open']:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 参数扫描配置
# ═══════════════════════════════════════════════════════════════

STRATEGY_CONFIGS = [
    # ── 趋势跟踪 ──
    ("ema_cross", "趋势跟踪", tmpl_ema_cross, [
        {"fast": 3, "slow": 10}, {"fast": 5, "slow": 15}, {"fast": 5, "slow": 20},
        {"fast": 8, "slow": 20}, {"fast": 10, "slow": 30}, {"fast": 12, "slow": 26},
        {"fast": 3, "slow": 12}, {"fast": 5, "slow": 25}, {"fast": 8, "slow": 30},
        {"fast": 2, "slow": 10}, {"fast": 3, "slow": 15}, {"fast": 5, "slow": 30},
    ]),
    ("ma_slope", "趋势跟踪", tmpl_ma_slope, [
        {"period": 20, "slope_threshold": 0.001}, {"period": 30, "slope_threshold": 0.001},
        {"period": 20, "slope_threshold": 0.0005}, {"period": 15, "slope_threshold": 0.001},
        {"period": 25, "slope_threshold": 0.001}, {"period": 10, "slope_threshold": 0.001},
    ]),
    ("price_above_ma", "趋势跟踪", tmpl_price_above_ma, [
        {"period": 20}, {"period": 30}, {"period": 50}, {"period": 10}, {"period": 15},
        {"period": 25}, {"period": 40}, {"period": 60},
    ]),
    ("higher_highs", "趋势跟踪", tmpl_higher_highs, [
        {"lookback": 20}, {"lookback": 30}, {"lookback": 40}, {"lookback": 15}, {"lookback": 25},
    ]),
    ("trend_strength", "趋势跟踪", tmpl_trend_strength, [
        {"period": 14, "adx_threshold": 25}, {"period": 10, "adx_threshold": 20},
        {"period": 20, "adx_threshold": 30}, {"period": 14, "adx_threshold": 20},
        {"period": 14, "adx_threshold": 30},
    ]),

    # ── 动量策略 ──
    ("momentum_cross", "动量策略", tmpl_momentum_cross, [
        {"period": 12}, {"period": 10}, {"period": 20}, {"period": 14}, {"period": 8},
        {"period": 6}, {"period": 15}, {"period": 5},
    ]),
    ("roc_ma", "动量策略", tmpl_roc_ma, [
        {"roc_period": 10, "ma_period": 5}, {"roc_period": 12, "ma_period": 6},
        {"roc_period": 8, "ma_period": 4}, {"roc_period": 15, "ma_period": 5},
        {"roc_period": 20, "ma_period": 10}, {"roc_period": 5, "ma_period": 3},
    ]),
    ("acceleration", "动量策略", tmpl_acceleration, [
        {"short_period": 5, "long_period": 20}, {"short_period": 3, "long_period": 15},
        {"short_period": 10, "long_period": 30}, {"short_period": 5, "long_period": 15},
        {"short_period": 8, "long_period": 25}, {"short_period": 3, "long_period": 10},
    ]),
    ("momentum_divergence", "动量策略", tmpl_momentum_divergence, [
        {"mom_period": 14, "lookback": 20}, {"mom_period": 10, "lookback": 15},
        {"mom_period": 20, "lookback": 30}, {"mom_period": 12, "lookback": 20},
    ]),
    ("volume_momentum", "动量策略", tmpl_volume_momentum, [
        {"price_period": 10, "vol_period": 20}, {"price_period": 5, "vol_period": 15},
        {"price_period": 20, "vol_period": 30}, {"price_period": 10, "vol_period": 10},
        {"price_period": 15, "vol_period": 25},
    ]),

    # ── 均值回归 ──
    ("rsi_reversal", "均值回归", tmpl_rsi_reversal, [
        {"period": 14, "oversold": 30, "overbought": 70},
        {"period": 10, "oversold": 25, "overbought": 75},
        {"period": 20, "oversold": 35, "overbought": 65},
        {"period": 14, "oversold": 20, "overbought": 80},
        {"period": 7, "oversold": 20, "overbought": 80},
        {"period": 14, "oversold": 25, "overbought": 75},
        {"period": 10, "oversold": 30, "overbought": 70},
    ]),
    ("bollinger_reversion", "均值回归", tmpl_bollinger_reversion, [
        {"period": 20, "std_mult": 2.0}, {"period": 15, "std_mult": 1.5},
        {"period": 25, "std_mult": 2.5}, {"period": 20, "std_mult": 1.5},
        {"period": 30, "std_mult": 2.0}, {"period": 20, "std_mult": 2.5},
        {"period": 15, "std_mult": 2.0},
    ]),
    ("stochastic_reversal", "均值回归", tmpl_stochastic_reversal, [
        {"k_period": 14, "d_period": 3, "oversold": 20, "overbought": 80},
        {"k_period": 10, "d_period": 3, "oversold": 15, "overbought": 85},
        {"k_period": 20, "d_period": 5, "oversold": 25, "overbought": 75},
        {"k_period": 14, "d_period": 3, "oversold": 30, "overbought": 70},
        {"k_period": 7, "d_period": 3, "oversold": 20, "overbought": 80},
    ]),
    ("cci_reversal", "均值回归", tmpl_cci_reversal, [
        {"period": 20, "threshold": 100}, {"period": 14, "threshold": 100},
        {"period": 20, "threshold": 150}, {"period": 10, "threshold": 100},
        {"period": 20, "threshold": 80}, {"period": 14, "threshold": 80},
    ]),
    ("williams_r", "均值回归", tmpl_williams_r, [
        {"period": 14, "oversold": -80, "overbought": -20},
        {"period": 10, "oversold": -85, "overbought": -15},
        {"period": 20, "oversold": -75, "overbought": -25},
        {"period": 14, "oversold": -75, "overbought": -25},
        {"period": 7, "oversold": -80, "overbought": -20},
    ]),

    # ── 突破策略 ──
    ("donchian_breakout", "突破策略", tmpl_donchian_breakout, [
        {"period": 20}, {"period": 40}, {"period": 60}, {"period": 10}, {"period": 30},
        {"period": 50}, {"period": 15}, {"period": 25}, {"period": 35},
    ]),
    ("volume_breakout", "突破策略", tmpl_volume_breakout, [
        {"lookback": 60, "vol_mult": 2.0}, {"lookback": 40, "vol_mult": 1.8},
        {"lookback": 20, "vol_mult": 2.5}, {"lookback": 60, "vol_mult": 1.5},
        {"lookback": 30, "vol_mult": 2.0}, {"lookback": 50, "vol_mult": 2.2},
    ]),
    ("consolidation_breakout", "突破策略", tmpl_consolidation_breakout, [
        {"lookback": 40, "contraction": 0.8}, {"lookback": 20, "contraction": 0.7},
        {"lookback": 60, "contraction": 0.8}, {"lookback": 30, "contraction": 0.75},
        {"lookback": 40, "contraction": 0.7}, {"lookback": 50, "contraction": 0.8},
    ]),
    ("atr_breakout", "突破策略", tmpl_atr_breakout, [
        {"period": 20, "atr_mult": 2.0}, {"period": 15, "atr_mult": 1.5},
        {"period": 25, "atr_mult": 2.5}, {"period": 20, "atr_mult": 1.5},
        {"period": 30, "atr_mult": 3.0}, {"period": 15, "atr_mult": 2.0},
    ]),
    ("keltner_breakout", "突破策略", tmpl_keltner_breakout, [
        {"ema_period": 20, "atr_period": 10, "mult": 2.0},
        {"ema_period": 20, "atr_period": 10, "mult": 1.5},
        {"ema_period": 15, "atr_period": 7, "mult": 2.0},
        {"ema_period": 25, "atr_period": 10, "mult": 2.5},
        {"ema_period": 20, "atr_period": 14, "mult": 2.0},
        {"ema_period": 15, "atr_period": 10, "mult": 1.5},
    ]),

    # ── 波动率策略 ──
    ("bollinger_squeeze", "波动率策略", tmpl_bollinger_squeeze, [
        {"bb_period": 20, "squeeze_threshold": 0.8}, {"bb_period": 15, "squeeze_threshold": 0.7},
        {"bb_period": 25, "squeeze_threshold": 0.8}, {"bb_period": 20, "squeeze_threshold": 0.7},
        {"bb_period": 30, "squeeze_threshold": 0.8}, {"bb_period": 20, "squeeze_threshold": 0.9},
    ]),
    ("volatility_regime", "波动率策略", tmpl_volatility_regime, [
        {"vol_window": 20, "low_threshold": 0.9, "high_threshold": 1.1},
        {"vol_window": 10, "low_threshold": 0.85, "high_threshold": 1.15},
        {"vol_window": 30, "low_threshold": 0.9, "high_threshold": 1.1},
        {"vol_window": 20, "low_threshold": 0.8, "high_threshold": 1.2},
        {"vol_window": 15, "low_threshold": 0.9, "high_threshold": 1.1},
    ]),
    ("volatility_mean_reversion", "波动率策略", tpl_volatility_mean_reversion, [
        {"period": 20, "extreme_mult": 1.5}, {"period": 15, "extreme_mult": 1.5},
        {"period": 20, "extreme_mult": 2.0}, {"period": 10, "extreme_mult": 1.5},
        {"period": 30, "extreme_mult": 1.5},
    ]),
    ("range_expansion", "波动率策略", tmpl_range_expansion, [
        {"period": 20}, {"period": 15}, {"period": 30}, {"period": 10}, {"period": 25},
    ]),
    ("atr_position", "波动率策略", tpl_atr_position, [
        {"period": 14, "atr_threshold": 0.03}, {"period": 10, "atr_threshold": 0.02},
        {"period": 20, "atr_threshold": 0.04}, {"period": 14, "atr_threshold": 0.02},
        {"period": 14, "atr_threshold": 0.04},
    ]),

    # ── 多因子复合 ──
    ("trend_momentum_vol", "多因子复合", tmpl_trend_momentum_vol, [
        {"trend_ma": 50, "mom_period": 20, "vol_window": 20},
        {"trend_ma": 30, "mom_period": 10, "vol_window": 15},
        {"trend_ma": 60, "mom_period": 30, "vol_window": 30},
        {"trend_ma": 40, "mom_period": 15, "vol_window": 20},
        {"trend_ma": 20, "mom_period": 10, "vol_window": 10},
        {"trend_ma": 50, "mom_period": 15, "vol_window": 15},
    ]),
    ("rsi_ma_combo", "多因子复合", tmpl_rsi_ma_combo, [
        {"rsi_period": 14, "ma_period": 50}, {"rsi_period": 10, "ma_period": 30},
        {"rsi_period": 20, "ma_period": 60}, {"rsi_period": 14, "ma_period": 30},
        {"rsi_period": 10, "ma_period": 50}, {"rsi_period": 14, "ma_period": 40},
    ]),
    ("macd_rsi_combo", "多因子复合", tmpl_macd_rsi_combo, [
        {"fast": 12, "slow": 26, "signal": 9, "rsi_period": 14},
        {"fast": 8, "slow": 21, "signal": 5, "rsi_period": 10},
        {"fast": 5, "slow": 15, "signal": 3, "rsi_period": 14},
        {"fast": 10, "slow": 30, "signal": 9, "rsi_period": 14},
        {"fast": 12, "slow": 26, "signal": 9, "rsi_period": 10},
    ]),
    ("boll_rsi_combo", "多因子复合", tmpl_boll_rsi_combo, [
        {"bb_period": 20, "rsi_period": 14}, {"bb_period": 15, "rsi_period": 10},
        {"bb_period": 25, "rsi_period": 20}, {"bb_period": 20, "rsi_period": 10},
        {"bb_period": 15, "rsi_period": 14}, {"bb_period": 30, "rsi_period": 14},
    ]),
    ("multi_timeframe", "多因子复合", tmpl_multi_timeframe, [
        {"short": 10, "mid": 30, "long": 60}, {"short": 5, "mid": 20, "long": 50},
        {"short": 10, "mid": 20, "long": 40}, {"short": 5, "mid": 15, "long": 30},
        {"short": 8, "mid": 25, "long": 50}, {"short": 10, "mid": 30, "long": 50},
    ]),

    # ── 行为金融 ──
    ("contrarian_extreme", "行为金融", tmpl_contrarian_extreme, [
        {"streak": 5, "threshold": 0.15}, {"streak": 3, "threshold": 0.1},
        {"streak": 7, "threshold": 0.2}, {"streak": 5, "threshold": 0.1},
        {"streak": 3, "threshold": 0.15}, {"streak": 5, "threshold": 0.2},
    ]),
    ("fear_greed_index", "行为金融", tmpl_fear_greed_index, [
        {"lookback": 20}, {"lookback": 10}, {"lookback": 30}, {"lookback": 15},
        {"lookback": 25}, {"lookback": 40},
    ]),
    ("pivot_points", "行为金融", tmpl_pivot_points, [{}]),
    ("vwap_deviation", "行为金融", tmpl_vwap_deviation, [
        {"period": 20, "threshold": 0.03}, {"period": 10, "threshold": 0.02},
        {"period": 30, "threshold": 0.04}, {"period": 20, "threshold": 0.02},
        {"period": 15, "threshold": 0.03}, {"period": 25, "threshold": 0.03},
    ]),
    ("support_resistance", "行为金融", tmpl_support_resistance, [
        {"lookback": 40, "touch_threshold": 0.02}, {"lookback": 20, "touch_threshold": 0.015},
        {"lookback": 60, "touch_threshold": 0.025}, {"lookback": 30, "touch_threshold": 0.02},
        {"lookback": 40, "touch_threshold": 0.015},
    ]),
]


# ═══════════════════════════════════════════════════════════════
# 策略发现主函数
# ═══════════════════════════════════════════════════════════════

def discover_strategies(target_count: int = 35, verbose: bool = True) -> list[dict]:
    """策略发现主函数.

    Args:
        target_count: 目标策略数量
        verbose: 是否打印详情

    Returns:
        通过验证的策略列表
    """
    if verbose:
        print(f"[StrategyDiscovery] 开始策略发现，目标: {target_count}个高质量策略")
        print(f"[StrategyDiscovery] 策略模板数量: {len(STRATEGY_CONFIGS)}")
        print("=" * 80)

    data_pool = preload_all_data()

    passed = []
    failed = []
    total_tested = 0

    for family_name, family_label, func, param_list in STRATEGY_CONFIGS:
        for params in param_list:
            total_tested += 1
            strategy_id = f"{family_name}_{'_'.join([f'{k}{v}' for k, v in params.items()])}"

            if verbose and total_tested % 50 == 0:
                print(f"  已测试 {total_tested} 个变体, 通过 {len(passed)} 个")

            result = validate_template(
                strategy_id,
                'technical_indicator',
                func,
                params,
                data_pool=data_pool,
                verbose=False  # 批量测试时关闭详细输出
            )

            if result['passed']:
                strategy_info = {
                    'id': strategy_id,
                    'name': family_name,
                    'family': family_label,
                    'func': func,
                    'params': params,
                    'overall': result['overall'],
                }
                passed.append(strategy_info)
                if verbose:
                    print(f"  ✅ {strategy_id} ({family_label}) - WR:{result['overall']['avg_win_rate']:.1%}")
            else:
                failed.append({
                    'id': strategy_id,
                    'family': family_label,
                    'reasons': result['fail_reasons'][:3]
                })

            if len(passed) >= target_count:
                if verbose:
                    print(f"\n[StrategyDiscovery] 已达到目标数量 {target_count}，提前终止")
                break

        if len(passed) >= target_count:
            break

    if verbose:
        print("\n" + "=" * 80)
        print(f"[StrategyDiscovery] 完成: 测试了 {total_tested} 个变体")
        print(f"[StrategyDiscovery] 通过验证: {len(passed)} 个策略")
        if len(passed) < target_count:
            print(f"[StrategyDiscovery] 警告: 未达到目标数量，还需 {target_count - len(passed)} 个策略")

        # 按家族统计
        family_counts = {}
        for p in passed:
            family_counts[p['family']] = family_counts.get(p['family'], 0) + 1
        print("\n[StrategyDiscovery] 各家族通过数量:")
        for family, count in sorted(family_counts.items()):
            print(f"  {family}: {count}个")

    return passed


def get_strategy_pool() -> list[dict]:
    """获取完整的策略池(用于外部调用).

    Returns:
        策略配置列表，每个元素包含id/name/family/func/params
    """
    pool = []
    for family_name, family_label, func, param_list in STRATEGY_CONFIGS:
        for params in param_list:
            strategy_id = f"{family_name}_{'_'.join([f'{k}{v}' for k, v in params.items()])}"
            pool.append({
                'id': strategy_id,
                'name': family_name,
                'family': family_label,
                'func': func,
                'params': params,
            })
    return pool


if __name__ == "__main__":
    passed = discover_strategies(target_count=35, verbose=True)
    print(f"\n最终通过策略数: {len(passed)}")
    for p in passed:
        print(f"  - {p['id']} ({p['family']}) WR:{p['overall']['avg_win_rate']:.1%}")

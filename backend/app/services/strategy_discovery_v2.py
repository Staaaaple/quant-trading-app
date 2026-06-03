"""策略发现引擎V2 — 更复杂的策略 + 更宽松的验证标准.

策略设计思路：
1. 多因子复合（趋势+动量+波动率+量价）
2. 机器学习特征（价格形态、统计套利）
3. 行为金融（情绪指标、反向指标）
4. 跨市场信号（宏观+微观）
"""

import numpy as np
import pandas as pd
from typing import Any

from app.services.backtest_validator import validate_template, preload_all_data
from app.services.template_runner import make_signal


# ═══════════════════════════════════════════════════════════════
# 高级策略定义
# ═══════════════════════════════════════════════════════════════

# ── 1. 多因子复合策略 ──

def tmpl_trend_momentum_vol(symbol, df, params):
    """趋势+动量+波动率三因子复合.

    买入条件：
    1. 价格在均线之上（趋势）
    2. 短期动量>0（动量）
    3. 波动率处于低位（波动率）
    """
    trend_window = int(params.get('trend_window', 60))
    mom_window = int(params.get('mom_window', 20))
    vol_window = int(params.get('vol_window', 20))
    vol_lookback = int(params.get('vol_lookback', 60))

    df = df.copy()
    df['ma'] = df['close'].rolling(trend_window).mean()
    df['momentum'] = df['close'].pct_change(mom_window)
    df['vol'] = df['close'].pct_change().rolling(vol_window).std()
    df['vol_ma'] = df['vol'].rolling(vol_lookback).mean()

    df['trend_ok'] = df['close'] > df['ma']
    df['mom_ok'] = df['momentum'] > 0
    df['vol_ok'] = df['vol'] < df['vol_ma']  # 低波动

    df['score'] = df['trend_ok'].astype(int) + df['mom_ok'].astype(int) + df['vol_ok'].astype(int)

    signals = []
    prev_score = None
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['score']):
            prev_score = None
            continue

        # 3分满分 = 强烈买入
        if not in_position and row['score'] >= 3 and prev_score is not None and prev_score < 3:
            sig = make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03)
            signals.append(sig)
            in_position = True
        # 分数下降 = 卖出
        elif in_position and row['score'] < 2:
            sig = make_signal(symbol, str(row['date']), -1, 0.6, -0.03, 0.03)
            signals.append(sig)
            in_position = False

        prev_score = row['score']

    return signals


def tmpl_mean_reversion_combo(symbol, df, params):
    """均值回归组合：RSI超卖+价格偏离+缩量.

    买入：RSI<30 + 价格<均线5% + 成交量<均值
    卖出：RSI>70 + 价格>均线5% + 成交量>均值
    """
    rsi_period = int(params.get('rsi_period', 14))
    ma_window = int(params.get('ma_window', 20))
    vol_window = int(params.get('vol_window', 20))
    dev_threshold = float(params.get('dev_threshold', 0.05))

    df = df.copy()
    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(rsi_period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # 价格偏离
    df['ma'] = df['close'].rolling(ma_window).mean()
    df['dev'] = (df['close'] - df['ma']) / df['ma']

    # 成交量
    df['vol_ma'] = df['volume'].rolling(vol_window).mean()
    df['vol_low'] = df['volume'] < df['vol_ma'] * 0.8

    signals = []
    for _, row in df.iterrows():
        if pd.isna(row['rsi']):
            continue

        # 超卖+偏离+缩量 = 买入
        if row['rsi'] < 30 and row['dev'] < -dev_threshold and row['vol_low']:
            sig = make_signal(symbol, str(row['date']), 1, 0.75, 0.05, 0.03)
            signals.append(sig)

        # 超买+偏离+放量 = 卖出
        elif row['rsi'] > 70 and row['dev'] > dev_threshold and not row['vol_low']:
            sig = make_signal(symbol, str(row['date']), -1, 0.75, -0.04, 0.03)
            signals.append(sig)

    return signals


# ── 2. 统计套利策略 ──

def tmpl_pairs_trading_style(symbol, df, params):
    """配对交易风格：基于价差的均值回归.

    使用个股自身的移动平均线作为"配对"基准.
    """
    fast_window = int(params.get('fast_window', 5))
    slow_window = int(params.get('slow_window', 60))
    z_threshold = float(params.get('z_threshold', 2.0))

    df = df.copy()
    df['fast_ma'] = df['close'].rolling(fast_window).mean()
    df['slow_ma'] = df['close'].rolling(slow_window).mean()
    df['spread'] = df['close'] - df['slow_ma']
    df['spread_std'] = df['spread'].rolling(slow_window).std()
    df['zscore'] = df['spread'] / df['spread_std']

    signals = []
    for _, row in df.iterrows():
        if pd.isna(row['zscore']):
            continue

        # 价差过大 = 回归
        if row['zscore'] > z_threshold:
            sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.04, 0.03)
            signals.append(sig)
        elif row['zscore'] < -z_threshold:
            sig = make_signal(symbol, str(row['date']), 1, 0.7, 0.05, 0.03)
            signals.append(sig)

    return signals


def tmpl_bollinger_rsi_combo(symbol, df, params):
    """布林带+RSI复合：双重确认.

    买入：价格触及下轨 + RSI<30
    卖出：价格触及上轨 + RSI>70
    """
    bb_period = int(params.get('bb_period', 20))
    bb_std = float(params.get('bb_std', 2.0))
    rsi_period = int(params.get('rsi_period', 14))

    df = df.copy()
    # 布林带
    df['ma'] = df['close'].rolling(bb_period).mean()
    df['std'] = df['close'].rolling(bb_period).std()
    df['upper'] = df['ma'] + bb_std * df['std']
    df['lower'] = df['ma'] - bb_std * df['std']

    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(rsi_period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    signals = []
    for _, row in df.iterrows():
        if pd.isna(row['rsi']):
            continue

        # 下轨+超卖
        if row['close'] < row['lower'] and row['rsi'] < 30:
            sig = make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03)
            signals.append(sig)

        # 上轨+超买
        elif row['close'] > row['upper'] and row['rsi'] > 70:
            sig = make_signal(symbol, str(row['date']), -1, 0.8, -0.04, 0.03)
            signals.append(sig)

    return signals


# ── 3. 行为金融策略 ──

def tmpl_contrarian_sentiment(symbol, df, params):
    """逆向情绪策略：连续极端走势后反向操作.

    基于行为金融学中的过度反应理论.
    """
    streak_window = int(params.get('streak_window', 5))
    extreme_threshold = float(params.get('extreme_threshold', 0.10))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['cum_ret'] = df['returns'].rolling(streak_window).sum()

    signals = []
    for i in range(streak_window, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]

        if pd.isna(row['cum_ret']):
            continue

        # 连续大跌后买入（恐惧）
        if row['cum_ret'] < -extreme_threshold and prev_row['cum_ret'] < -extreme_threshold * 0.5:
            sig = make_signal(symbol, str(row['date']), 1, 0.7, 0.06, 0.04)
            signals.append(sig)

        # 连续大涨后卖出（贪婪）
        elif row['cum_ret'] > extreme_threshold and prev_row['cum_ret'] > extreme_threshold * 0.5:
            sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.04, 0.04)
            signals.append(sig)

    return signals


def tmpl_vwap_deviation(symbol, df, params):
    """VWAP偏离策略：价格回归成交量加权均价.

    机构常用策略，价格大幅偏离VWAP后回归.
    """
    vwap_window = int(params.get('vwap_window', 20))
    dev_threshold = float(params.get('dev_threshold', 0.03))

    df = df.copy()
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3
    df['tp_vol'] = df['tp'] * df['volume']
    df['vwap'] = df['tp_vol'].rolling(vwap_window).sum() / df['volume'].rolling(vwap_window).sum()
    df['dev'] = (df['close'] - df['vwap']) / df['vwap']

    signals = []
    for _, row in df.iterrows():
        if pd.isna(row['dev']):
            continue

        # 大幅低于VWAP = 买入
        if row['dev'] < -dev_threshold:
            sig = make_signal(symbol, str(row['date']), 1, 0.65, 0.04, 0.03)
            signals.append(sig)

        # 大幅高于VWAP = 卖出
        elif row['dev'] > dev_threshold:
            sig = make_signal(symbol, str(row['date']), -1, 0.65, -0.03, 0.03)
            signals.append(sig)

    return signals


# ── 4. 量价分析策略 ──

def tmpl_on_balance_volume(symbol, df, params):
    """OBV能量潮趋势确认.

    OBV与价格趋势背离时产生信号.
    """
    obv_window = int(params.get('obv_window', 20))
    confirm_days = int(params.get('confirm_days', 3))

    df = df.copy()
    df['obv_change'] = np.where(
        df['close'] > df['close'].shift(1), df['volume'],
        np.where(df['close'] < df['close'].shift(1), -df['volume'], 0)
    )
    df['obv'] = df['obv_change'].cumsum()
    df['obv_ma'] = df['obv'].rolling(obv_window).mean()
    df['price_ma'] = df['close'].rolling(obv_window).mean()

    df['obv_trend'] = df['obv'] > df['obv_ma']
    df['price_trend'] = df['close'] > df['price_ma']

    signals = []
    prev_state = None
    confirm_count = 0

    for _, row in df.iterrows():
        if pd.isna(row['obv_ma']):
            continue

        # OBV和价格同向 = 趋势确认
        state = 'aligned' if row['obv_trend'] == row['price_trend'] else 'diverged'

        if state == 'aligned':
            confirm_count += 1
        else:
            confirm_count = 0

        if confirm_count >= confirm_days and prev_state != 'confirmed':
            if row['obv_trend']:  # 同步向上
                sig = make_signal(symbol, str(row['date']), 1, 0.7, 0.05, 0.03)
                signals.append(sig)
            else:  # 同步向下
                sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.03, 0.03)
                signals.append(sig)
            prev_state = 'confirmed'
        elif state == 'diverged':
            prev_state = 'diverged'

    return signals


def tmpl_money_flow_index(symbol, df, params):
    """MFI资金流量指标：量价结合的RSI.

    MFI < 20 超卖，MFI > 80 超买.
    """
    period = int(params.get('period', 14))
    oversold = float(params.get('oversold', 20))
    overbought = float(params.get('overbought', 80))

    df = df.copy()
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3
    df['raw_money'] = df['tp'] * df['volume']
    df['money_flow'] = np.where(
        df['tp'] > df['tp'].shift(1), df['raw_money'],
        np.where(df['tp'] < df['tp'].shift(1), -df['raw_money'], 0)
    )
    df['positive'] = df['money_flow'].clip(lower=0).rolling(period).sum()
    df['negative'] = (-df['money_flow'].clip(upper=0)).rolling(period).sum()
    df['mfi'] = 100 - (100 / (1 + df['positive'] / df['negative']))

    signals = []
    prev_mfi = None

    for _, row in df.iterrows():
        if prev_mfi is not None and not np.isnan(row['mfi']):
            if prev_mfi < oversold and row['mfi'] >= oversold:
                sig = make_signal(symbol, str(row['date']), 1, 0.7, 0.05, 0.03)
                signals.append(sig)
            elif prev_mfi > overbought and row['mfi'] <= overbought:
                sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.04, 0.03)
                signals.append(sig)
        prev_mfi = row['mfi']

    return signals


# ── 5. 趋势跟踪策略 ──

def tmpl_adaptive_moving_average(symbol, df, params):
    """自适应移动平均线：根据波动率调整周期.

    高波动用短周期，低波动用长周期.
    """
    fast_period = int(params.get('fast_period', 10))
    slow_period = int(params.get('slow_period', 50))
    vol_window = int(params.get('vol_window', 20))
    vol_lookback = int(params.get('vol_lookback', 60))

    df = df.copy()
    df['vol'] = df['close'].pct_change().rolling(vol_window).std()
    df['vol_ma'] = df['vol'].rolling(vol_lookback).mean()
    df['high_vol'] = df['vol'] > df['vol_ma']

    df['fast_ma'] = df['close'].rolling(fast_period).mean()
    df['slow_ma'] = df['close'].rolling(slow_period).mean()
    df['adaptive_ma'] = np.where(df['high_vol'], df['fast_ma'], df['slow_ma'])

    signals = []
    prev_close = None

    for _, row in df.iterrows():
        if pd.isna(row['adaptive_ma']):
            prev_close = row['close']
            continue

        if prev_close is not None:
            # 上穿自适应均线
            if prev_close <= row['adaptive_ma'] and row['close'] > row['adaptive_ma']:
                sig = make_signal(symbol, str(row['date']), 1, 0.7, 0.05, 0.03)
                signals.append(sig)
            # 下穿自适应均线
            elif prev_close >= row['adaptive_ma'] and row['close'] < row['adaptive_ma']:
                sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.03, 0.03)
                signals.append(sig)

        prev_close = row['close']

    return signals


def tmpl_donchian_channel(symbol, df, params):
    """唐奇安通道突破：N日高低点突破.

    海龟交易系统的核心.
    """
    channel_period = int(params.get('channel_period', 20))
    exit_period = int(params.get('exit_period', 10))

    df = df.copy()
    df['upper'] = df['high'].rolling(channel_period).max().shift(1)
    df['lower'] = df['low'].rolling(channel_period).min().shift(1)
    df['exit_upper'] = df['high'].rolling(exit_period).max().shift(1)
    df['exit_lower'] = df['low'].rolling(exit_period).min().shift(1)

    signals = []
    in_position = False
    position_type = None

    for _, row in df.iterrows():
        if pd.isna(row['upper']):
            continue

        if not in_position:
            if row['close'] > row['upper']:
                sig = make_signal(symbol, str(row['date']), 1, 0.75, 0.06, 0.04)
                signals.append(sig)
                in_position = True
                position_type = 'long'
            elif row['close'] < row['lower']:
                sig = make_signal(symbol, str(row['date']), -1, 0.75, -0.04, 0.04)
                signals.append(sig)
                in_position = True
                position_type = 'short'
        else:
            if position_type == 'long' and row['close'] < row['exit_lower']:
                sig = make_signal(symbol, str(row['date']), -1, 0.6, -0.03, 0.03)
                signals.append(sig)
                in_position = False
                position_type = None
            elif position_type == 'short' and row['close'] > row['exit_upper']:
                sig = make_signal(symbol, str(row['date']), 1, 0.6, 0.03, 0.03)
                signals.append(sig)
                in_position = False
                position_type = None

    return signals


# ── 6. 波动率策略 ──

def tmpl_keltner_breakout(symbol, df, params):
    """Keltner通道突破：基于ATR的通道.

    比布林带更平滑，减少假突破.
    """
    ema_period = int(params.get('ema_period', 20))
    atr_period = int(params.get('atr_period', 10))
    atr_mult = float(params.get('atr_mult', 2.0))

    df = df.copy()
    df['ema'] = df['close'].ewm(span=ema_period).mean()
    df['tr'] = np.maximum(df['high'] - df['low'],
                          np.maximum(abs(df['high'] - df['close'].shift(1)),
                                    abs(df['low'] - df['close'].shift(1))))
    df['atr'] = df['tr'].rolling(atr_period).mean()
    df['upper'] = df['ema'] + atr_mult * df['atr']
    df['lower'] = df['ema'] - atr_mult * df['atr']

    signals = []
    for _, row in df.iterrows():
        if pd.isna(row['upper']):
            continue

        if row['close'] > row['upper']:
            sig = make_signal(symbol, str(row['date']), 1, 0.7, 0.05, 0.04)
            signals.append(sig)
        elif row['close'] < row['lower']:
            sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.04, 0.04)
            signals.append(sig)

    return signals


def tmpl_volatility_squeeze(symbol, df, params):
    """波动率挤压：布林带在Keltner内部时，预示大行情.

    挤压结束后跟随突破方向.
    """
    bb_period = int(params.get('bb_period', 20))
    kc_period = int(params.get('kc_period', 20))
    atr_mult = float(params.get('atr_mult', 1.5))

    df = df.copy()
    # 布林带
    df['bb_mid'] = df['close'].rolling(bb_period).mean()
    df['bb_std'] = df['close'].rolling(bb_period).std()
    df['bb_upper'] = df['bb_mid'] + 2 * df['bb_std']
    df['bb_lower'] = df['bb_mid'] - 2 * df['bb_std']

    # Keltner
    df['tr'] = np.maximum(df['high'] - df['low'],
                          np.maximum(abs(df['high'] - df['close'].shift(1)),
                                    abs(df['low'] - df['close'].shift(1))))
    df['atr'] = df['tr'].rolling(kc_period).mean()
    df['kc_upper'] = df['bb_mid'] + atr_mult * df['atr']
    df['kc_lower'] = df['bb_mid'] - atr_mult * df['atr']

    # 挤压检测
    df['squeeze'] = (df['bb_upper'] < df['kc_upper']) & (df['bb_lower'] > df['kc_lower'])
    df['squeeze_off'] = df['squeeze'].shift(1).fillna(False) & ~df['squeeze']

    signals = []
    for _, row in df.iterrows():
        if pd.isna(row['squeeze_off']):
            continue

        if row['squeeze_off']:
            if row['close'] > row['bb_mid']:
                sig = make_signal(symbol, str(row['date']), 1, 0.75, 0.06, 0.03)
                signals.append(sig)
            elif row['close'] < row['bb_mid']:
                sig = make_signal(symbol, str(row['date']), -1, 0.75, -0.04, 0.03)
                signals.append(sig)

    return signals


# ── 7. 动量策略 ──

def tmpl_rate_of_change(symbol, df, params):
    """ROC变动率：价格变化速度.

    ROC由负转正买入，由正转负卖出.
    """
    roc_period = int(params.get('roc_period', 12))
    ma_period = int(params.get('ma_period', 9))

    df = df.copy()
    df['roc'] = (df['close'] - df['close'].shift(roc_period)) / df['close'].shift(roc_period) * 100
    df['roc_ma'] = df['roc'].rolling(ma_period).mean()

    signals = []
    prev_roc = None

    for _, row in df.iterrows():
        if prev_roc is not None and not np.isnan(row['roc']):
            if prev_roc < 0 and row['roc'] >= 0:
                sig = make_signal(symbol, str(row['date']), 1, 0.65, 0.05, 0.03)
                signals.append(sig)
            elif prev_roc > 0 and row['roc'] <= 0:
                sig = make_signal(symbol, str(row['date']), -1, 0.65, -0.03, 0.03)
                signals.append(sig)
        prev_roc = row['roc']

    return signals


def tmpl_stochastic_oscillator(symbol, df, params):
    """%K%D随机指标: 超买超卖.

    K上穿D买入, K下穿D卖出.
    """
    k_period = int(params.get('k_period', 14))
    d_period = int(params.get('d_period', 3))
    oversold = float(params.get('oversold', 20))
    overbought = float(params.get('overbought', 80))

    df = df.copy()
    df['lowest'] = df['low'].rolling(k_period).min()
    df['highest'] = df['high'].rolling(k_period).max()
    df['k'] = 100 * (df['close'] - df['lowest']) / (df['highest'] - df['lowest'])
    df['d'] = df['k'].rolling(d_period).mean()

    signals = []
    prev_k = None

    for _, row in df.iterrows():
        if prev_k is not None and not np.isnan(row['k']):
            # 超卖区金叉
            if prev_k < row['k'] and row['k'] < oversold and row['d'] < oversold:
                sig = make_signal(symbol, str(row['date']), 1, 0.7, 0.05, 0.03)
                signals.append(sig)
            # 超买区死叉
            elif prev_k > row['k'] and row['k'] > overbought and row['d'] > overbought:
                sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.04, 0.03)
                signals.append(sig)
        prev_k = row['k']

    return signals


# ── 8. 复合高级策略 ──

def tmpl_multi_indicator_consensus(symbol, df, params):
    """多指标共识：多个指标同时确认才交易.

    MA趋势 + RSI + MACD + 成交量，4个指标共识.
    """
    ma_period = int(params.get('ma_period', 20))
    rsi_period = int(params.get('rsi_period', 14))
    macd_fast = int(params.get('macd_fast', 12))
    macd_slow = int(params.get('macd_slow', 26))
    macd_signal = int(params.get('macd_signal', 9))
    vol_window = int(params.get('vol_window', 20))

    df = df.copy()
    # MA趋势
    df['ma'] = df['close'].rolling(ma_period).mean()
    df['ma_trend'] = df['close'] > df['ma']

    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(rsi_period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df['rsi_ok'] = (df['rsi'] > 30) & (df['rsi'] < 70)

    # MACD
    ema_fast = df['close'].ewm(span=macd_fast).mean()
    ema_slow = df['close'].ewm(span=macd_slow).mean()
    df['macd'] = ema_fast - ema_slow
    df['macd_signal'] = df['macd'].ewm(span=macd_signal).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    df['macd_ok'] = df['macd_hist'] > 0

    # 成交量
    df['vol_ma'] = df['volume'].rolling(vol_window).mean()
    df['vol_ok'] = df['volume'] > df['vol_ma']

    # 共识评分
    df['score'] = (df['ma_trend'].astype(int) +
                   df['rsi_ok'].astype(int) +
                   df['macd_ok'].astype(int) +
                   df['vol_ok'].astype(int))

    signals = []
    prev_score = None

    for _, row in df.iterrows():
        if pd.isna(row['score']):
            prev_score = None
            continue

        if prev_score is not None:
            # 4分共识买入
            if prev_score < 4 and row['score'] >= 4:
                sig = make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03)
                signals.append(sig)
            # 共识破裂卖出
            elif prev_score >= 3 and row['score'] < 2:
                sig = make_signal(symbol, str(row['date']), -1, 0.6, -0.03, 0.03)
                signals.append(sig)

        prev_score = row['score']

    return signals


def tmpl_price_volume_trend(symbol, df, params):
    """PVT价量趋势：累积成交量加权价格变化.

    PVT与价格背离时产生信号.
    """
    pvt_window = int(params.get('pvt_window', 20))

    df = df.copy()
    df['ret'] = df['close'].pct_change()
    df['pvt_change'] = df['ret'] * df['volume']
    df['pvt'] = df['pvt_change'].cumsum()
    df['pvt_ma'] = df['pvt'].rolling(pvt_window).mean()
    df['price_ma'] = df['close'].rolling(pvt_window).mean()

    df['pvt_trend'] = df['pvt'] > df['pvt_ma']
    df['price_trend'] = df['close'] > df['price_ma']

    signals = []
    prev_aligned = None

    for _, row in df.iterrows():
        if pd.isna(row['pvt_ma']):
            continue

        aligned = row['pvt_trend'] == row['price_trend']

        if prev_aligned is not None and not prev_aligned and aligned:
            if row['pvt_trend']:  # 同步向上
                sig = make_signal(symbol, str(row['date']), 1, 0.7, 0.05, 0.03)
                signals.append(sig)
            else:
                sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.03, 0.03)
                signals.append(sig)

        prev_aligned = aligned

    return signals


# ═══════════════════════════════════════════════════════════════
# 策略池定义
# ═══════════════════════════════════════════════════════════════

STRATEGY_POOL = [
    # 多因子复合
    {"id": "trend_momentum_vol", "name": "趋势动量波动率复合", "family": "多因子", "func": tmpl_trend_momentum_vol, "params": {"trend_window": 60, "mom_window": 20, "vol_window": 20, "vol_lookback": 60}},
    {"id": "mean_reversion_combo", "name": "均值回归组合", "family": "多因子", "func": tmpl_mean_reversion_combo, "params": {"rsi_period": 14, "ma_window": 20, "vol_window": 20, "dev_threshold": 0.05}},
    {"id": "mean_reversion_combo_v2", "name": "均值回归组合V2", "family": "多因子", "func": tmpl_mean_reversion_combo, "params": {"rsi_period": 10, "ma_window": 30, "vol_window": 15, "dev_threshold": 0.03}},

    # 统计套利
    {"id": "pairs_trading", "name": "配对交易风格", "family": "统计套利", "func": tmpl_pairs_trading_style, "params": {"fast_window": 5, "slow_window": 60, "z_threshold": 2.0}},
    {"id": "pairs_trading_v2", "name": "配对交易风格V2", "family": "统计套利", "func": tmpl_pairs_trading_style, "params": {"fast_window": 10, "slow_window": 40, "z_threshold": 1.5}},
    {"id": "boll_rsi_combo", "name": "布林带RSI复合", "family": "统计套利", "func": tmpl_bollinger_rsi_combo, "params": {"bb_period": 20, "bb_std": 2.0, "rsi_period": 14}},
    {"id": "boll_rsi_combo_v2", "name": "布林带RSI复合V2", "family": "统计套利", "func": tmpl_bollinger_rsi_combo, "params": {"bb_period": 15, "bb_std": 1.5, "rsi_period": 10}},

    # 行为金融
    {"id": "contrarian_sentiment", "name": "逆向情绪策略", "family": "行为金融", "func": tmpl_contrarian_sentiment, "params": {"streak_window": 5, "extreme_threshold": 0.10}},
    {"id": "contrarian_sentiment_v2", "name": "逆向情绪策略V2", "family": "行为金融", "func": tmpl_contrarian_sentiment, "params": {"streak_window": 3, "extreme_threshold": 0.08}},
    {"id": "vwap_deviation", "name": "VWAP偏离策略", "family": "行为金融", "func": tmpl_vwap_deviation, "params": {"vwap_window": 20, "dev_threshold": 0.03}},
    {"id": "vwap_deviation_v2", "name": "VWAP偏离策略V2", "family": "行为金融", "func": tmpl_vwap_deviation, "params": {"vwap_window": 30, "dev_threshold": 0.02}},

    # 量价分析
    {"id": "obv_trend", "name": "OBV趋势确认", "family": "量价分析", "func": tmpl_on_balance_volume, "params": {"obv_window": 20, "confirm_days": 3}},
    {"id": "obv_trend_v2", "name": "OBV趋势确认V2", "family": "量价分析", "func": tmpl_on_balance_volume, "params": {"obv_window": 30, "confirm_days": 2}},
    {"id": "mfi_reversal", "name": "MFI资金流量反转", "family": "量价分析", "func": tmpl_money_flow_index, "params": {"period": 14, "oversold": 20, "overbought": 80}},
    {"id": "mfi_reversal_v2", "name": "MFI资金流量反转V2", "family": "量价分析", "func": tmpl_money_flow_index, "params": {"period": 10, "oversold": 15, "overbought": 85}},

    # 趋势跟踪
    {"id": "adaptive_ma", "name": "自适应均线", "family": "趋势跟踪", "func": tmpl_adaptive_moving_average, "params": {"fast_period": 10, "slow_period": 50, "vol_window": 20, "vol_lookback": 60}},
    {"id": "adaptive_ma_v2", "name": "自适应均线V2", "family": "趋势跟踪", "func": tmpl_adaptive_moving_average, "params": {"fast_period": 5, "slow_period": 30, "vol_window": 15, "vol_lookback": 40}},
    {"id": "donchian_channel", "name": "唐奇安通道", "family": "趋势跟踪", "func": tmpl_donchian_channel, "params": {"channel_period": 20, "exit_period": 10}},
    {"id": "donchian_channel_v2", "name": "唐奇安通道V2", "family": "趋势跟踪", "func": tmpl_donchian_channel, "params": {"channel_period": 40, "exit_period": 20}},

    # 波动率
    {"id": "keltner_breakout", "name": "Keltner通道突破", "family": "波动率", "func": tmpl_keltner_breakout, "params": {"ema_period": 20, "atr_period": 10, "atr_mult": 2.0}},
    {"id": "keltner_breakout_v2", "name": "Keltner通道突破V2", "family": "波动率", "func": tmpl_keltner_breakout, "params": {"ema_period": 15, "atr_period": 7, "atr_mult": 1.5}},
    {"id": "vol_squeeze", "name": "波动率挤压", "family": "波动率", "func": tmpl_volatility_squeeze, "params": {"bb_period": 20, "kc_period": 20, "atr_mult": 1.5}},
    {"id": "vol_squeeze_v2", "name": "波动率挤压V2", "family": "波动率", "func": tmpl_volatility_squeeze, "params": {"bb_period": 15, "kc_period": 15, "atr_mult": 1.2}},

    # 动量
    {"id": "roc_momentum", "name": "ROC变动率", "family": "动量", "func": tmpl_rate_of_change, "params": {"roc_period": 12, "ma_period": 9}},
    {"id": "roc_momentum_v2", "name": "ROC变动率V2", "family": "动量", "func": tmpl_rate_of_change, "params": {"roc_period": 20, "ma_period": 5}},
    {"id": "stochastic", "name": "随机指标", "family": "动量", "func": tmpl_stochastic_oscillator, "params": {"k_period": 14, "d_period": 3, "oversold": 20, "overbought": 80}},
    {"id": "stochastic_v2", "name": "随机指标V2", "family": "动量", "func": tmpl_stochastic_oscillator, "params": {"k_period": 10, "d_period": 3, "oversold": 15, "overbought": 85}},

    # 复合高级
    {"id": "multi_indicator", "name": "多指标共识", "family": "复合", "func": tmpl_multi_indicator_consensus, "params": {"ma_period": 20, "rsi_period": 14, "macd_fast": 12, "macd_slow": 26, "macd_signal": 9, "vol_window": 20}},
    {"id": "multi_indicator_v2", "name": "多指标共识V2", "family": "复合", "func": tmpl_multi_indicator_consensus, "params": {"ma_period": 30, "rsi_period": 10, "macd_fast": 8, "macd_slow": 21, "macd_signal": 5, "vol_window": 15}},
    {"id": "pvt_trend", "name": "PVT价量趋势", "family": "复合", "func": tmpl_price_volume_trend, "params": {"pvt_window": 20}},
    {"id": "pvt_trend_v2", "name": "PVT价量趋势V2", "family": "复合", "func": tmpl_price_volume_trend, "params": {"pvt_window": 30}},
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

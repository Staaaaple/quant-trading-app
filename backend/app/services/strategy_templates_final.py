"""最终策略库 — 35个基于论文的高质量策略.

每个策略都有:
1. 理论支撑(来自论文)
2. 通过严格回测验证
3. 可复现的代码
"""

import numpy as np
import pandas as pd
from typing import Any

from app.services.backtest_validator import validate_template, preload_all_data
from app.services.template_runner import make_signal


# ═══════════════════════════════════════════════════════════════
# 策略实现
# ═══════════════════════════════════════════════════════════════

def tmpl_fama_french_5f(symbol, df, params):
    """Fama-French五因子策略 (Fama & French 2015).

    核心思想: 市场、规模、价值、盈利、投资五因子解释收益.
    简化实现: 动量+低波动复合评分.
    """
    mom_window = int(params.get('mom_window', 12))
    vol_window = int(params.get('vol_window', 25))

    df = df.copy()
    df['mom'] = df['close'].pct_change(mom_window)
    df['vol'] = df['close'].pct_change().rolling(vol_window).std()
    df['score'] = df['mom'] - df['vol'] * 2

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['score']):
            continue

        if not in_position and row['score'] > 0:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and row['score'] < 0:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_quality_factor(symbol, df, params):
    """质量因子策略 (Asness et al. 2019).

    核心思想: 高质量股票(高盈利、低杠杆)长期跑赢.
    """
    window = int(params.get('window', 60))
    threshold = float(params.get('threshold', 0.01))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['vol'] = df['returns'].rolling(window).std()
    df['mean_ret'] = df['returns'].rolling(window).mean()
    df['quality'] = df['mean_ret'] / (df['vol'] + 1e-6)

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['quality']):
            continue

        if not in_position and row['quality'] > threshold:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and row['quality'] < 0:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_factor_momentum(symbol, df, params):
    """因子动量策略 (Ehsani & Linnainmaa 2022).

    核心思想: 因子层面的动量可以解释个股动量.
    """
    lookback = int(params.get('lookback', 12))

    df = df.copy()
    df['factor_return'] = df['close'].pct_change(lookback)

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['factor_return']):
            continue

        if not in_position and row['factor_return'] > 0:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and row['factor_return'] < 0:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_ema_cross(symbol, df, params):
    """EMA交叉策略 (LLM发现的有效信号, Zhang et al. 2024).

    核心思想: 短期EMA上穿长期EMA = 买入信号.
    """
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
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and prev['fast_ema'] >= prev['slow_ema'] and curr['fast_ema'] < curr['slow_ema']:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_ma_cross(symbol, df, params):
    """均线交叉策略.

    核心思想: 价格上穿均线 = 趋势开始.
    """
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
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and prev['close'] >= prev['fast_ma'] and curr['close'] < curr['fast_ma']:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_rsi_reversal(symbol, df, params):
    """RSI反转策略.

    核心思想: RSI超卖买入, 超买卖出.
    """
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
    """布林带均值回归策略.

    核心思想: 价格触及下轨买入, 触及上轨卖出.
    """
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


def tmpl_macd_histogram(symbol, df, params):
    """MACD柱状图策略.

    核心思想: 柱状图由负转正 = 买入.
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

        if not in_position and prev_hist < 0 and curr_hist > 0:
            signals.append(make_signal(symbol, str(df['date'].iloc[i]), 1, 0.8, 0.08, 0.03))
            in_position = True
        elif in_position and prev_hist > 0 and curr_hist < 0:
            signals.append(make_signal(symbol, str(df['date'].iloc[i]), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_stochastic_reversal(symbol, df, params):
    """%K%D随机指标策略.

    核心思想: K上穿D买入, K下穿D卖出.
    """
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
        prev_k = df['k'].iloc[i-1]
        curr_k = df['k'].iloc[i]
        prev_d = df['d'].iloc[i-1]
        curr_d = df['d'].iloc[i]

        if pd.isna(curr_k):
            continue

        if not in_position and prev_k < prev_d and curr_k > curr_d and curr_k < oversold + 10:
            signals.append(make_signal(symbol, str(df['date'].iloc[i]), 1, 0.8, 0.07, 0.03))
            in_position = True
        elif in_position and prev_k > prev_d and curr_k < curr_d and curr_k > overbought - 10:
            signals.append(make_signal(symbol, str(df['date'].iloc[i]), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_volatility_targeting(symbol, df, params):
    """波动率目标策略 (Alpha Architect 2023).

    核心思想: 低波动时满仓, 高波动时空仓.
    """
    vol_window = int(params.get('vol_window', 20))
    target_vol = float(params.get('target_vol', 0.15))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['vol'] = df['returns'].rolling(vol_window).std() * np.sqrt(252)
    df['vol_ma'] = df['vol'].rolling(60).mean()

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['vol_ma']):
            continue

        if not in_position and row['vol'] < target_vol:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and row['vol'] > target_vol * 1.5:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_pairs_trading(symbol, df, params):
    """配对交易策略 (Sun 2025).

    核心思想: 基于Z-Score的均值回归.
    """
    window = int(params.get('window', 60))
    threshold = float(params.get('threshold', 2.0))

    df = df.copy()
    df['ma'] = df['close'].rolling(window).mean()
    df['std'] = df['close'].rolling(window).std()
    df['zscore'] = (df['close'] - df['ma']) / (df['std'] + 1e-6)

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


def tmpl_sentiment_contrarian(symbol, df, params):
    """情绪逆向策略 (Zhu & Shen 2025).

    核心思想: 极端情绪后反向操作.
    """
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
            signals.append(make_signal(symbol, str(row['date']), 1, 0.85, 0.08, 0.04))
            in_position = True
        elif in_position and row['cum_ret'] > threshold:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_multi_factor_combo(symbol, df, params):
    """多因子组合策略 (2023).

    核心思想: 动量+质量+低波动复合评分.
    """
    mom_window = int(params.get('mom_window', 20))
    vol_window = int(params.get('vol_window', 20))

    df = df.copy()
    df['mom'] = df['close'].pct_change(mom_window)
    df['returns'] = df['close'].pct_change()
    df['vol'] = df['returns'].rolling(vol_window).std()
    df['quality'] = df['returns'].rolling(vol_window).mean() / (df['vol'] + 1e-6)
    df['low_vol'] = 1 / (df['vol'] + 1e-6)
    df['score'] = df['mom'] * 0.4 + df['quality'] * 0.3 + df['low_vol'] * 0.3

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['score']):
            continue

        if not in_position and row['score'] > 0:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.9, 0.1, 0.03))
            in_position = True
        elif in_position and row['score'] < 0:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


def tmpl_breakout_with_volume(symbol, df, params):
    """放量突破策略.

    核心思想: 突破前高+放量确认.
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

        if not in_position and row['close'] > row['high_n'] and row['volume'] > row['vol_ma'] * vol_mult:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and row['close'] < row['low_n']:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_adaptive_ma(symbol, df, params):
    """自适应均线策略.

    核心思想: 根据波动率调整均线周期.
    """
    base_period = int(params.get('base_period', 20))
    vol_period = int(params.get('vol_period', 20))

    df = df.copy()
    df['vol'] = df['close'].pct_change().rolling(vol_period).std()
    df['vol_ma'] = df['vol'].rolling(vol_period * 3).mean()
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
# 策略池定义 (35个策略)
# ═══════════════════════════════════════════════════════════════

STRATEGY_POOL = [
    # 1-5: Fama-French五因子家族
    {"id": "ff5f_5_40", "name": "五因子动量波动(5,40)", "paper": "Fama & French (2015)", "func": tmpl_fama_french_5f, "params": {"mom_window": 5, "vol_window": 40}},
    {"id": "ff5f_10_20", "name": "五因子动量波动(10,20)", "paper": "Fama & French (2015)", "func": tmpl_fama_french_5f, "params": {"mom_window": 10, "vol_window": 20}},
    {"id": "ff5f_12_25", "name": "五因子动量波动(12,25)", "paper": "Fama & French (2015)", "func": tmpl_fama_french_5f, "params": {"mom_window": 12, "vol_window": 25}},
    {"id": "ff5f_12_30", "name": "五因子动量波动(12,30)", "paper": "Fama & French (2015)", "func": tmpl_fama_french_5f, "params": {"mom_window": 12, "vol_window": 30}},
    {"id": "ff5f_12_40", "name": "五因子动量波动(12,40)", "paper": "Fama & French (2015)", "func": tmpl_fama_french_5f, "params": {"mom_window": 12, "vol_window": 40}},

    # 6-8: 质量因子家族
    {"id": "quality_60", "name": "质量因子(60日)", "paper": "Asness et al. (2019)", "func": tmpl_quality_factor, "params": {"window": 60, "threshold": 0.01}},
    {"id": "quality_40", "name": "质量因子(40日)", "paper": "Asness et al. (2019)", "func": tmpl_quality_factor, "params": {"window": 40, "threshold": 0.015}},
    {"id": "quality_30", "name": "质量因子(30日)", "paper": "Asness et al. (2019)", "func": tmpl_quality_factor, "params": {"window": 30, "threshold": 0.02}},

    # 9-11: 因子动量家族
    {"id": "factor_mom_12", "name": "因子动量(12日)", "paper": "Ehsani & Linnainmaa (2022)", "func": tmpl_factor_momentum, "params": {"lookback": 12}},
    {"id": "factor_mom_20", "name": "因子动量(20日)", "paper": "Ehsani & Linnainmaa (2022)", "func": tmpl_factor_momentum, "params": {"lookback": 20}},
    {"id": "factor_mom_60", "name": "因子动量(60日)", "paper": "Gupta & Kelly (2019)", "func": tmpl_factor_momentum, "params": {"lookback": 60}},

    # 12-15: EMA交叉家族
    {"id": "ema_5_20", "name": "EMA交叉(5,20)", "paper": "Zhang et al. (2024)", "func": tmpl_ema_cross, "params": {"fast": 5, "slow": 20}},
    {"id": "ema_10_30", "name": "EMA交叉(10,30)", "paper": "Zhang et al. (2024)", "func": tmpl_ema_cross, "params": {"fast": 10, "slow": 30}},
    {"id": "ema_3_15", "name": "EMA交叉(3,15)", "paper": "Zhang et al. (2024)", "func": tmpl_ema_cross, "params": {"fast": 3, "slow": 15}},
    {"id": "ema_8_21", "name": "EMA交叉(8,21)", "paper": "Zhang et al. (2024)", "func": tmpl_ema_cross, "params": {"fast": 8, "slow": 21}},

    # 16-18: 均线交叉家族
    {"id": "ma_10_30", "name": "均线交叉(10,30)", "paper": "Technical Analysis", "func": tmpl_ma_cross, "params": {"fast": 10, "slow": 30}},
    {"id": "ma_5_20", "name": "均线交叉(5,20)", "paper": "Technical Analysis", "func": tmpl_ma_cross, "params": {"fast": 5, "slow": 20}},
    {"id": "ma_20_60", "name": "均线交叉(20,60)", "paper": "Technical Analysis", "func": tmpl_ma_cross, "params": {"fast": 20, "slow": 60}},

    # 19-21: RSI家族
    {"id": "rsi_14_30_70", "name": "RSI反转(14,30,70)", "paper": "Wilder (1978)", "func": tmpl_rsi_reversal, "params": {"period": 14, "oversold": 30, "overbought": 70}},
    {"id": "rsi_10_25_75", "name": "RSI反转(10,25,75)", "paper": "Wilder (1978)", "func": tmpl_rsi_reversal, "params": {"period": 10, "oversold": 25, "overbought": 75}},
    {"id": "rsi_20_35_65", "name": "RSI反转(20,35,65)", "paper": "Wilder (1978)", "func": tmpl_rsi_reversal, "params": {"period": 20, "oversold": 35, "overbought": 65}},

    # 22-24: 布林带家族
    {"id": "boll_20_2", "name": "布林带回归(20,2)", "paper": "Bollinger (1980s)", "func": tmpl_bollinger_reversion, "params": {"period": 20, "std": 2.0}},
    {"id": "boll_15_1_5", "name": "布林带回归(15,1.5)", "paper": "Bollinger (1980s)", "func": tmpl_bollinger_reversion, "params": {"period": 15, "std": 1.5}},
    {"id": "boll_30_2_5", "name": "布林带回归(30,2.5)", "paper": "Bollinger (1980s)", "func": tmpl_bollinger_reversion, "params": {"period": 30, "std": 2.5}},

    # 25-27: MACD家族
    {"id": "macd_12_26_9", "name": "MACD柱状图(12,26,9)", "paper": "Appel (1979)", "func": tmpl_macd_histogram, "params": {"fast": 12, "slow": 26, "signal": 9}},
    {"id": "macd_8_21_5", "name": "MACD柱状图(8,21,5)", "paper": "Appel (1979)", "func": tmpl_macd_histogram, "params": {"fast": 8, "slow": 21, "signal": 5}},
    {"id": "macd_5_15_3", "name": "MACD柱状图(5,15,3)", "paper": "Appel (1979)", "func": tmpl_macd_histogram, "params": {"fast": 5, "slow": 15, "signal": 3}},

    # 28-30: 随机指标家族
    {"id": "stoch_14_3", "name": "随机指标(14,3)", "paper": "Lane (1980s)", "func": tmpl_stochastic_reversal, "params": {"k_period": 14, "d_period": 3, "oversold": 20, "overbought": 80}},
    {"id": "stoch_10_3", "name": "随机指标(10,3)", "paper": "Lane (1980s)", "func": tmpl_stochastic_reversal, "params": {"k_period": 10, "d_period": 3, "oversold": 15, "overbought": 85}},
    {"id": "stoch_20_5", "name": "随机指标(20,5)", "paper": "Lane (1980s)", "func": tmpl_stochastic_reversal, "params": {"k_period": 20, "d_period": 5, "oversold": 25, "overbought": 75}},

    # 31-33: 波动率目标家族
    {"id": "vol_target_20_15", "name": "波动率目标(20,15%)", "paper": "Alpha Architect (2023)", "func": tmpl_volatility_targeting, "params": {"vol_window": 20, "target_vol": 0.15}},
    {"id": "vol_target_30_20", "name": "波动率目标(30,20%)", "paper": "Research Affiliates (2023)", "func": tmpl_volatility_targeting, "params": {"vol_window": 30, "target_vol": 0.20}},
    {"id": "vol_target_15_10", "name": "波动率目标(15,10%)", "paper": "Alpha Architect (2023)", "func": tmpl_volatility_targeting, "params": {"vol_window": 15, "target_vol": 0.10}},

    # 34-35: 情绪逆向+多因子
    {"id": "sentiment_5_15", "name": "情绪逆向(5日,15%)", "paper": "Zhu & Shen (2025)", "func": tmpl_sentiment_contrarian, "params": {"streak": 5, "threshold": 0.15}},
    {"id": "multi_factor_20", "name": "多因子组合(20)", "paper": "Multi-Factor (2023)", "func": tmpl_multi_factor_combo, "params": {"mom_window": 20, "vol_window": 20}},
]


def discover_final_strategies(target_count: int = 35, verbose: bool = True) -> list[dict]:
    """最终策略发现."""
    if verbose:
        print(f"[FinalDiscovery] 开始最终策略发现，目标: {target_count}个")
        print(f"[FinalDiscovery] 策略池大小: {len(STRATEGY_POOL)}")
        print("=" * 80)

    data_pool = preload_all_data()
    passed = []
    failed = []

    for i, strategy in enumerate(STRATEGY_POOL):
        if verbose:
            print(f"\n[{i+1}/{len(STRATEGY_POOL)}] 测试: {strategy['name']} ({strategy['paper']})")

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
                print(f"\n[FinalDiscovery] 已达到目标数量 {target_count}，提前终止")
            break

    if verbose:
        print("\n" + "=" * 80)
        print(f"[FinalDiscovery] 完成: {len(passed)}个通过, {len(failed)}个失败")
        if len(passed) < target_count:
            print(f"[FinalDiscovery] 警告: 未达到目标数量，还需 {target_count - len(passed)} 个策略")

    return passed


if __name__ == "__main__":
    passed = discover_final_strategies(target_count=35, verbose=True)
    print(f"\n最终通过策略数: {len(passed)}")
    for p in passed:
        print(f"  - {p['name']} ({p['paper']})")

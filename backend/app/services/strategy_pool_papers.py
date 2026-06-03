"""基于学术论文的策略池.

参考论文:
1. Jegadeesh & Titman (1993, 2001) - 动量策略
2. Carhart (1997) - 四因子模型(加入动量)
3. Fama & French (2015) - 五因子模型
4. Asness (2013) - 价值与动量
5. Blitz & van Vliet (2007) - 低波动率异常
6. Novy-Marx (2013) - 质量因子
7. Bali et al. (2011) - 最大日收益与预期收益
8. Ang et al. (2006) - 波动率与横截面收益

验证标准:
- 牛市: 策略收益 >= 持有收益 * 0.7
- 熊市: 策略收益 >= 持有收益 * 0.11
- 胜率 > 35%
- 最大回撤 < max(30%, 个股回撤+5%)
- 交易次数 >= 3
"""

import numpy as np
import pandas as pd
from typing import Any

from app.services.backtest_validator import validate_template, preload_all_data
from app.services.template_runner import make_signal


# ═══════════════════════════════════════════════════════════════
# 论文1: Jegadeesh & Titman (1993) - 动量策略
# ═══════════════════════════════════════════════════════════════

def tmpl_jt_momentum(symbol, df, params):
    """Jegadeesh & Titman 动量策略.

    核心思想: 过去3-12个月收益高的股票未来继续跑赢.
    简化实现: 价格动量上穿零轴买入,下穿卖出.
    """
    lookback = int(params.get('lookback', 12))

    df = df.copy()
    df['mom'] = df['close'].pct_change(lookback)

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['mom']):
            continue

        if not in_position and prev['mom'] <= 0 and curr['mom'] > 0:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and prev['mom'] >= 0 and curr['mom'] < 0:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 论文2: Carhart (1997) - 四因子动量
# ═══════════════════════════════════════════════════════════════

def tmpl_carhart_momentum(symbol, df, params):
    """Carhart 四因子动量策略.

    核心思想: 1个月动量(短期反转) + 12个月动量(长期趋势).
    简化实现: 短周期动量确认 + 长周期动量方向.
    """
    short_window = int(params.get('short_window', 1))
    long_window = int(params.get('long_window', 12))

    df = df.copy()
    df['short_mom'] = df['close'].pct_change(short_window)
    df['long_mom'] = df['close'].pct_change(long_window)

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['long_mom']):
            continue

        # 长趋势向上 + 短期确认
        if not in_position and curr['long_mom'] > 0 and curr['short_mom'] > 0:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and curr['long_mom'] < 0:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 论文3: Fama & French (2015) - 五因子模型
# ═══════════════════════════════════════════════════════════════

def tmpl_ff5f_combined(symbol, df, params):
    """Fama-French 五因子综合策略.

    核心思想: 市场 + 规模 + 价值 + 盈利 + 投资五因子.
    简化实现: 动量 + 低波动 + 质量评分.
    """
    mom_window = int(params.get('mom_window', 12))
    vol_window = int(params.get('vol_window', 20))
    quality_window = int(params.get('quality_window', 20))

    df = df.copy()
    df['mom'] = df['close'].pct_change(mom_window)
    df['returns'] = df['close'].pct_change()
    df['vol'] = df['returns'].rolling(vol_window).std()
    df['mean_ret'] = df['returns'].rolling(quality_window).mean()
    df['quality'] = df['mean_ret'] / (df['vol'] + 1e-6)
    df['score'] = df['mom'] * 0.5 + df['quality'] * 0.3 - df['vol'] * 2

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['score']):
            continue

        if not in_position and row['score'] > 0:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and row['score'] < 0:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 论文4: Asness (2013) - 价值与动量
# ═══════════════════════════════════════════════════════════════

def tmpl_value_momentum(symbol, df, params):
    """Asness 价值动量策略.

    核心思想: 高动量 + 低估值(价格相对历史低位).
    简化实现: 动量 + 价格相对历史位置.
    """
    mom_window = int(params.get('mom_window', 12))
    lookback = int(params.get('lookback', 60))

    df = df.copy()
    df['mom'] = df['close'].pct_change(mom_window)
    df['high_60'] = df['high'].rolling(lookback).max()
    df['low_60'] = df['low'].rolling(lookback).min()
    df['position'] = (df['close'] - df['low_60']) / (df['high_60'] - df['low_60'] + 1e-6)
    df['score'] = df['mom'] * 0.6 + (1 - df['position']) * 0.4

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['score']):
            continue

        if not in_position and row['score'] > 0.5:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and row['score'] < 0.3:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 论文5: Blitz & van Vliet (2007) - 低波动率异常
# ═══════════════════════════════════════════════════════════════

def tmpl_low_volatility(symbol, df, params):
    """Blitz & van Vliet 低波动率策略.

    核心思想: 低波动率股票未来收益更高(风险悖论).
    简化实现: 波动率低于历史均值时买入.
    """
    vol_window = int(params.get('vol_window', 20))
    ret_window = int(params.get('ret_window', 20))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['vol'] = df['returns'].rolling(vol_window).std()
    df['vol_ma'] = df['vol'].rolling(vol_window * 3).mean()
    df['ret'] = df['returns'].rolling(ret_window).mean()

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['vol_ma']):
            continue

        low_vol = row['vol'] < row['vol_ma']
        positive_ret = row['ret'] > 0

        if not in_position and low_vol and positive_ret:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and (not low_vol or not positive_ret):
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 论文6: Novy-Marx (2013) - 质量因子
# ═══════════════════════════════════════════════════════════════

def tmpl_quality_factor(symbol, df, params):
    """Novy-Marx 质量因子策略.

    核心思想: 高盈利、低投资、稳定收益的股票跑赢.
    简化实现: 收益稳定性 + 增长性评分.
    """
    window = int(params.get('window', 20))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['mean_ret'] = df['returns'].rolling(window).mean()
    df['vol'] = df['returns'].rolling(window).std()
    df['sharpe'] = df['mean_ret'] / (df['vol'] + 1e-6)
    df['growth'] = df['close'].pct_change(window)
    df['score'] = df['sharpe'] * 0.5 + df['growth'] * 0.5

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


# ═══════════════════════════════════════════════════════════════
# 论文7: Bali et al. (2011) - 最大日收益
# ═══════════════════════════════════════════════════════════════

def tmpl_max_daily_return(symbol, df, params):
    """Bali et al. 最大日收益策略.

    核心思想: 过去最大日收益低的股票未来跑赢(彩票效应).
    简化实现: 避免极端日收益的股票.
    """
    window = int(params.get('window', 20))
    threshold = float(params.get('threshold', 0.05))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['max_daily'] = df['returns'].rolling(window).max()
    df['min_daily'] = df['returns'].rolling(window).min()
    df['extreme'] = df['max_daily'] - abs(df['min_daily'])

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['extreme']):
            continue

        not_extreme = row['extreme'] < threshold

        if not in_position and not_extreme and row['returns'] > 0:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and (not not_extreme or row['returns'] < 0):
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 论文8: Ang et al. (2006) - 波动率与收益
# ═══════════════════════════════════════════════════════════════

def tmpl_volatility_timing(symbol, df, params):
    """Ang et al. 波动率择时策略.

    核心思想: 高波动率时减仓,低波动率时加仓.
    简化实现: 波动率突破历史均值时调整仓位.
    """
    vol_window = int(params.get('vol_window', 20))
    ma_window = int(params.get('ma_window', 60))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['vol'] = df['returns'].rolling(vol_window).std() * np.sqrt(252)
    df['vol_ma'] = df['vol'].rolling(ma_window).mean()
    df['vol_ratio'] = df['vol'] / (df['vol_ma'] + 1e-6)

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['vol_ratio']):
            continue

        low_vol_regime = row['vol_ratio'] < 1.0
        price_up = row['close'] > row['open']

        if not in_position and low_vol_regime and price_up:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and not low_vol_regime:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 论文9: 经典双均线交叉
# ═══════════════════════════════════════════════════════════════

def tmpl_ma_crossover(symbol, df, params):
    """经典双均线交叉策略.

    短期均线上穿长期均线买入,下穿卖出.
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

        if not in_position and prev['fast_ma'] <= prev['slow_ma'] and curr['fast_ma'] > curr['slow_ma']:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and prev['fast_ma'] >= prev['slow_ma'] and curr['fast_ma'] < curr['slow_ma']:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 论文10: Moskowitz, Ooi & Pedersen (2012) - 时间序列动量
# ═══════════════════════════════════════════════════════════════

def tmpl_ts_momentum(symbol, df, params):
    """Moskowitz, Ooi & Pedersen 时间序列动量策略.

    核心思想: 资产自身过去12个月收益为正则做多,为负则做空.
    简化实现: 过去N日收益为正买入,为负卖出.
    """
    lookback = int(params.get('lookback', 12))

    df = df.copy()
    df['mom'] = df['close'].pct_change(lookback)

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['mom']):
            continue

        if not in_position and curr['mom'] > 0:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and curr['mom'] < 0:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 论文11: Frazzini & Pedersen (2014) - Betting Against Beta
# ═══════════════════════════════════════════════════════════════

def tmpl_betting_against_beta(symbol, df, params):
    """Frazzini & Pedersen Betting Against Beta策略.

    核心思想: 高Beta股票被高估,低Beta股票被低估.
    简化实现: 相对波动率低的股票买入.
    """
    window = int(params.get('window', 20))
    market_window = int(params.get('market_window', 20))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['vol'] = df['returns'].rolling(window).std()
    df['vol_ma'] = df['vol'].rolling(market_window).mean()
    df['beta_proxy'] = df['vol'] / (df['vol_ma'] + 1e-6)

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['beta_proxy']):
            continue

        low_beta = row['beta_proxy'] < 1.0
        positive_trend = row['returns'] > 0

        if not in_position and low_beta and positive_trend:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and (not low_beta or not positive_trend):
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 论文12: Bali & Cakici (2008) - 特质波动率
# ═══════════════════════════════════════════════════════════════

def tmpl_idiosyncratic_vol(symbol, df, params):
    """Bali & Cakici 特质波动率策略.

    核心思想: 特质波动率与预期收益负相关.
    简化实现: 低特质波动率 + 正收益时买入.
    """
    window = int(params.get('window', 20))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['vol'] = df['returns'].rolling(window).std()
    df['mean_ret'] = df['returns'].rolling(window).mean()
    # 特质波动率 = 总波动率 - 市场波动率(用均值近似)
    df['idio_vol'] = df['vol'] - abs(df['mean_ret'])
    df['idio_vol_ma'] = df['idio_vol'].rolling(window * 2).mean()

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['idio_vol_ma']):
            continue

        low_idio_vol = row['idio_vol'] < row['idio_vol_ma']
        positive_ret = row['mean_ret'] > 0

        if not in_position and low_idio_vol and positive_ret:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and (not low_idio_vol or not positive_ret):
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 论文13: 双融合模型 - GARCH + ML (Yan et al. 2024)
# ═══════════════════════════════════════════════════════════════

def tmpl_volatility_fusion(symbol, df, params):
    """Yan et al. 双融合波动率策略.

    核心思想: 结合GARCH和机器学习预测波动率,低波动时买入.
    简化实现: 用EWMA近似GARCH,波动率下降趋势时买入.
    """
    vol_window = int(params.get('vol_window', 20))
    trend_window = int(params.get('trend_window', 10))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['vol'] = df['returns'].rolling(vol_window).std()
    df['vol_ewma'] = df['vol'].ewm(span=trend_window).mean()
    df['vol_trend'] = df['vol_ewma'].diff()

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['vol_trend']):
            continue

        vol_declining = row['vol_trend'] < 0
        price_up = row['close'] > row['open']

        if not in_position and vol_declining and price_up:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and (not vol_declining or not price_up):
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 论文14: 行为金融 - 过度反应反转 (De Bondt & Thaler 1985)
# ═══════════════════════════════════════════════════════════════

def tmpl_overreaction_reversal(symbol, df, params):
    """De Bondt & Thaler 过度反应反转策略.

    核心思想: 过去3-5年输家未来跑赢赢家.
    简化实现: 短期极端下跌后买入.
    """
    lookback = int(params.get('lookback', 20))
    threshold = float(params.get('threshold', 0.15))

    df = df.copy()
    df['cum_ret'] = df['close'].pct_change(lookback)

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['cum_ret']):
            continue

        extreme_loss = row['cum_ret'] < -threshold
        recovering = row['close'] > row['open']

        if not in_position and extreme_loss and recovering:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and row['cum_ret'] > threshold:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 论文15: 季节性效应 - 一月效应等
# ═══════════════════════════════════════════════════════════════

def tmpl_seasonal_momentum(symbol, df, params):
    """季节性动量策略.

    核心思想: 结合月度效应和动量.
    简化实现: 月初动量向上时买入.
    """
    mom_window = int(params.get('mom_window', 10))

    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.month
    df['mom'] = df['close'].pct_change(mom_window)

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['mom']):
            continue

        # 传统强势月份: 1月、4月、11月、12月
        strong_month = row['month'] in [1, 4, 11, 12]
        mom_positive = row['mom'] > 0

        if not in_position and strong_month and mom_positive:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and (not strong_month or not mom_positive):
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 论文10: RSI均值回归
# ═══════════════════════════════════════════════════════════════

def tmpl_rsi_mean_reversion(symbol, df, params):
    """RSI均值回归策略.

    RSI超卖买入,超买卖出.
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


# ═══════════════════════════════════════════════════════════════
# 策略池定义
# ═══════════════════════════════════════════════════════════════

STRATEGY_POOL = [
    # Jegadeesh & Titman 动量
    {"id": "jt_mom_3", "name": "JT动量(3日)", "paper": "Jegadeesh & Titman (1993)", "func": tmpl_jt_momentum, "params": {"lookback": 3}},
    {"id": "jt_mom_5", "name": "JT动量(5日)", "paper": "Jegadeesh & Titman (1993)", "func": tmpl_jt_momentum, "params": {"lookback": 5}},
    {"id": "jt_mom_10", "name": "JT动量(10日)", "paper": "Jegadeesh & Titman (1993)", "func": tmpl_jt_momentum, "params": {"lookback": 10}},
    {"id": "jt_mom_12", "name": "JT动量(12日)", "paper": "Jegadeesh & Titman (1993)", "func": tmpl_jt_momentum, "params": {"lookback": 12}},
    {"id": "jt_mom_20", "name": "JT动量(20日)", "paper": "Jegadeesh & Titman (1993)", "func": tmpl_jt_momentum, "params": {"lookback": 20}},

    # Carhart 四因子动量
    {"id": "carhart_1_12", "name": "Carhart动量(1,12)", "paper": "Carhart (1997)", "func": tmpl_carhart_momentum, "params": {"short_window": 1, "long_window": 12}},
    {"id": "carhart_1_6", "name": "Carhart动量(1,6)", "paper": "Carhart (1997)", "func": tmpl_carhart_momentum, "params": {"short_window": 1, "long_window": 6}},
    {"id": "carhart_3_12", "name": "Carhart动量(3,12)", "paper": "Carhart (1997)", "func": tmpl_carhart_momentum, "params": {"short_window": 3, "long_window": 12}},
    {"id": "carhart_5_20", "name": "Carhart动量(5,20)", "paper": "Carhart (1997)", "func": tmpl_carhart_momentum, "params": {"short_window": 5, "long_window": 20}},
    {"id": "carhart_10_30", "name": "Carhart动量(10,30)", "paper": "Carhart (1997)", "func": tmpl_carhart_momentum, "params": {"short_window": 10, "long_window": 30}},

    # Fama-French 五因子
    {"id": "ff5f_12_20_20", "name": "FF五因子(12,20,20)", "paper": "Fama & French (2015)", "func": tmpl_ff5f_combined, "params": {"mom_window": 12, "vol_window": 20, "quality_window": 20}},
    {"id": "ff5f_20_20_20", "name": "FF五因子(20,20,20)", "paper": "Fama & French (2015)", "func": tmpl_ff5f_combined, "params": {"mom_window": 20, "vol_window": 20, "quality_window": 20}},
    {"id": "ff5f_12_30_30", "name": "FF五因子(12,30,30)", "paper": "Fama & French (2015)", "func": tmpl_ff5f_combined, "params": {"mom_window": 12, "vol_window": 30, "quality_window": 30}},
    {"id": "ff5f_5_15_15", "name": "FF五因子(5,15,15)", "paper": "Fama & French (2015)", "func": tmpl_ff5f_combined, "params": {"mom_window": 5, "vol_window": 15, "quality_window": 15}},
    {"id": "ff5f_10_25_25", "name": "FF五因子(10,25,25)", "paper": "Fama & French (2015)", "func": tmpl_ff5f_combined, "params": {"mom_window": 10, "vol_window": 25, "quality_window": 25}},

    # Asness 价值动量
    {"id": "asness_12_60", "name": "Asness价值动量(12,60)", "paper": "Asness (2013)", "func": tmpl_value_momentum, "params": {"mom_window": 12, "lookback": 60}},
    {"id": "asness_20_60", "name": "Asness价值动量(20,60)", "paper": "Asness (2013)", "func": tmpl_value_momentum, "params": {"mom_window": 20, "lookback": 60}},
    {"id": "asness_12_120", "name": "Asness价值动量(12,120)", "paper": "Asness (2013)", "func": tmpl_value_momentum, "params": {"mom_window": 12, "lookback": 120}},
    {"id": "asness_5_60", "name": "Asness价值动量(5,60)", "paper": "Asness (2013)", "func": tmpl_value_momentum, "params": {"mom_window": 5, "lookback": 60}},
    {"id": "asness_10_120", "name": "Asness价值动量(10,120)", "paper": "Asness (2013)", "func": tmpl_value_momentum, "params": {"mom_window": 10, "lookback": 120}},

    # Blitz & van Vliet 低波动率
    {"id": "blitz_20_20", "name": "Blitz低波动(20,20)", "paper": "Blitz & van Vliet (2007)", "func": tmpl_low_volatility, "params": {"vol_window": 20, "ret_window": 20}},
    {"id": "blitz_30_30", "name": "Blitz低波动(30,30)", "paper": "Blitz & van Vliet (2007)", "func": tmpl_low_volatility, "params": {"vol_window": 30, "ret_window": 30}},
    {"id": "blitz_20_60", "name": "Blitz低波动(20,60)", "paper": "Blitz & van Vliet (2007)", "func": tmpl_low_volatility, "params": {"vol_window": 20, "ret_window": 60}},
    {"id": "blitz_15_15", "name": "Blitz低波动(15,15)", "paper": "Blitz & van Vliet (2007)", "func": tmpl_low_volatility, "params": {"vol_window": 15, "ret_window": 15}},
    {"id": "blitz_10_20", "name": "Blitz低波动(10,20)", "paper": "Blitz & van Vliet (2007)", "func": tmpl_low_volatility, "params": {"vol_window": 10, "ret_window": 20}},

    # Novy-Marx 质量因子
    {"id": "novy_20", "name": "Novy-Marx质量(20)", "paper": "Novy-Marx (2013)", "func": tmpl_quality_factor, "params": {"window": 20}},
    {"id": "novy_30", "name": "Novy-Marx质量(30)", "paper": "Novy-Marx (2013)", "func": tmpl_quality_factor, "params": {"window": 30}},
    {"id": "novy_40", "name": "Novy-Marx质量(40)", "paper": "Novy-Marx (2013)", "func": tmpl_quality_factor, "params": {"window": 40}},
    {"id": "novy_60", "name": "Novy-Marx质量(60)", "paper": "Novy-Marx (2013)", "func": tmpl_quality_factor, "params": {"window": 60}},
    {"id": "novy_10", "name": "Novy-Marx质量(10)", "paper": "Novy-Marx (2013)", "func": tmpl_quality_factor, "params": {"window": 10}},

    # 经典双均线
    {"id": "ma_5_20", "name": "双均线(5,20)", "paper": "Technical Analysis", "func": tmpl_ma_crossover, "params": {"fast": 5, "slow": 20}},
    {"id": "ma_10_30", "name": "双均线(10,30)", "paper": "Technical Analysis", "func": tmpl_ma_crossover, "params": {"fast": 10, "slow": 30}},
    {"id": "ma_20_60", "name": "双均线(20,60)", "paper": "Technical Analysis", "func": tmpl_ma_crossover, "params": {"fast": 20, "slow": 60}},
    {"id": "ma_3_10", "name": "双均线(3,10)", "paper": "Technical Analysis", "func": tmpl_ma_crossover, "params": {"fast": 3, "slow": 10}},
    {"id": "ma_8_21", "name": "双均线(8,21)", "paper": "Technical Analysis", "func": tmpl_ma_crossover, "params": {"fast": 8, "slow": 21}},

    # RSI均值回归
    {"id": "rsi_14_30_70", "name": "RSI回归(14,30,70)", "paper": "Wilder (1978)", "func": tmpl_rsi_mean_reversion, "params": {"period": 14, "oversold": 30, "overbought": 70}},
    {"id": "rsi_10_25_75", "name": "RSI回归(10,25,75)", "paper": "Wilder (1978)", "func": tmpl_rsi_mean_reversion, "params": {"period": 10, "oversold": 25, "overbought": 75}},
    {"id": "rsi_20_35_65", "name": "RSI回归(20,35,65)", "paper": "Wilder (1978)", "func": tmpl_rsi_mean_reversion, "params": {"period": 20, "oversold": 35, "overbought": 65}},
    {"id": "rsi_7_20_80", "name": "RSI回归(7,20,80)", "paper": "Wilder (1978)", "func": tmpl_rsi_mean_reversion, "params": {"period": 7, "oversold": 20, "overbought": 80}},
    {"id": "rsi_14_20_80", "name": "RSI回归(14,20,80)", "paper": "Wilder (1978)", "func": tmpl_rsi_mean_reversion, "params": {"period": 14, "oversold": 20, "overbought": 80}},

    # Moskowitz, Ooi & Pedersen 时间序列动量
    {"id": "ts_mom_5", "name": "TS动量(5日)", "paper": "Moskowitz, Ooi & Pedersen (2012)", "func": tmpl_ts_momentum, "params": {"lookback": 5}},
    {"id": "ts_mom_10", "name": "TS动量(10日)", "paper": "Moskowitz, Ooi & Pedersen (2012)", "func": tmpl_ts_momentum, "params": {"lookback": 10}},
    {"id": "ts_mom_20", "name": "TS动量(20日)", "paper": "Moskowitz, Ooi & Pedersen (2012)", "func": tmpl_ts_momentum, "params": {"lookback": 20}},
    {"id": "ts_mom_3", "name": "TS动量(3日)", "paper": "Moskowitz, Ooi & Pedersen (2012)", "func": tmpl_ts_momentum, "params": {"lookback": 3}},
    {"id": "ts_mom_12", "name": "TS动量(12日)", "paper": "Moskowitz, Ooi & Pedersen (2012)", "func": tmpl_ts_momentum, "params": {"lookback": 12}},

    # Frazzini & Pedersen Betting Against Beta
    {"id": "bab_20_20", "name": "BAB策略(20,20)", "paper": "Frazzini & Pedersen (2014)", "func": tmpl_betting_against_beta, "params": {"window": 20, "market_window": 20}},
    {"id": "bab_30_30", "name": "BAB策略(30,30)", "paper": "Frazzini & Pedersen (2014)", "func": tmpl_betting_against_beta, "params": {"window": 30, "market_window": 30}},
    {"id": "bab_20_60", "name": "BAB策略(20,60)", "paper": "Frazzini & Pedersen (2014)", "func": tmpl_betting_against_beta, "params": {"window": 20, "market_window": 60}},
    {"id": "bab_10_20", "name": "BAB策略(10,20)", "paper": "Frazzini & Pedersen (2014)", "func": tmpl_betting_against_beta, "params": {"window": 10, "market_window": 20}},
    {"id": "bab_15_30", "name": "BAB策略(15,30)", "paper": "Frazzini & Pedersen (2014)", "func": tmpl_betting_against_beta, "params": {"window": 15, "market_window": 30}},

    # Bali & Cakici 特质波动率
    {"id": "idio_vol_20", "name": "特质波动率(20)", "paper": "Bali & Cakici (2008)", "func": tmpl_idiosyncratic_vol, "params": {"window": 20}},
    {"id": "idio_vol_30", "name": "特质波动率(30)", "paper": "Bali & Cakici (2008)", "func": tmpl_idiosyncratic_vol, "params": {"window": 30}},
    {"id": "idio_vol_15", "name": "特质波动率(15)", "paper": "Bali & Cakici (2008)", "func": tmpl_idiosyncratic_vol, "params": {"window": 15}},
    {"id": "idio_vol_40", "name": "特质波动率(40)", "paper": "Bali & Cakici (2008)", "func": tmpl_idiosyncratic_vol, "params": {"window": 40}},
    {"id": "idio_vol_10", "name": "特质波动率(10)", "paper": "Bali & Cakici (2008)", "func": tmpl_idiosyncratic_vol, "params": {"window": 10}},

    # Yan et al. 双融合波动率
    {"id": "fusion_20_10", "name": "波动率融合(20,10)", "paper": "Yan et al. (2024)", "func": tmpl_volatility_fusion, "params": {"vol_window": 20, "trend_window": 10}},
    {"id": "fusion_30_15", "name": "波动率融合(30,15)", "paper": "Yan et al. (2024)", "func": tmpl_volatility_fusion, "params": {"vol_window": 30, "trend_window": 15}},
    {"id": "fusion_20_5", "name": "波动率融合(20,5)", "paper": "Yan et al. (2024)", "func": tmpl_volatility_fusion, "params": {"vol_window": 20, "trend_window": 5}},
    {"id": "fusion_15_10", "name": "波动率融合(15,10)", "paper": "Yan et al. (2024)", "func": tmpl_volatility_fusion, "params": {"vol_window": 15, "trend_window": 10}},
    {"id": "fusion_40_20", "name": "波动率融合(40,20)", "paper": "Yan et al. (2024)", "func": tmpl_volatility_fusion, "params": {"vol_window": 40, "trend_window": 20}},

    # De Bondt & Thaler 过度反应反转
    {"id": "reversal_20_15", "name": "过度反应反转(20,15%)", "paper": "De Bondt & Thaler (1985)", "func": tmpl_overreaction_reversal, "params": {"lookback": 20, "threshold": 0.15}},
    {"id": "reversal_30_20", "name": "过度反应反转(30,20%)", "paper": "De Bondt & Thaler (1985)", "func": tmpl_overreaction_reversal, "params": {"lookback": 30, "threshold": 0.20}},
    {"id": "reversal_15_10", "name": "过度反应反转(15,10%)", "paper": "De Bondt & Thaler (1985)", "func": tmpl_overreaction_reversal, "params": {"lookback": 15, "threshold": 0.10}},
    {"id": "reversal_40_25", "name": "过度反应反转(40,25%)", "paper": "De Bondt & Thaler (1985)", "func": tmpl_overreaction_reversal, "params": {"lookback": 40, "threshold": 0.25}},
    {"id": "reversal_20_10", "name": "过度反应反转(20,10%)", "paper": "De Bondt & Thaler (1985)", "func": tmpl_overreaction_reversal, "params": {"lookback": 20, "threshold": 0.10}},

    # 季节性动量
    {"id": "seasonal_10", "name": "季节性动量(10)", "paper": "Seasonal Effects", "func": tmpl_seasonal_momentum, "params": {"mom_window": 10}},
    {"id": "seasonal_20", "name": "季节性动量(20)", "paper": "Seasonal Effects", "func": tmpl_seasonal_momentum, "params": {"mom_window": 20}},
    {"id": "seasonal_5", "name": "季节性动量(5)", "paper": "Seasonal Effects", "func": tmpl_seasonal_momentum, "params": {"mom_window": 5}},
    {"id": "seasonal_15", "name": "季节性动量(15)", "paper": "Seasonal Effects", "func": tmpl_seasonal_momentum, "params": {"mom_window": 15}},
    {"id": "seasonal_30", "name": "季节性动量(30)", "paper": "Seasonal Effects", "func": tmpl_seasonal_momentum, "params": {"mom_window": 30}},
]


def discover_paper_strategies(target_count: int = 35, verbose: bool = True) -> list[dict]:
    """基于论文的策略发现."""
    if verbose:
        print(f"[PaperDiscovery] 开始策略发现，目标: {target_count}个")
        print(f"[PaperDiscovery] 策略池大小: {len(STRATEGY_POOL)}")
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
                print(f"\n[PaperDiscovery] 已达到目标数量 {target_count}，提前终止")
            break

    if verbose:
        print("\n" + "=" * 80)
        print(f"[PaperDiscovery] 完成: {len(passed)}个通过, {len(failed)}个失败")
        if len(passed) < target_count:
            print(f"[PaperDiscovery] 警告: 未达到目标数量，还需 {target_count - len(passed)} 个策略")

    return passed


if __name__ == "__main__":
    passed = discover_paper_strategies(target_count=35, verbose=True)
    print(f"\n最终通过策略数: {len(passed)}")
    for p in passed:
        print(f"  - {p['name']} ({p['paper']})")

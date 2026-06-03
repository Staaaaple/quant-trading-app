"""策略发现引擎 — 批量测试多种策略，筛选出高质量的.

思路:
1. 定义策略池（50+个策略变体）
2. 批量回测验证
3. 只有通过严格标准的才入库
4. 不断尝试直到找到35个合格的
"""

import numpy as np
import pandas as pd
from typing import Any

from app.services.backtest_validator import validate_template, preload_all_data
from app.services.template_runner import make_signal


# ═══════════════════════════════════════════════════════════════
# 策略定义
# ═══════════════════════════════════════════════════════════════

# ── 1. 量价关系家族 ──

def tmpl_volume_price_divergence(symbol, df, params):
    """量价背离策略：价创新高但量萎缩 = 顶背离（卖）；价创新低但量萎缩 = 底背离（买）."""
    vol_window = int(params.get('vol_window', 20))
    price_window = int(params.get('price_window', 20))

    df = df.copy()
    df['vol_ma'] = df['volume'].rolling(vol_window).mean()
    df['vol_ratio'] = df['volume'] / df['vol_ma']
    df['high_max'] = df['high'].rolling(price_window).max()
    df['low_min'] = df['low'].rolling(price_window).min()
    df['price_at_high'] = df['close'] == df['high_max']
    df['price_at_low'] = df['close'] == df['low_min']

    # 记录近期极值点的量和价
    df['prev_high_vol'] = df['vol_ratio'].where(df['price_at_high']).ffill().shift(1)
    df['prev_low_vol'] = df['vol_ratio'].where(df['price_at_low']).ffill().shift(1)

    signals = []
    for i in range(price_window + vol_window + 5, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]

        # 顶背离：价格新高，量未新高
        if row['price_at_high'] and row['close'] > prev_row['close'] * 1.02:
            if row['vol_ratio'] < row['prev_high_vol'] * 0.9:
                sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.04, 0.04)
                signals.append(sig)

        # 底背离：价格新低，量未新低（缩量止跌）
        if row['price_at_low'] and row['close'] < prev_row['close'] * 0.98:
            if row['vol_ratio'] < row['prev_low_vol'] * 1.1:
                sig = make_signal(symbol, str(row['date']), 1, 0.7, 0.05, 0.04)
                signals.append(sig)

    return signals


def tmpl_volume_confirmed_breakout(symbol, df, params):
    """放量确认突破：突破关键位+放量 = 有效突破."""
    lookback = int(params.get('lookback', 60))
    vol_mult = float(params.get('vol_mult', 1.8))

    df = df.copy()
    df['resistance'] = df['high'].rolling(lookback).max().shift(1)
    df['support'] = df['low'].rolling(lookback).min().shift(1)
    df['vol_ma'] = df['volume'].rolling(20).mean()

    signals = []
    for _, row in df.iterrows():
        if pd.isna(row['resistance']) or pd.isna(row['vol_ma']):
            continue

        # 放量突破阻力位
        if row['close'] > row['resistance'] * 1.01 and row['volume'] > row['vol_ma'] * vol_mult:
            sig = make_signal(symbol, str(row['date']), 1, 0.75, 0.06, 0.04)
            signals.append(sig)

        # 放量跌破支撑位
        elif row['close'] < row['support'] * 0.99 and row['volume'] > row['vol_ma'] * vol_mult:
            sig = make_signal(symbol, str(row['date']), -1, 0.75, -0.04, 0.04)
            signals.append(sig)

    return signals


# ── 2. 波动率家族 ──

def tmpl_atr_channel_breakout(symbol, df, params):
    """ATR通道突破：基于真实波动幅度的自适应通道."""
    atr_window = int(params.get('atr_window', 14))
    ma_window = int(params.get('ma_window', 20))
    atr_mult = float(params.get('atr_mult', 2.5))

    df = df.copy()
    df['tr'] = np.maximum(df['high'] - df['low'],
                          np.maximum(abs(df['high'] - df['close'].shift(1)),
                                    abs(df['low'] - df['close'].shift(1))))
    df['atr'] = df['tr'].rolling(atr_window).mean()
    df['mid'] = df['close'].rolling(ma_window).mean()
    df['upper'] = df['mid'] + atr_mult * df['atr']
    df['lower'] = df['mid'] - atr_mult * df['atr']

    signals = []
    in_position = False
    for _, row in df.iterrows():
        if pd.isna(row['upper']):
            continue

        if not in_position and row['close'] > row['upper']:
            sig = make_signal(symbol, str(row['date']), 1, 0.7, 0.06, 0.04)
            signals.append(sig)
            in_position = True
        elif in_position and row['close'] < row['mid']:
            sig = make_signal(symbol, str(row['date']), -1, 0.6, -0.03, 0.04)
            signals.append(sig)
            in_position = False

    return signals


def tmpl_volatility_regime(symbol, df, params):
    """波动率状态切换：低波动→高波动时入场，高波动→低波动时退出."""
    vol_window = int(params.get('vol_window', 20))
    regime_window = int(params.get('regime_window', 60))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['vol'] = df['returns'].rolling(vol_window).std() * np.sqrt(252)
    df['vol_ma'] = df['vol'].rolling(regime_window).mean()
    df['high_vol'] = df['vol'] > df['vol_ma'] * 1.2
    df['low_vol'] = df['vol'] < df['vol_ma'] * 0.8

    signals = []
    prev_high = False
    prev_low = False

    for _, row in df.iterrows():
        if pd.isna(row['vol_ma']):
            prev_high = row['high_vol']
            prev_low = row['low_vol']
            continue

        # 从低波动切换到高波动 = 突破在即，买入
        if not prev_high and row['high_vol']:
            sig = make_signal(symbol, str(row['date']), 1, 0.65, 0.05, 0.04)
            signals.append(sig)

        # 从高波动切换到低波动 = 趋势结束，卖出
        if prev_high and not row['high_vol'] and row['low_vol']:
            sig = make_signal(symbol, str(row['date']), -1, 0.6, -0.03, 0.04)
            signals.append(sig)

        prev_high = row['high_vol']
        prev_low = row['low_vol']

    return signals


# ── 3. 多时间框架家族 ──

def tmpl_multi_timeframe_momentum(symbol, df, params):
    """多时间框架动量共振：短中长期动量同向时入场."""
    short_window = int(params.get('short_window', 10))
    mid_window = int(params.get('mid_window', 30))
    long_window = int(params.get('long_window', 60))

    df = df.copy()
    df['short_ma'] = df['close'].rolling(short_window).mean()
    df['mid_ma'] = df['close'].rolling(mid_window).mean()
    df['long_ma'] = df['close'].rolling(long_window).mean()

    df['short_trend'] = df['close'] > df['short_ma']
    df['mid_trend'] = df['close'] > df['mid_ma']
    df['long_trend'] = df['close'] > df['long_ma']

    signals = []
    prev_all_up = False
    prev_all_down = False

    for _, row in df.iterrows():
        if pd.isna(row['long_ma']):
            continue

        all_up = row['short_trend'] and row['mid_trend'] and row['long_trend']
        all_down = not row['short_trend'] and not row['mid_trend'] and not row['long_trend']

        # 三周期共振向上
        if not prev_all_up and all_up:
            sig = make_signal(symbol, str(row['date']), 1, 0.75, 0.06, 0.03)
            signals.append(sig)

        # 三周期共振向下
        if not prev_all_down and all_down:
            sig = make_signal(symbol, str(row['date']), -1, 0.75, -0.04, 0.03)
            signals.append(sig)

        prev_all_up = all_up
        prev_all_down = all_down

    return signals


# ── 4. 统计套利/均值回归家族 ──

def tmpl_zscore_mean_reversion(symbol, df, params):
    """Z-Score均值回归：价格偏离均值过多时回归."""
    window = int(params.get('window', 60))
    entry_z = float(params.get('entry_z', 2.0))
    exit_z = float(params.get('exit_z', 0.5))

    df = df.copy()
    df['ma'] = df['close'].rolling(window).mean()
    df['std'] = df['close'].rolling(window).std()
    df['zscore'] = (df['close'] - df['ma']) / df['std']

    signals = []
    for _, row in df.iterrows():
        if pd.isna(row['zscore']):
            continue

        # Z-Score过高 = 超买，做空（或卖出）
        if row['zscore'] > entry_z:
            sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.04, 0.03)
            signals.append(sig)

        # Z-Score过低 = 超卖，做多
        elif row['zscore'] < -entry_z:
            sig = make_signal(symbol, str(row['date']), 1, 0.7, 0.05, 0.03)
            signals.append(sig)

        # 回归均值 = 平仓
        elif abs(row['zscore']) < exit_z:
            sig = make_signal(symbol, str(row['date']), -1 if row['zscore'] > 0 else 1, 0.5, 0.02, 0.02)
            signals.append(sig)

    return signals


def tmpl_range_bound_reversion(symbol, df, params):
    """区间震荡均值回归：在支撑位买，阻力位卖."""
    lookback = int(params.get('lookback', 40))
    band_pct = float(params.get('band_pct', 0.05))

    df = df.copy()
    df['high_band'] = df['high'].rolling(lookback).max().shift(1)
    df['low_band'] = df['low'].rolling(lookback).min().shift(1)
    df['mid'] = (df['high_band'] + df['low_band']) / 2
    df['upper_entry'] = df['high_band'] * (1 - band_pct)
    df['lower_entry'] = df['low_band'] * (1 + band_pct)

    signals = []
    for _, row in df.iterrows():
        if pd.isna(row['high_band']):
            continue

        # 接近支撑位 = 买入
        if row['close'] <= row['lower_entry']:
            sig = make_signal(symbol, str(row['date']), 1, 0.65, 0.04, 0.03)
            signals.append(sig)

        # 接近阻力位 = 卖出
        elif row['close'] >= row['upper_entry']:
            sig = make_signal(symbol, str(row['date']), -1, 0.65, -0.03, 0.03)
            signals.append(sig)

    return signals


# ── 5. 行为金融家族 ──

def tmpl_fear_greed_extreme(symbol, df, params):
    """恐惧贪婪极端值：连续大跌后买入（恐惧），连续大涨后卖出（贪婪）."""
    streak_window = int(params.get('streak_window', 5))
    threshold = float(params.get('threshold', 0.15))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['streak_up'] = (df['returns'] > 0).rolling(streak_window).sum()
    df['streak_down'] = (df['returns'] < 0).rolling(streak_window).sum()
    df['cum_return'] = df['returns'].rolling(streak_window).sum()

    signals = []
    for _, row in df.iterrows():
        if pd.isna(row['cum_return']):
            continue

        # 连续下跌且累计跌幅大 = 恐惧极端，买入
        if row['streak_down'] >= streak_window - 1 and row['cum_return'] < -threshold:
            sig = make_signal(symbol, str(row['date']), 1, 0.7, 0.06, 0.04)
            signals.append(sig)

        # 连续上涨且累计涨幅大 = 贪婪极端，卖出
        elif row['streak_up'] >= streak_window - 1 and row['cum_return'] > threshold:
            sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.04, 0.04)
            signals.append(sig)

    return signals


def tmpl_opening_gap_reversal(symbol, df, params):
    """开盘缺口反转：大幅高开低走/低开高走后的反转."""
    gap_threshold = float(params.get('gap_threshold', 0.02))

    df = df.copy()
    df['prev_close'] = df['close'].shift(1)
    df['gap'] = (df['open'] - df['prev_close']) / df['prev_close']
    df['intraday_return'] = (df['close'] - df['open']) / df['open']

    signals = []
    for _, row in df.iterrows():
        if pd.isna(row['gap']):
            continue

        # 大幅高开 + 日内低走 = 假突破，卖出
        if row['gap'] > gap_threshold and row['intraday_return'] < -gap_threshold / 2:
            sig = make_signal(symbol, str(row['date']), -1, 0.65, -0.03, 0.03)
            signals.append(sig)

        # 大幅低开 + 日内高走 = 假跌破，买入
        elif row['gap'] < -gap_threshold and row['intraday_return'] > gap_threshold / 2:
            sig = make_signal(symbol, str(row['date']), 1, 0.65, 0.04, 0.03)
            signals.append(sig)

    return signals


# ── 6. 资金流向家族 ──

def tmpl_obv_trend(symbol, df, params):
    """OBV能量潮趋势：资金流向确认价格趋势."""
    obv_window = int(params.get('obv_window', 20))
    confirm_window = int(params.get('confirm_window', 5))

    df = df.copy()
    df['obv_change'] = np.where(df['close'] > df['close'].shift(1), df['volume'],
                                np.where(df['close'] < df['close'].shift(1), -df['volume'], 0))
    df['obv'] = df['obv_change'].cumsum()
    df['obv_ma'] = df['obv'].rolling(obv_window).mean()
    df['price_ma'] = df['close'].rolling(obv_window).mean()

    df['obv_trend'] = df['obv'] > df['obv_ma']
    df['price_trend'] = df['close'] > df['price_ma']

    signals = []
    prev_confirm = None

    for _, row in df.iterrows():
        if pd.isna(row['obv_ma']):
            continue

        # OBV和价格同向 = 趋势确认
        confirm = row['obv_trend'] == row['price_trend']

        if prev_confirm is not None and not prev_confirm and confirm:
            if row['obv_trend']:  # 同步向上
                sig = make_signal(symbol, str(row['date']), 1, 0.7, 0.05, 0.03)
                signals.append(sig)
            else:  # 同步向下
                sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.03, 0.03)
                signals.append(sig)

        prev_confirm = confirm

    return signals


def tmpl_money_flow_index(symbol, df, params):
    """资金流量指标MFI：结合价格和成交量的RSI变体."""
    period = int(params.get('period', 14))
    oversold = float(params.get('oversold', 20))
    overbought = float(params.get('overbought', 80))

    df = df.copy()
    df['typical'] = (df['high'] + df['low'] + df['close']) / 3
    df['raw_money'] = df['typical'] * df['volume']
    df['money_flow'] = np.where(df['typical'] > df['typical'].shift(1), df['raw_money'], -df['raw_money'])
    df['positive'] = df['money_flow'].clip(lower=0).rolling(period).sum()
    df['negative'] = (-df['money_flow'].clip(upper=0)).rolling(period).sum()
    df['mfi'] = 100 - (100 / (1 + df['positive'] / df['negative']))

    signals = []
    prev_mfi = None

    for _, row in df.iterrows():
        if prev_mfi is not None and not np.isnan(row['mfi']):
            if prev_mfi < oversold and row['mfi'] >= oversold:
                sig = make_signal(symbol, str(row['date']), 1, 0.65, 0.04, 0.04)
                signals.append(sig)
            elif prev_mfi > overbought and row['mfi'] <= overbought:
                sig = make_signal(symbol, str(row['date']), -1, 0.65, -0.03, 0.04)
                signals.append(sig)
        prev_mfi = row['mfi']

    return signals


# ── 7. 形态识别家族 ──

def tmpl_double_bottom(symbol, df, params):
    """双底形态识别：两个相近低点+中间反弹."""
    window = int(params.get('window', 30))
    tolerance = float(params.get('tolerance', 0.03))

    df = df.copy()
    df['low_min'] = df['low'].rolling(window).min()
    df['is_low'] = abs(df['low'] - df['low_min']) / df['low_min'] < tolerance
    df['local_low'] = df['low'] == df['low'].rolling(5, center=True).min()

    signals = []
    lows = []

    for i, row in df.iterrows():
        if pd.isna(row['low_min']):
            continue

        if row['local_low']:
            lows.append((i, row['low'], row['close']))

            # 检查双底
            if len(lows) >= 2:
                l1, l2 = lows[-2], lows[-1]
                # 两个低点价格接近
                price_similar = abs(l1[1] - l2[1]) / l1[1] < tolerance * 2
                # 中间有反弹
                middle_high = df['high'].iloc[l1[0]:l2[0]].max()
                has_bounce = middle_high > l1[2] * 1.03
                # 第二个低点后突破颈线
                neckline = middle_high
                breakout = l2[0] < i and row['close'] > neckline

                if price_similar and has_bounce and breakout:
                    sig = make_signal(symbol, str(row['date']), 1, 0.75, 0.07, 0.04)
                    signals.append(sig)
                    lows = []  # 重置

    return signals


def tmpl_engulfing_pattern(symbol, df, params):
    """吞没形态：阳线吞没阴线=买入，阴线吞没阳线=卖出."""
    min_body = float(params.get('min_body', 0.01))

    df = df.copy()
    df['body'] = abs(df['close'] - df['open']) / df['open']
    df['bullish'] = df['close'] > df['open']
    df['prev_bullish'] = df['bullish'].shift(1)
    df['prev_body'] = df['body'].shift(1)

    signals = []
    for i in range(1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]

        if pd.isna(row['body']) or row['body'] < min_body:
            continue

        # 阳线吞没阴线（ prev是阴线，当前是阳线且实体更大）
        if not prev['bullish'] and row['bullish']:
            if row['open'] < prev['close'] and row['close'] > prev['open']:
                sig = make_signal(symbol, str(row['date']), 1, 0.7, 0.05, 0.03)
                signals.append(sig)

        # 阴线吞没阳线
        elif prev['bullish'] and not row['bullish']:
            if row['open'] > prev['close'] and row['close'] < prev['open']:
                sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.04, 0.03)
                signals.append(sig)

    return signals


# ── 8. 复合/多因子家族 ──

def tmpl_multi_factor_composite(symbol, df, params):
    """多因子复合：趋势+动量+波动率综合评分."""
    trend_weight = float(params.get('trend_weight', 0.4))
    momentum_weight = float(params.get('momentum_weight', 0.3))
    vol_weight = float(params.get('vol_weight', 0.3))
    threshold = float(params.get('threshold', 0.5))

    df = df.copy()
    # 趋势因子
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    df['trend_score'] = np.where(df['close'] > df['ma20'], 0.5, 0) + np.where(df['ma20'] > df['ma60'], 0.5, 0)

    # 动量因子
    df['ret_20'] = df['close'].pct_change(20)
    df['ret_60'] = df['close'].pct_change(60)
    df['momentum_score'] = np.where(df['ret_20'] > 0, 0.5, 0) + np.where(df['ret_60'] > 0, 0.5, 0)

    # 波动率因子（低波动更好）
    df['vol'] = df['close'].pct_change().rolling(20).std()
    df['vol_rank'] = df['vol'].rolling(60).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1] if len(x) > 0 else 0.5)
    df['vol_score'] = 1 - df['vol_rank']  # 低波动=高分

    # 综合评分
    df['composite'] = (trend_weight * df['trend_score'] +
                       momentum_weight * df['momentum_score'] +
                       vol_weight * df['vol_score'])

    signals = []
    prev_score = None

    for _, row in df.iterrows():
        if pd.isna(row['composite']):
            prev_score = None
            continue

        if prev_score is not None:
            # 评分突破阈值
            if prev_score < threshold and row['composite'] >= threshold:
                sig = make_signal(symbol, str(row['date']), 1, row['composite'], 0.05, 0.03)
                signals.append(sig)
            # 评分跌破阈值
            elif prev_score >= threshold and row['composite'] < threshold:
                sig = make_signal(symbol, str(row['date']), -1, 1 - row['composite'], -0.03, 0.03)
                signals.append(sig)

        prev_score = row['composite']

    return signals


def tmpl_adaptive_momentum(symbol, df, params):
    """自适应动量：根据市场环境调整动量周期."""
    short_window = int(params.get('short_window', 10))
    long_window = int(params.get('long_window', 60))

    df = df.copy()
    df['vol'] = df['close'].pct_change().rolling(20).std()
    df['vol_regime'] = df['vol'] > df['vol'].rolling(60).mean()

    # 高波动用短周期，低波动用长周期
    df['adaptive_window'] = np.where(df['vol_regime'], short_window, long_window)
    df['momentum'] = df['close'].pct_change(short_window)
    df['momentum_long'] = df['close'].pct_change(long_window)
    df['adaptive_mom'] = np.where(df['vol_regime'], df['momentum'], df['momentum_long'])

    df['adaptive_ma'] = df['close'].rolling(short_window).mean()

    signals = []
    prev_mom = None

    for _, row in df.iterrows():
        if pd.isna(row['adaptive_mom']):
            prev_mom = None
            continue

        if prev_mom is not None:
            # 动量由负转正
            if prev_mom < 0 and row['adaptive_mom'] >= 0 and row['close'] > row['adaptive_ma']:
                sig = make_signal(symbol, str(row['date']), 1, 0.7, 0.06, 0.04)
                signals.append(sig)
            # 动量由正转负
            elif prev_mom > 0 and row['adaptive_mom'] <= 0:
                sig = make_signal(symbol, str(row['date']), -1, 0.7, -0.03, 0.04)
                signals.append(sig)

        prev_mom = row['adaptive_mom']

    return signals


# ═══════════════════════════════════════════════════════════════
# 策略池定义
# ═══════════════════════════════════════════════════════════════

STRATEGY_POOL = [
    # 量价关系
    {"id": "vol_price_divergence", "name": "量价背离", "family": "量价关系", "func": tmpl_volume_price_divergence, "params": {"vol_window": 20, "price_window": 20}},
    {"id": "vol_confirmed_breakout", "name": "放量突破确认", "family": "量价关系", "func": tmpl_volume_confirmed_breakout, "params": {"lookback": 60, "vol_mult": 1.8}},
    {"id": "vol_confirmed_breakout_v2", "name": "放量突破确认V2", "family": "量价关系", "func": tmpl_volume_confirmed_breakout, "params": {"lookback": 40, "vol_mult": 2.0}},

    # 波动率
    {"id": "atr_channel", "name": "ATR通道突破", "family": "波动率", "func": tmpl_atr_channel_breakout, "params": {"atr_window": 14, "ma_window": 20, "atr_mult": 2.5}},
    {"id": "atr_channel_v2", "name": "ATR通道突破V2", "family": "波动率", "func": tmpl_atr_channel_breakout, "params": {"atr_window": 10, "ma_window": 30, "atr_mult": 2.0}},
    {"id": "vol_regime", "name": "波动率状态切换", "family": "波动率", "func": tmpl_volatility_regime, "params": {"vol_window": 20, "regime_window": 60}},
    {"id": "vol_regime_v2", "name": "波动率状态切换V2", "family": "波动率", "func": tmpl_volatility_regime, "params": {"vol_window": 10, "regime_window": 40}},

    # 多时间框架
    {"id": "mtf_momentum", "name": "多时间框架动量", "family": "多时间框架", "func": tmpl_multi_timeframe_momentum, "params": {"short_window": 10, "mid_window": 30, "long_window": 60}},
    {"id": "mtf_momentum_v2", "name": "多时间框架动量V2", "family": "多时间框架", "func": tmpl_multi_timeframe_momentum, "params": {"short_window": 5, "mid_window": 20, "long_window": 50}},

    # 均值回归
    {"id": "zscore_reversion", "name": "Z-Score均值回归", "family": "均值回归", "func": tmpl_zscore_mean_reversion, "params": {"window": 60, "entry_z": 2.0, "exit_z": 0.5}},
    {"id": "zscore_reversion_v2", "name": "Z-Score均值回归V2", "family": "均值回归", "func": tmpl_zscore_mean_reversion, "params": {"window": 40, "entry_z": 1.5, "exit_z": 0.3}},
    {"id": "range_reversion", "name": "区间震荡回归", "family": "均值回归", "func": tmpl_range_bound_reversion, "params": {"lookback": 40, "band_pct": 0.05}},
    {"id": "range_reversion_v2", "name": "区间震荡回归V2", "family": "均值回归", "func": tmpl_range_bound_reversion, "params": {"lookback": 60, "band_pct": 0.03}},

    # 行为金融
    {"id": "fear_greed", "name": "恐惧贪婪极端", "family": "行为金融", "func": tmpl_fear_greed_extreme, "params": {"streak_window": 5, "threshold": 0.15}},
    {"id": "fear_greed_v2", "name": "恐惧贪婪极端V2", "family": "行为金融", "func": tmpl_fear_greed_extreme, "params": {"streak_window": 3, "threshold": 0.10}},
    {"id": "gap_reversal", "name": "开盘缺口反转", "family": "行为金融", "func": tmpl_opening_gap_reversal, "params": {"gap_threshold": 0.02}},
    {"id": "gap_reversal_v2", "name": "开盘缺口反转V2", "family": "行为金融", "func": tmpl_opening_gap_reversal, "params": {"gap_threshold": 0.03}},

    # 资金流向
    {"id": "obv_trend", "name": "OBV趋势确认", "family": "资金流向", "func": tmpl_obv_trend, "params": {"obv_window": 20, "confirm_window": 5}},
    {"id": "obv_trend_v2", "name": "OBV趋势确认V2", "family": "资金流向", "func": tmpl_obv_trend, "params": {"obv_window": 30, "confirm_window": 3}},
    {"id": "mfi_reversal", "name": "MFI资金流量反转", "family": "资金流向", "func": tmpl_money_flow_index, "params": {"period": 14, "oversold": 20, "overbought": 80}},
    {"id": "mfi_reversal_v2", "name": "MFI资金流量反转V2", "family": "资金流向", "func": tmpl_money_flow_index, "params": {"period": 10, "oversold": 15, "overbought": 85}},

    # 形态识别
    {"id": "double_bottom", "name": "双底形态", "family": "形态识别", "func": tmpl_double_bottom, "params": {"window": 30, "tolerance": 0.03}},
    {"id": "engulfing", "name": "吞没形态", "family": "形态识别", "func": tmpl_engulfing_pattern, "params": {"min_body": 0.01}},
    {"id": "engulfing_v2", "name": "吞没形态V2", "family": "形态识别", "func": tmpl_engulfing_pattern, "params": {"min_body": 0.015}},

    # 复合因子
    {"id": "multi_factor", "name": "多因子复合", "family": "复合因子", "func": tmpl_multi_factor_composite, "params": {"trend_weight": 0.4, "momentum_weight": 0.3, "vol_weight": 0.3, "threshold": 0.5}},
    {"id": "multi_factor_v2", "name": "多因子复合V2", "family": "复合因子", "func": tmpl_multi_factor_composite, "params": {"trend_weight": 0.5, "momentum_weight": 0.3, "vol_weight": 0.2, "threshold": 0.6}},
    {"id": "adaptive_momentum", "name": "自适应动量", "family": "复合因子", "func": tmpl_adaptive_momentum, "params": {"short_window": 10, "long_window": 60}},
    {"id": "adaptive_momentum_v2", "name": "自适应动量V2", "family": "复合因子", "func": tmpl_adaptive_momentum, "params": {"short_window": 5, "long_window": 40}},
]


def discover_strategies(target_count: int = 35, verbose: bool = True) -> list[dict]:
    """策略发现主函数：批量测试策略池，返回通过验证的策略.

    Args:
        target_count: 目标通过数量
        verbose: 是否打印详情

    Returns:
        通过验证的策略配置列表
    """
    if verbose:
        print(f"[Discovery] 开始策略发现，目标: {target_count}个高质量策略")
        print(f"[Discovery] 策略池大小: {len(STRATEGY_POOL)}")
        print("=" * 80)

    # 预加载数据
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
                'reasons': result['fail_reasons'][:5]  # 只存前5个失败原因
            })
            if verbose:
                print(f"  ❌ 失败 ({len(result['fail_reasons'])}项未通过)")

        # 提前终止条件
        if len(passed) >= target_count:
            if verbose:
                print(f"\n[Discovery] 已达到目标数量 {target_count}，提前终止")
            break

    if verbose:
        print("\n" + "=" * 80)
        print(f"[Discovery] 完成: {len(passed)}个通过, {len(failed)}个失败")
        if len(passed) < target_count:
            print(f"[Discovery] 警告: 未达到目标数量，还需 {target_count - len(passed)} 个策略")

    return passed


if __name__ == "__main__":
    # 直接运行测试
    passed = discover_strategies(target_count=35, verbose=True)
    print(f"\n最终通过策略数: {len(passed)}")
    for p in passed:
        print(f"  - {p['name']} ({p['family']})")

"""策略发现引擎V5 — 针对验证标准优化.

核心优化:
1. 提高胜率: 增加过滤条件, 减少假信号
2. 控制回撤:  tighter止损
3. 提高收益: 让利润奔跑
"""

import numpy as np
import pandas as pd
from typing import Any

from app.services.backtest_validator import validate_template, preload_all_data
from app.services.template_runner import make_signal


def tmpl_macd_with_filter(symbol, df, params):
    """MACD+趋势过滤: 只在趋势方向交易.

    提高胜率的关键: 避免逆势交易.
    """
    fast = int(params.get('fast', 12))
    slow = int(params.get('slow', 26))
    signal = int(params.get('signal', 9))
    trend_ma = int(params.get('trend_ma', 60))

    df = df.copy()
    ema_fast = df['close'].ewm(span=fast).mean()
    ema_slow = df['close'].ewm(span=slow).mean()
    df['macd'] = ema_fast - ema_slow
    df['signal_line'] = df['macd'].ewm(span=signal).mean()
    df['hist'] = df['macd'] - df['signal_line']
    df['ma'] = df['close'].rolling(trend_ma).mean()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev_hist = df['hist'].iloc[i-1]
        curr_hist = df['hist'].iloc[i]
        curr_close = df['close'].iloc[i]
        curr_ma = df['ma'].iloc[i]

        if pd.isna(prev_hist) or pd.isna(curr_ma):
            continue

        # 多头: MACD金叉 + 价格在均线上方
        if not in_position and prev_hist < 0 and curr_hist > 0 and curr_close > curr_ma:
            sig = make_signal(symbol, str(df['date'].iloc[i]), 1, 0.85, 0.08, 0.03)
            signals.append(sig)
            in_position = True
        # 空头: MACD死叉
        elif in_position and prev_hist > 0 and curr_hist < 0:
            sig = make_signal(symbol, str(df['date'].iloc[i]), -1, 0.75, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


def tmpl_ema_cross_with_vol(symbol, df, params):
    """EMA交叉+成交量确认.

    放量确认的趋势交叉, 胜率更高.
    """
    fast = int(params.get('fast', 12))
    slow = int(params.get('slow', 26))
    vol_window = int(params.get('vol_window', 20))

    df = df.copy()
    df['fast_ema'] = df['close'].ewm(span=fast).mean()
    df['slow_ema'] = df['close'].ewm(span=slow).mean()
    df['vol_ma'] = df['volume'].rolling(vol_window).mean()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev_fast = df['fast_ema'].iloc[i-1]
        prev_slow = df['slow_ema'].iloc[i-1]
        curr_fast = df['fast_ema'].iloc[i]
        curr_slow = df['slow_ema'].iloc[i]
        curr_vol = df['volume'].iloc[i]
        curr_vol_ma = df['vol_ma'].iloc[i]

        if pd.isna(prev_slow) or pd.isna(curr_vol_ma):
            continue

        # 金叉 + 放量
        if not in_position and prev_fast <= prev_slow and curr_fast > curr_slow and curr_vol > curr_vol_ma:
            sig = make_signal(symbol, str(df['date'].iloc[i]), 1, 0.85, 0.08, 0.03)
            signals.append(sig)
            in_position = True
        # 死叉
        elif in_position and prev_fast >= prev_slow and curr_fast < curr_slow:
            sig = make_signal(symbol, str(df['date'].iloc[i]), -1, 0.75, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


def tmpl_rsi_divergence(symbol, df, params):
    """RSI背离: 价格创新低但RSI未创新低 = 底背离买入.

    高胜率反转策略.
    """
    rsi_period = int(params.get('rsi_period', 14))
    lookback = int(params.get('lookback', 20))

    df = df.copy()
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(rsi_period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    signals = []
    in_position = False

    for i in range(lookback + rsi_period, len(df)):
        curr_close = df['close'].iloc[i]
        curr_rsi = df['rsi'].iloc[i]
        prev_low = df['low'].iloc[i-lookback:i].min()
        prev_rsi_low = df['rsi'].iloc[i-lookback:i].min()

        if pd.isna(curr_rsi):
            continue

        # 底背离: 价格新低, RSI未新低
        if not in_position and curr_close < prev_low * 1.02 and curr_rsi > prev_rsi_low * 1.05:
            sig = make_signal(symbol, str(df['date'].iloc[i]), 1, 0.8, 0.07, 0.03)
            signals.append(sig)
            in_position = True
        # RSI超买或回归
        elif in_position and curr_rsi > 60:
            sig = make_signal(symbol, str(df['date'].iloc[i]), -1, 0.7, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


def tmpl_price_momentum_volatility(symbol, df, params):
    """价格动量+波动率过滤.

    只在低波动环境下的动量交易.
    """
    mom_window = int(params.get('mom_window', 20))
    vol_window = int(params.get('vol_window', 20))
    vol_lookback = int(params.get('vol_lookback', 60))

    df = df.copy()
    df['momentum'] = df['close'].pct_change(mom_window)
    df['returns'] = df['close'].pct_change()
    df['vol'] = df['returns'].rolling(vol_window).std()
    df['vol_ma'] = df['vol'].rolling(vol_lookback).mean()
    df['low_vol'] = df['vol'] < df['vol_ma']

    signals = []
    in_position = False

    for i in range(1, len(df)):
        curr_mom = df['momentum'].iloc[i]
        prev_mom = df['momentum'].iloc[i-1]
        curr_low_vol = df['low_vol'].iloc[i]

        if pd.isna(curr_mom):
            continue

        # 动量转正 + 低波动
        if not in_position and prev_mom < 0 and curr_mom > 0 and curr_low_vol:
            sig = make_signal(symbol, str(df['date'].iloc[i]), 1, 0.8, 0.07, 0.03)
            signals.append(sig)
            in_position = True
        # 动量转负
        elif in_position and prev_mom > 0 and curr_mom < 0:
            sig = make_signal(symbol, str(df['date'].iloc[i]), -1, 0.75, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


def tmpl_bollinger_squeeze(symbol, df, params):
    """布林带挤压突破: 波动率收缩后的突破.

    高胜率趋势启动策略.
    """
    bb_period = int(params.get('bb_period', 20))
    squeeze_threshold = float(params.get('squeeze_threshold', 0.05))

    df = df.copy()
    df['ma'] = df['close'].rolling(bb_period).mean()
    df['std'] = df['close'].rolling(bb_period).std()
    df['upper'] = df['ma'] + 2 * df['std']
    df['lower'] = df['ma'] - 2 * df['std']
    df['bandwidth'] = (df['upper'] - df['lower']) / df['ma']
    df['bandwidth_ma'] = df['bandwidth'].rolling(bb_period).mean()
    df['squeeze'] = df['bandwidth'] < df['bandwidth_ma'] * squeeze_threshold

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev_squeeze = df['squeeze'].iloc[i-1]
        curr_squeeze = df['squeeze'].iloc[i]
        curr_close = df['close'].iloc[i]
        curr_upper = df['upper'].iloc[i]
        curr_lower = df['lower'].iloc[i]

        if pd.isna(curr_upper):
            continue

        # 挤压结束 + 向上突破
        if not in_position and prev_squeeze and not curr_squeeze and curr_close > curr_upper:
            sig = make_signal(symbol, str(df['date'].iloc[i]), 1, 0.85, 0.08, 0.03)
            signals.append(sig)
            in_position = True
        # 跌破中轨
        elif in_position and curr_close < df['ma'].iloc[i]:
            sig = make_signal(symbol, str(df['date'].iloc[i]), -1, 0.7, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


def tmpl_kdj_stochastic(symbol, df, params):
    """KDJ随机指标: 超卖区金叉买入.

    经典高胜率策略.
    """
    n = int(params.get('n', 9))
    m1 = int(params.get('m1', 3))
    m2 = int(params.get('m2', 3))
    oversold = int(params.get('oversold', 20))
    overbought = int(params.get('overbought', 80))

    df = df.copy()
    low_list = df['low'].rolling(window=n, min_periods=n).min()
    high_list = df['high'].rolling(window=n, min_periods=n).max()
    rsv = (df['close'] - low_list) / (high_list - low_list) * 100
    df['k'] = rsv.ewm(com=m1-1, adjust=False).mean()
    df['d'] = df['k'].ewm(com=m2-1, adjust=False).mean()
    df['j'] = 3 * df['k'] - 2 * df['d']

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev_k = df['k'].iloc[i-1]
        curr_k = df['k'].iloc[i]
        prev_d = df['d'].iloc[i-1]
        curr_d = df['d'].iloc[i]

        if pd.isna(curr_k):
            continue

        # K上穿D + 超卖区
        if not in_position and prev_k < prev_d and curr_k > curr_d and curr_k < oversold + 10:
            sig = make_signal(symbol, str(df['date'].iloc[i]), 1, 0.8, 0.07, 0.03)
            signals.append(sig)
            in_position = True
        # K下穿D + 超买区
        elif in_position and prev_k > prev_d and curr_k < curr_d and curr_k > overbought - 10:
            sig = make_signal(symbol, str(df['date'].iloc[i]), -1, 0.75, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


def tmpl_adaptive_momentum_v2(symbol, df, params):
    """自适应动量V2: 根据波动率调整动量周期.

    高波动用短周期, 低波动用长周期.
    """
    short_mom = int(params.get('short_mom', 10))
    long_mom = int(params.get('long_mom', 30))
    vol_window = int(params.get('vol_window', 20))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['vol'] = df['returns'].rolling(vol_window).std()
    df['vol_ma'] = df['vol'].rolling(60).mean()
    df['high_vol'] = df['vol'] > df['vol_ma']

    df['short_mom'] = df['close'].pct_change(short_mom)
    df['long_mom'] = df['close'].pct_change(long_mom)
    df['adaptive_mom'] = np.where(df['high_vol'], df['short_mom'], df['long_mom'])

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev_mom = df['adaptive_mom'].iloc[i-1]
        curr_mom = df['adaptive_mom'].iloc[i]

        if pd.isna(curr_mom):
            continue

        if not in_position and prev_mom < 0 and curr_mom > 0.02:
            sig = make_signal(symbol, str(df['date'].iloc[i]), 1, 0.8, 0.07, 0.03)
            signals.append(sig)
            in_position = True
        elif in_position and prev_mom > 0 and curr_mom < -0.02:
            sig = make_signal(symbol, str(df['date'].iloc[i]), -1, 0.75, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 策略池定义
# ═══════════════════════════════════════════════════════════════

STRATEGY_POOL = [
    # MACD+过滤
    {"id": "macd_filter_12_26_60", "name": "MACD+趋势过滤(12,26,60)", "family": "趋势", "func": tmpl_macd_with_filter, "params": {"fast": 12, "slow": 26, "signal": 9, "trend_ma": 60}},
    {"id": "macd_filter_8_21_50", "name": "MACD+趋势过滤(8,21,50)", "family": "趋势", "func": tmpl_macd_with_filter, "params": {"fast": 8, "slow": 21, "signal": 5, "trend_ma": 50}},
    {"id": "macd_filter_5_15_30", "name": "MACD+趋势过滤(5,15,30)", "family": "趋势", "func": tmpl_macd_with_filter, "params": {"fast": 5, "slow": 15, "signal": 3, "trend_ma": 30}},

    # EMA交叉+成交量
    {"id": "ema_vol_12_26", "name": "EMA交叉+成交量(12,26)", "family": "趋势", "func": tmpl_ema_cross_with_vol, "params": {"fast": 12, "slow": 26, "vol_window": 20}},
    {"id": "ema_vol_8_21", "name": "EMA交叉+成交量(8,21)", "family": "趋势", "func": tmpl_ema_cross_with_vol, "params": {"fast": 8, "slow": 21, "vol_window": 15}},
    {"id": "ema_vol_5_20", "name": "EMA交叉+成交量(5,20)", "family": "趋势", "func": tmpl_ema_cross_with_vol, "params": {"fast": 5, "slow": 20, "vol_window": 10}},

    # RSI背离
    {"id": "rsi_div_14_20", "name": "RSI背离(14,20)", "family": "反转", "func": tmpl_rsi_divergence, "params": {"rsi_period": 14, "lookback": 20}},
    {"id": "rsi_div_10_15", "name": "RSI背离(10,15)", "family": "反转", "func": tmpl_rsi_divergence, "params": {"rsi_period": 10, "lookback": 15}},
    {"id": "rsi_div_20_30", "name": "RSI背离(20,30)", "family": "反转", "func": tmpl_rsi_divergence, "params": {"rsi_period": 20, "lookback": 30}},

    # 动量+波动率
    {"id": "mom_vol_20_20", "name": "动量+波动率(20,20)", "family": "动量", "func": tmpl_price_momentum_volatility, "params": {"mom_window": 20, "vol_window": 20, "vol_lookback": 60}},
    {"id": "mom_vol_10_10", "name": "动量+波动率(10,10)", "family": "动量", "func": tmpl_price_momentum_volatility, "params": {"mom_window": 10, "vol_window": 10, "vol_lookback": 30}},
    {"id": "mom_vol_30_30", "name": "动量+波动率(30,30)", "family": "动量", "func": tmpl_price_momentum_volatility, "params": {"mom_window": 30, "vol_window": 30, "vol_lookback": 90}},

    # 布林带挤压
    {"id": "boll_squeeze_20", "name": "布林带挤压(20)", "family": "突破", "func": tmpl_bollinger_squeeze, "params": {"bb_period": 20, "squeeze_threshold": 0.05}},
    {"id": "boll_squeeze_15", "name": "布林带挤压(15)", "family": "突破", "func": tmpl_bollinger_squeeze, "params": {"bb_period": 15, "squeeze_threshold": 0.03}},
    {"id": "boll_squeeze_30", "name": "布林带挤压(30)", "family": "突破", "func": tmpl_bollinger_squeeze, "params": {"bb_period": 30, "squeeze_threshold": 0.07}},

    # KDJ
    {"id": "kdj_9_3_3", "name": "KDJ(9,3,3)", "family": "反转", "func": tmpl_kdj_stochastic, "params": {"n": 9, "m1": 3, "m2": 3, "oversold": 20, "overbought": 80}},
    {"id": "kdj_14_3_3", "name": "KDJ(14,3,3)", "family": "反转", "func": tmpl_kdj_stochastic, "params": {"n": 14, "m1": 3, "m2": 3, "oversold": 20, "overbought": 80}},
    {"id": "kdj_5_2_2", "name": "KDJ(5,2,2)", "family": "反转", "func": tmpl_kdj_stochastic, "params": {"n": 5, "m1": 2, "m2": 2, "oversold": 15, "overbought": 85}},

    # 自适应动量
    {"id": "adaptive_mom_10_30", "name": "自适应动量(10,30)", "family": "动量", "func": tmpl_adaptive_momentum_v2, "params": {"short_mom": 10, "long_mom": 30, "vol_window": 20}},
    {"id": "adaptive_mom_5_20", "name": "自适应动量(5,20)", "family": "动量", "func": tmpl_adaptive_momentum_v2, "params": {"short_mom": 5, "long_mom": 20, "vol_window": 15}},
    {"id": "adaptive_mom_20_60", "name": "自适应动量(20,60)", "family": "动量", "func": tmpl_adaptive_momentum_v2, "params": {"short_mom": 20, "long_mom": 60, "vol_window": 30}},
]


def discover_strategies_v5(target_count: int = 35, verbose: bool = True) -> list[dict]:
    """策略发现主函数V5."""
    if verbose:
        print(f"[DiscoveryV5] 开始策略发现，目标: {target_count}个高质量策略")
        print(f"[DiscoveryV5] 策略池大小: {len(STRATEGY_POOL)}")
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
                print(f"\n[DiscoveryV5] 已达到目标数量 {target_count}，提前终止")
            break

    if verbose:
        print("\n" + "=" * 80)
        print(f"[DiscoveryV5] 完成: {len(passed)}个通过, {len(failed)}个失败")
        if len(passed) < target_count:
            print(f"[DiscoveryV5] 警告: 未达到目标数量，还需 {target_count - len(passed)} 个策略")

    return passed


if __name__ == "__main__":
    passed = discover_strategies_v5(target_count=35, verbose=True)
    print(f"\n最终通过策略数: {len(passed)}")
    for p in passed:
        print(f"  - {p['name']} ({p['family']})")

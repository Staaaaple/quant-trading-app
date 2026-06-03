"""基于论文的策略实现.

每个策略都有理论支撑，来自论文知识库.
"""

import numpy as np
import pandas as pd
from typing import Any

from app.services.backtest_validator import validate_template, preload_all_data
from app.services.template_runner import make_signal


# ═══════════════════════════════════════════════════════════════
# 基于论文的策略
# ═══════════════════════════════════════════════════════════════

# ── Paper 001/002/005: 因子动量 ──

def tmpl_factor_momentum(symbol, df, params):
    """因子动量策略 (Ehsani & Linnainmaa 2022).

    核心思想: 过去表现好的因子继续表现好.
    简化实现: 用价格动量作为因子动量的代理.
    """
    lookback = int(params.get('lookback', 12))
    hold_days = int(params.get('hold_days', 5))

    df = df.copy()
    df['factor_return'] = df['close'].pct_change(lookback)

    signals = []
    in_position = False

    for i in range(lookback, len(df)):
        row = df.iloc[i]

        if pd.isna(row['factor_return']):
            continue

        # 因子动量 > 0 = 买入
        if not in_position and row['factor_return'] > 0:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        # 因子动量 < 0 = 卖出
        elif in_position and row['factor_return'] < 0:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


# ── Paper 003: 质量因子 ──

def tmpl_quality_factor(symbol, df, params):
    """质量因子策略 (Asness et al. 2019).

    核心思想: 高质量股票长期跑赢.
    简化实现: 用盈利稳定性作为质量代理.
    """
    window = int(params.get('window', 20))
    threshold = float(params.get('threshold', 0.02))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['vol'] = df['returns'].rolling(window).std()
    df['mean_ret'] = df['returns'].rolling(window).mean()
    # 高质量 = 高收益 + 低波动
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


# ── Paper 004: 五因子模型 ──

def tmpl_fama_french_5f(symbol, df, params):
    """Fama-French五因子策略 (Fama & French 2015).

    核心思想: 市场、规模、价值、盈利、投资五因子解释收益.
    简化实现: 用价格动量+市值效应.
    """
    mom_window = int(params.get('mom_window', 12))
    vol_window = int(params.get('vol_window', 20))

    df = df.copy()
    df['mom'] = df['close'].pct_change(mom_window)
    df['vol'] = df['close'].pct_change().rolling(vol_window).std()
    # 综合评分: 动量 + 低波动
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


# ── Paper 006: LLM策略发现 ──

def tmpl_llm_momentum(symbol, df, params):
    """LLM发现的动量策略 (Zhang et al. 2024).

    核心思想: 动量是最有效的信号之一.
    """
    short_window = int(params.get('short_window', 5))
    long_window = int(params.get('long_window', 20))

    df = df.copy()
    df['short_ma'] = df['close'].rolling(short_window).mean()
    df['long_ma'] = df['close'].rolling(long_window).mean()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['long_ma']):
            continue

        if not in_position and prev['short_ma'] <= prev['long_ma'] and curr['short_ma'] > curr['long_ma']:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.85, 0.1, 0.04))
            in_position = True
        elif in_position and prev['short_ma'] >= prev['long_ma'] and curr['short_ma'] < curr['long_ma']:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


# ── Paper 007: LSTM-Transformer ──

def tmpl_lstm_transformer_trend(symbol, df, params):
    """LSTM-Transformer趋势策略 (Kabir et al. 2025).

    核心思想: 结合LSTM记忆和Transformer注意力.
    简化实现: 多时间尺度趋势确认.
    """
    short = int(params.get('short', 5))
    mid = int(params.get('mid', 20))
    long = int(params.get('long', 60))

    df = df.copy()
    df['short_ma'] = df['close'].ewm(span=short).mean()
    df['mid_ma'] = df['close'].ewm(span=mid).mean()
    df['long_ma'] = df['close'].ewm(span=long).mean()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['long_ma']):
            continue

        # 三均线共振
        all_up = curr['short_ma'] > curr['mid_ma'] > curr['long_ma']
        prev_all_up = prev['short_ma'] > prev['mid_ma'] > prev['long_ma']

        if not in_position and all_up and not prev_all_up:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.9, 0.1, 0.03))
            in_position = True
        elif in_position and not all_up:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


# ── Paper 008/009: 强化学习 ──

def tmpl_rl_trend_following(symbol, df, params):
    """强化学习趋势跟踪 (Nature 2025).

    核心思想: 用奖励机制优化交易决策.
    简化实现: 趋势跟踪+动态止损.
    """
    ma_period = int(params.get('ma_period', 20))
    trail_pct = float(params.get('trail_pct', 0.05))

    df = df.copy()
    df['ma'] = df['close'].rolling(ma_period).mean()

    signals = []
    in_position = False
    highest = 0

    for _, row in df.iterrows():
        if pd.isna(row['ma']):
            continue

        if not in_position and row['close'] > row['ma']:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.85, 0.08, 0.04))
            in_position = True
            highest = row['close']
        elif in_position:
            highest = max(highest, row['close'])
            if row['close'] < highest * (1 - trail_pct):
                signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
                in_position = False
                highest = 0

    return signals


# ── Paper 010: Temporal Fusion Transformer ──

def tmpl_tft_multivariate(symbol, df, params):
    """TFT多变量策略 (Lim et al. 2023).

    核心思想: 多变量注意力机制.
    简化实现: 价格+成交量+波动率多变量确认.
    """
    vol_window = int(params.get('vol_window', 20))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['vol'] = df['returns'].rolling(vol_window).std()
    df['vol_ma'] = df['vol'].rolling(vol_window * 3).mean()
    df['price_ma'] = df['close'].rolling(vol_window).mean()

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['vol_ma']):
            continue

        # 低波动 + 价格突破 = 买入
        low_vol = row['vol'] < row['vol_ma']
        price_up = row['close'] > row['price_ma']

        if not in_position and low_vol and price_up:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.85, 0.08, 0.03))
            in_position = True
        elif in_position and (not low_vol or not price_up):
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


# ── Paper 011/012: 配对交易 ──

def tmpl_pairs_trading(symbol, df, params):
    """配对交易策略 (Sun 2025).

    核心思想: 基于距离的配对交易.
    简化实现: 价格偏离均值回归.
    """
    window = int(params.get('window', 60))
    threshold = float(params.get('threshold', 2.0))

    df = df.copy()
    df['ma'] = df['close'].rolling(window).mean()
    df['std'] = df['close'].rolling(window).std()
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


# ── Paper 013/014: 深度强化学习配对交易 ──

def tmpl_dqn_pairs(symbol, df, params):
    """DQN配对交易策略 (Liu et al. 2024).

    核心思想: 用DQN优化交易时机.
    简化实现: 价差动量+均值回归.
    """
    short_window = int(params.get('short_window', 10))
    long_window = int(params.get('long_window', 30))

    df = df.copy()
    df['short_ma'] = df['close'].rolling(short_window).mean()
    df['long_ma'] = df['close'].rolling(long_window).mean()
    df['spread'] = df['short_ma'] - df['long_ma']
    df['spread_ma'] = df['spread'].rolling(long_window).mean()
    df['spread_std'] = df['spread'].rolling(long_window).std()
    df['zscore'] = (df['spread'] - df['spread_ma']) / (df['spread_std'] + 1e-6)

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['zscore']):
            continue

        if not in_position and row['zscore'] < -2:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.85, 0.06, 0.03))
            in_position = True
        elif in_position and row['zscore'] > 2:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


# ── Paper 015/016: 波动率目标 ──

def tmpl_volatility_targeting(symbol, df, params):
    """波动率目标策略 (Alpha Architect 2023).

    核心思想: 根据波动率动态调整仓位.
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

        # 低波动 = 满仓
        if not in_position and row['vol'] < target_vol:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        # 高波动 = 空仓
        elif in_position and row['vol'] > target_vol * 1.5:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


# ── Paper 017: CVaR风险平价 ──

def tmpl_cvar_risk_parity(symbol, df, params):
    """CVaR风险平价策略 (2025).

    核心思想: 基于CVaR的风险平价配置.
    简化实现: 波动率倒数加权.
    """
    vol_window = int(params.get('vol_window', 20))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['vol'] = df['returns'].rolling(vol_window).std()
    df['inv_vol'] = 1 / (df['vol'] + 1e-6)

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['inv_vol']):
            continue

        # 低波动 = 高权重 = 买入
        if not in_position and row['inv_vol'] > np.percentile(df['inv_vol'].dropna(), 60):
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.06, 0.03))
            in_position = True
        elif in_position and row['inv_vol'] < np.percentile(df['inv_vol'].dropna(), 40):
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03))
            in_position = False

    return signals


# ── Paper 018/019: 行为金融 ──

def tmpl_sentiment_contrarian(symbol, df, params):
    """情绪逆向策略 (Zhu & Shen 2025).

    核心思想: 利用投资者情绪和套利限制构建逆向策略.
    简化实现: 极端收益后反向操作.
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

        # 连续大跌 = 恐惧 = 买入
        if not in_position and row['cum_ret'] < -threshold:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.85, 0.08, 0.04))
            in_position = True
        # 连续大涨 = 贪婪 = 卖出
        elif in_position and row['cum_ret'] > threshold:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


# ── Paper 020: 多因子组合 ──

def tmpl_multi_factor_combo(symbol, df, params):
    """多因子组合策略 (2023).

    核心思想: 多因子+风险平价组合构建.
    简化实现: 动量+质量+低波动复合评分.
    """
    mom_window = int(params.get('mom_window', 20))
    vol_window = int(params.get('vol_window', 20))

    df = df.copy()
    # 动量因子
    df['mom'] = df['close'].pct_change(mom_window)
    # 质量因子 (收益/波动)
    df['returns'] = df['close'].pct_change()
    df['vol'] = df['returns'].rolling(vol_window).std()
    df['quality'] = df['returns'].rolling(vol_window).mean() / (df['vol'] + 1e-6)
    # 低波动因子
    df['low_vol'] = 1 / (df['vol'] + 1e-6)

    # 复合评分
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


# ═══════════════════════════════════════════════════════════════
# 策略池定义
# ═══════════════════════════════════════════════════════════════

STRATEGY_POOL = [
    # 因子动量 (Paper 001/002/005)
    {"id": "factor_momentum_12", "name": "因子动量(12日)", "paper": "paper_001", "func": tmpl_factor_momentum, "params": {"lookback": 12, "hold_days": 5}},
    {"id": "factor_momentum_20", "name": "因子动量(20日)", "paper": "paper_001", "func": tmpl_factor_momentum, "params": {"lookback": 20, "hold_days": 5}},
    {"id": "factor_momentum_60", "name": "因子动量(60日)", "paper": "paper_005", "func": tmpl_factor_momentum, "params": {"lookback": 60, "hold_days": 10}},

    # 质量因子 (Paper 003)
    {"id": "quality_factor_20", "name": "质量因子(20日)", "paper": "paper_003", "func": tmpl_quality_factor, "params": {"window": 20, "threshold": 0.02}},
    {"id": "quality_factor_60", "name": "质量因子(60日)", "paper": "paper_003", "func": tmpl_quality_factor, "params": {"window": 60, "threshold": 0.01}},

    # 五因子模型 (Paper 004)
    {"id": "ff5f_mom_vol", "name": "五因子动量波动", "paper": "paper_004", "func": tmpl_fama_french_5f, "params": {"mom_window": 12, "vol_window": 20}},
    {"id": "ff5f_mom_vol_v2", "name": "五因子动量波动V2", "paper": "paper_004", "func": tmpl_fama_french_5f, "params": {"mom_window": 20, "vol_window": 30}},

    # LLM动量 (Paper 006)
    {"id": "llm_momentum_5_20", "name": "LLM动量(5,20)", "paper": "paper_006", "func": tmpl_llm_momentum, "params": {"short_window": 5, "long_window": 20}},
    {"id": "llm_momentum_10_30", "name": "LLM动量(10,30)", "paper": "paper_006", "func": tmpl_llm_momentum, "params": {"short_window": 10, "long_window": 30}},

    # LSTM-Transformer (Paper 007)
    {"id": "lstm_transformer_5_20_60", "name": "LSTM-Transformer趋势(5,20,60)", "paper": "paper_007", "func": tmpl_lstm_transformer_trend, "params": {"short": 5, "mid": 20, "long": 60}},
    {"id": "lstm_transformer_10_30_60", "name": "LSTM-Transformer趋势(10,30,60)", "paper": "paper_007", "func": tmpl_lstm_transformer_trend, "params": {"short": 10, "mid": 30, "long": 60}},

    # 强化学习 (Paper 008/009)
    {"id": "rl_trend_20_5", "name": "RL趋势跟踪(20,5%)", "paper": "paper_008", "func": tmpl_rl_trend_following, "params": {"ma_period": 20, "trail_pct": 0.05}},
    {"id": "rl_trend_30_8", "name": "RL趋势跟踪(30,8%)", "paper": "paper_008", "func": tmpl_rl_trend_following, "params": {"ma_period": 30, "trail_pct": 0.08}},

    # TFT多变量 (Paper 010)
    {"id": "tft_multi_20", "name": "TFT多变量(20)", "paper": "paper_010", "func": tmpl_tft_multivariate, "params": {"vol_window": 20}},
    {"id": "tft_multi_30", "name": "TFT多变量(30)", "paper": "paper_010", "func": tmpl_tft_multivariate, "params": {"vol_window": 30}},

    # 配对交易 (Paper 011/012)
    {"id": "pairs_zscore_60", "name": "配对交易ZScore(60)", "paper": "paper_012", "func": tmpl_pairs_trading, "params": {"window": 60, "threshold": 2.0}},
    {"id": "pairs_zscore_40", "name": "配对交易ZScore(40)", "paper": "paper_012", "func": tmpl_pairs_trading, "params": {"window": 40, "threshold": 1.5}},

    # DQN配对 (Paper 013/014)
    {"id": "dqn_pairs_10_30", "name": "DQN配对(10,30)", "paper": "paper_013", "func": tmpl_dqn_pairs, "params": {"short_window": 10, "long_window": 30}},
    {"id": "dqn_pairs_20_60", "name": "DQN配对(20,60)", "paper": "paper_013", "func": tmpl_dqn_pairs, "params": {"short_window": 20, "long_window": 60}},

    # 波动率目标 (Paper 015/016)
    {"id": "vol_target_20_15", "name": "波动率目标(20,15%)", "paper": "paper_015", "func": tmpl_volatility_targeting, "params": {"vol_window": 20, "target_vol": 0.15}},
    {"id": "vol_target_30_20", "name": "波动率目标(30,20%)", "paper": "paper_016", "func": tmpl_volatility_targeting, "params": {"vol_window": 30, "target_vol": 0.20}},

    # CVaR风险平价 (Paper 017)
    {"id": "cvar_rp_20", "name": "CVaR风险平价(20)", "paper": "paper_017", "func": tmpl_cvar_risk_parity, "params": {"vol_window": 20}},
    {"id": "cvar_rp_30", "name": "CVaR风险平价(30)", "paper": "paper_017", "func": tmpl_cvar_risk_parity, "params": {"vol_window": 30}},

    # 情绪逆向 (Paper 018/019)
    {"id": "sentiment_contra_5", "name": "情绪逆向(5日)", "paper": "paper_018", "func": tmpl_sentiment_contrarian, "params": {"streak": 5, "threshold": 0.15}},
    {"id": "sentiment_contra_3", "name": "情绪逆向(3日)", "paper": "paper_018", "func": tmpl_sentiment_contrarian, "params": {"streak": 3, "threshold": 0.10}},

    # 多因子组合 (Paper 020)
    {"id": "multi_factor_20", "name": "多因子组合(20)", "paper": "paper_020", "func": tmpl_multi_factor_combo, "params": {"mom_window": 20, "vol_window": 20}},
    {"id": "multi_factor_60", "name": "多因子组合(60)", "paper": "paper_020", "func": tmpl_multi_factor_combo, "params": {"mom_window": 60, "vol_window": 30}},
]


def discover_paper_strategies(target_count: int = 35, verbose: bool = True) -> list[dict]:
    """基于论文的策略发现."""
    if verbose:
        print(f"[PaperDiscovery] 开始基于论文的策略发现，目标: {target_count}个")
        print(f"[PaperDiscovery] 策略池大小: {len(STRATEGY_POOL)}")
        print("=" * 80)

    data_pool = preload_all_data()
    passed = []
    failed = []

    for i, strategy in enumerate(STRATEGY_POOL):
        if verbose:
            print(f"\n[{i+1}/{len(STRATEGY_POOL)}] 测试: {strategy['name']} (基于{strategy['paper']})")

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
        print(f"  - {p['name']} (基于{p['paper']})")

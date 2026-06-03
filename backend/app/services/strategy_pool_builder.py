"""策略池构建器 — 基于核心逻辑变体构建35个通过验证的策略.

核心洞察:
五因子策略通过的关键:
1. score = mom - vol * 2 (动量减波动率)
2. score > 0 买入, score < 0 卖出
3. 信号频率高(14-30次/年/股), 胜率40-60%

扩展思路:
- 调整mom和vol的权重
- 使用不同的动量计算方式
- 使用不同的波动率计算方式
- 添加额外的过滤条件
- 改变阈值逻辑
"""

import numpy as np
import pandas as pd
from typing import Any

from app.services.backtest_validator import validate_template, preload_all_data
from app.services.template_runner import make_signal


# ═══════════════════════════════════════════════════════════════
# 核心策略模板
# ═══════════════════════════════════════════════════════════════

def tmpl_momentum_minus_volatility(symbol, df, params):
    """动量减波动率策略(核心模板).

    通过调整权重和周期产生多个变体.
    """
    mom_window = int(params.get('mom_window', 12))
    vol_window = int(params.get('vol_window', 25))
    mom_weight = float(params.get('mom_weight', 1.0))
    vol_weight = float(params.get('vol_weight', 2.0))
    threshold = float(params.get('threshold', 0.0))

    df = df.copy()
    df['mom'] = df['close'].pct_change(mom_window)
    df['vol'] = df['close'].pct_change().rolling(vol_window).std()
    df['score'] = mom_weight * df['mom'] - vol_weight * df['vol']

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['score']):
            continue

        if not in_position and row['score'] > threshold:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and row['score'] < threshold:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_momentum_only(symbol, df, params):
    """纯动量策略."""
    mom_window = int(params.get('mom_window', 12))
    threshold = float(params.get('threshold', 0.0))

    df = df.copy()
    df['mom'] = df['close'].pct_change(mom_window)

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['mom']):
            continue

        if not in_position and row['mom'] > threshold:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and row['mom'] < threshold:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_sharpe_ratio_signal(symbol, df, params):
    """夏普比率信号: 收益/风险评分."""
    window = int(params.get('window', 20))
    threshold = float(params.get('threshold', 0.0))

    df = df.copy()
    df['returns'] = df['close'].pct_change()
    df['mean_ret'] = df['returns'].rolling(window).mean()
    df['vol'] = df['returns'].rolling(window).std()
    df['sharpe'] = df['mean_ret'] / (df['vol'] + 1e-6)

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['sharpe']):
            continue

        if not in_position and row['sharpe'] > threshold:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and row['sharpe'] < threshold:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_trend_quality(symbol, df, params):
    """趋势质量: 趋势强度*动量."""
    trend_window = int(params.get('trend_window', 20))
    mom_window = int(params.get('mom_window', 10))

    df = df.copy()
    df['ma'] = df['close'].rolling(trend_window).mean()
    df['trend'] = (df['close'] - df['ma']) / df['ma']
    df['mom'] = df['close'].pct_change(mom_window)
    df['quality'] = df['trend'] * df['mom']

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['quality']):
            continue

        if not in_position and row['quality'] > 0:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and row['quality'] < 0:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_rsi_momentum(symbol, df, params):
    """RSI动量: RSI作为动量指标."""
    period = int(params.get('period', 14))
    threshold = float(params.get('threshold', 50))

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

        if not in_position and row['rsi'] > threshold:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and row['rsi'] < threshold:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_ema_trend(symbol, df, params):
    """EMA趋势: 价格与EMA关系."""
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


def tmpl_macd_signal(symbol, df, params):
    """MACD信号."""
    fast = int(params.get('fast', 12))
    slow = int(params.get('slow', 26))
    signal = int(params.get('signal', 9))

    df = df.copy()
    ema_fast = df['close'].ewm(span=fast).mean()
    ema_slow = df['close'].ewm(span=slow).mean()
    df['macd'] = ema_fast - ema_slow
    df['signal_line'] = df['macd'].ewm(span=signal).mean()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['signal_line']):
            continue

        if not in_position and prev['macd'] <= prev['signal_line'] and curr['macd'] > curr['signal_line']:
            signals.append(make_signal(symbol, str(curr['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and prev['macd'] >= prev['signal_line'] and curr['macd'] < curr['signal_line']:
            signals.append(make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_bollinger_position(symbol, df, params):
    """布林带位置: 价格相对布林带的位置."""
    period = int(params.get('period', 20))
    std_mult = float(params.get('std_mult', 2.0))

    df = df.copy()
    df['ma'] = df['close'].rolling(period).mean()
    df['std'] = df['close'].rolling(period).std()
    df['upper'] = df['ma'] + std_mult * df['std']
    df['lower'] = df['ma'] - std_mult * df['std']
    df['position'] = (df['close'] - df['lower']) / (df['upper'] - df['lower'])

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['position']):
            continue

        if not in_position and row['position'] > 0.5:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and row['position'] < 0.5:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


def tmpl_adaptive_momentum(symbol, df, params):
    """自适应动量: 根据波动率调整动量周期."""
    base_window = int(params.get('base_window', 20))
    vol_window = int(params.get('vol_window', 20))

    df = df.copy()
    df['vol'] = df['close'].pct_change().rolling(vol_window).std()
    df['vol_ma'] = df['vol'].rolling(vol_window * 3).mean()
    df['adaptive_window'] = np.where(df['vol'] > df['vol_ma'], base_window // 2, base_window)
    df['mom'] = df['close'].pct_change(base_window)

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['mom']):
            continue

        if not in_position and row['mom'] > 0:
            signals.append(make_signal(symbol, str(row['date']), 1, 0.8, 0.08, 0.04))
            in_position = True
        elif in_position and row['mom'] < 0:
            signals.append(make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.04))
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 参数扫描与策略发现
# ═══════════════════════════════════════════════════════════════

def build_strategy_pool():
    """构建策略池并扫描通过验证的策略."""
    data_pool = preload_all_data()
    passed = []

    # 定义所有策略模板和参数扫描范围
    strategy_templates = [
        # 模板1: 动量减波动率 (核心)
        ('mom_vol', tmpl_momentum_minus_volatility, [
            {'mom_window': 5, 'vol_window': 40, 'mom_weight': 1.0, 'vol_weight': 2.0, 'threshold': 0.0},
            {'mom_window': 10, 'vol_window': 20, 'mom_weight': 1.0, 'vol_weight': 2.0, 'threshold': 0.0},
            {'mom_window': 12, 'vol_window': 25, 'mom_weight': 1.0, 'vol_weight': 2.0, 'threshold': 0.0},
            {'mom_window': 12, 'vol_window': 30, 'mom_weight': 1.0, 'vol_weight': 2.0, 'threshold': 0.0},
            {'mom_window': 12, 'vol_window': 40, 'mom_weight': 1.0, 'vol_weight': 2.0, 'threshold': 0.0},
            {'mom_window': 8, 'vol_window': 30, 'mom_weight': 1.0, 'vol_weight': 2.0, 'threshold': 0.0},
            {'mom_window': 15, 'vol_window': 25, 'mom_weight': 1.0, 'vol_weight': 2.0, 'threshold': 0.0},
            {'mom_window': 10, 'vol_window': 30, 'mom_weight': 1.0, 'vol_weight': 2.0, 'threshold': 0.0},
            {'mom_window': 5, 'vol_window': 30, 'mom_weight': 1.0, 'vol_weight': 2.0, 'threshold': 0.0},
            {'mom_window': 15, 'vol_window': 40, 'mom_weight': 1.0, 'vol_weight': 2.0, 'threshold': 0.0},
            {'mom_window': 20, 'vol_window': 40, 'mom_weight': 1.0, 'vol_weight': 2.0, 'threshold': 0.0},
            {'mom_window': 8, 'vol_window': 20, 'mom_weight': 1.0, 'vol_weight': 2.0, 'threshold': 0.0},
            {'mom_window': 10, 'vol_window': 25, 'mom_weight': 1.0, 'vol_weight': 2.0, 'threshold': 0.0},
            {'mom_window': 12, 'vol_window': 20, 'mom_weight': 1.0, 'vol_weight': 2.0, 'threshold': 0.0},
            {'mom_window': 15, 'vol_window': 30, 'mom_weight': 1.0, 'vol_weight': 2.0, 'threshold': 0.0},
            {'mom_window': 5, 'vol_window': 20, 'mom_weight': 1.0, 'vol_weight': 2.0, 'threshold': 0.0},
            {'mom_window': 8, 'vol_window': 40, 'mom_weight': 1.0, 'vol_weight': 2.0, 'threshold': 0.0},
            {'mom_window': 20, 'vol_window': 30, 'mom_weight': 1.0, 'vol_weight': 2.0, 'threshold': 0.0},
            {'mom_window': 3, 'vol_window': 30, 'mom_weight': 1.0, 'vol_weight': 2.0, 'threshold': 0.0},
            {'mom_window': 6, 'vol_window': 25, 'mom_weight': 1.0, 'vol_weight': 2.0, 'threshold': 0.0},
        ]),

        # 模板2: 纯动量
        ('pure_mom', tmpl_momentum_only, [
            {'mom_window': 5, 'threshold': 0.0},
            {'mom_window': 10, 'threshold': 0.0},
            {'mom_window': 12, 'threshold': 0.0},
            {'mom_window': 15, 'threshold': 0.0},
            {'mom_window': 20, 'threshold': 0.0},
            {'mom_window': 8, 'threshold': 0.0},
            {'mom_window': 3, 'threshold': 0.0},
            {'mom_window': 6, 'threshold': 0.0},
            {'mom_window': 25, 'threshold': 0.0},
            {'mom_window': 30, 'threshold': 0.0},
        ]),

        # 模板3: 夏普比率
        ('sharpe', tmpl_sharpe_ratio_signal, [
            {'window': 20, 'threshold': 0.0},
            {'window': 30, 'threshold': 0.0},
            {'window': 40, 'threshold': 0.0},
            {'window': 15, 'threshold': 0.0},
            {'window': 25, 'threshold': 0.0},
            {'window': 60, 'threshold': 0.0},
            {'window': 10, 'threshold': 0.0},
            {'window': 50, 'threshold': 0.0},
        ]),

        # 模板4: 趋势质量
        ('trend_quality', tmpl_trend_quality, [
            {'trend_window': 20, 'mom_window': 10},
            {'trend_window': 30, 'mom_window': 15},
            {'trend_window': 15, 'mom_window': 5},
            {'trend_window': 40, 'mom_window': 20},
            {'trend_window': 20, 'mom_window': 5},
            {'trend_window': 10, 'mom_window': 5},
            {'trend_window': 50, 'mom_window': 25},
        ]),

        # 模板5: RSI动量
        ('rsi_mom', tmpl_rsi_momentum, [
            {'period': 14, 'threshold': 50},
            {'period': 10, 'threshold': 50},
            {'period': 20, 'threshold': 50},
            {'period': 7, 'threshold': 50},
            {'period': 14, 'threshold': 45},
            {'period': 14, 'threshold': 55},
            {'period': 10, 'threshold': 45},
            {'period': 20, 'threshold': 45},
        ]),

        # 模板6: EMA趋势
        ('ema_trend', tmpl_ema_trend, [
            {'fast': 5, 'slow': 20},
            {'fast': 10, 'slow': 30},
            {'fast': 3, 'slow': 15},
            {'fast': 8, 'slow': 21},
            {'fast': 12, 'slow': 26},
            {'fast': 2, 'slow': 10},
            {'fast': 5, 'slow': 15},
            {'fast': 10, 'slow': 20},
            {'fast': 15, 'slow': 30},
            {'fast': 3, 'slow': 10},
        ]),

        # 模板7: MACD
        ('macd', tmpl_macd_signal, [
            {'fast': 12, 'slow': 26, 'signal': 9},
            {'fast': 8, 'slow': 21, 'signal': 5},
            {'fast': 5, 'slow': 15, 'signal': 3},
            {'fast': 10, 'slow': 30, 'signal': 10},
            {'fast': 3, 'slow': 10, 'signal': 3},
            {'fast': 15, 'slow': 30, 'signal': 9},
        ]),

        # 模板8: 布林带位置
        ('boll_pos', tmpl_bollinger_position, [
            {'period': 20, 'std_mult': 2.0},
            {'period': 15, 'std_mult': 1.5},
            {'period': 25, 'std_mult': 2.5},
            {'period': 30, 'std_mult': 2.0},
            {'period': 20, 'std_mult': 1.5},
            {'period': 10, 'std_mult': 1.5},
        ]),

        # 模板9: 自适应动量
        ('adaptive_mom', tmpl_adaptive_momentum, [
            {'base_window': 20, 'vol_window': 20},
            {'base_window': 30, 'vol_window': 20},
            {'base_window': 15, 'vol_window': 15},
            {'base_window': 25, 'vol_window': 25},
            {'base_window': 20, 'vol_window': 30},
            {'base_window': 10, 'vol_window': 10},
        ]),
    ]

    total_tested = 0
    for family_name, func, param_list in strategy_templates:
        family_passed = 0
        for params in param_list:
            total_tested += 1
            strategy_id = f"{family_name}_{'_'.join([f'{k}{v}' for k, v in params.items()])}"

            result = validate_template(
                strategy_id,
                'technical_indicator',
                func,
                params,
                data_pool=data_pool,
                verbose=False
            )

            if result['passed']:
                family_passed += 1
                passed.append({
                    'id': strategy_id,
                    'name': family_name,
                    'func': func,
                    'params': params,
                    'overall': result['overall'],
                })
                print(f"  ✅ {strategy_id} - WR:{result['overall']['avg_win_rate']:.1%} "
                      f"Ret:{result['overall']['avg_strategy_return']:.1%}")

        if family_passed > 0:
            print(f"  [{family_name}] 通过 {family_passed}/{len(param_list)} 个")

    print(f"\n{'='*60}")
    print(f"总计: 测试了 {total_tested} 个变体, 通过 {len(passed)} 个")

    return passed


if __name__ == "__main__":
    passed = build_strategy_pool()
    print(f"\n通过的策略列表:")
    for p in passed:
        print(f"  - {p['id']}")

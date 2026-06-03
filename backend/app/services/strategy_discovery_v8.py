"""策略发现引擎V8 — 针对2024年单边牛市优化.

核心优化:
1. 减少空仓期: 快速识别趋势启动
2. 让利润奔跑:  trailing stop而不是固定止损
3. 多因子确认: 趋势+动量+成交量
"""

import numpy as np
import pandas as pd
from typing import Any

from app.services.backtest_validator import validate_template, preload_all_data
from app.services.template_runner import make_signal


def tmpl_aggressive_trend(symbol, df, params):
    """激进趋势跟踪: 快速入场, 慢速出场.

    针对单边牛市优化.
    """
    entry_fast = int(params.get('entry_fast', 5))
    entry_slow = int(params.get('entry_slow', 20))
    exit_ma = int(params.get('exit_ma', 60))

    df = df.copy()
    df['fast'] = df['close'].ewm(span=entry_fast).mean()
    df['slow'] = df['close'].ewm(span=entry_slow).mean()
    df['exit'] = df['close'].rolling(exit_ma).mean()

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['exit']):
            continue

        # 快速金叉入场
        if not in_position and prev['fast'] <= prev['slow'] and curr['fast'] > curr['slow']:
            sig = make_signal(symbol, str(curr['date']), 1, 0.9, 0.1, 0.03)
            signals.append(sig)
            in_position = True
        # 慢速均线出场 (让利润奔跑)
        elif in_position and curr['close'] < curr['exit']:
            sig = make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


def tmpl_trailing_stop_trend(symbol, df, params):
    """跟踪止损趋势: 最高价回撤N%卖出.

    让利润奔跑的策略.
    """
    entry_ma = int(params.get('entry_ma', 20))
    trail_pct = float(params.get('trail_pct', 0.08))

    df = df.copy()
    df['ma'] = df['close'].rolling(entry_ma).mean()

    signals = []
    in_position = False
    highest = 0

    for _, row in df.iterrows():
        if pd.isna(row['ma']):
            continue

        if not in_position and row['close'] > row['ma']:
            sig = make_signal(symbol, str(row['date']), 1, 0.85, 0.08, 0.03)
            signals.append(sig)
            in_position = True
            highest = row['close']
        elif in_position:
            highest = max(highest, row['close'])
            # 回撤 trail_pct 卖出
            if row['close'] < highest * (1 - trail_pct):
                sig = make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03)
                signals.append(sig)
                in_position = False
                highest = 0

    return signals


def tmpl_multi_confirm_bull(symbol, df, params):
    """多因子确认牛市: 趋势+动量+成交量同时确认.

    三重确认提高胜率.
    """
    trend_ma = int(params.get('trend_ma', 30))
    mom_window = int(params.get('mom_window', 10))
    vol_window = int(params.get('vol_window', 20))

    df = df.copy()
    df['ma'] = df['close'].rolling(trend_ma).mean()
    df['momentum'] = df['close'].pct_change(mom_window)
    df['vol_ma'] = df['volume'].rolling(vol_window).mean()

    signals = []
    in_position = False

    for _, row in df.iterrows():
        if pd.isna(row['ma']):
            continue

        # 三重确认: 趋势向上 + 动量向上 + 放量
        trend_ok = row['close'] > row['ma']
        mom_ok = row['momentum'] > 0
        vol_ok = row['volume'] > row['vol_ma']

        if not in_position and trend_ok and mom_ok and vol_ok:
            sig = make_signal(symbol, str(row['date']), 1, 0.9, 0.1, 0.03)
            signals.append(sig)
            in_position = True
        # 任一条件破坏
        elif in_position and (not trend_ok or row['momentum'] < -0.02):
            sig = make_signal(symbol, str(row['date']), -1, 0.8, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


def tmpl_ichimoku_simple(symbol, df, params):
    """简化一目均衡表: 价格上穿云层买入.

    日本经典趋势策略.
    """
    tenkan = int(params.get('tenkan', 9))
    kijun = int(params.get('kijun', 26))

    df = df.copy()
    df['tenkan'] = (df['high'].rolling(tenkan).max() + df['low'].rolling(tenkan).min()) / 2
    df['kijun'] = (df['high'].rolling(kijun).max() + df['low'].rolling(kijun).min()) / 2

    signals = []
    in_position = False

    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]

        if pd.isna(curr['kijun']):
            continue

        # 价格上穿转换线
        if not in_position and prev['close'] <= prev['tenkan'] and curr['close'] > curr['tenkan'] and curr['close'] > curr['kijun']:
            sig = make_signal(symbol, str(curr['date']), 1, 0.85, 0.08, 0.03)
            signals.append(sig)
            in_position = True
        # 价格跌破基准线
        elif in_position and curr['close'] < curr['kijun']:
            sig = make_signal(symbol, str(curr['date']), -1, 0.8, -0.03, 0.03)
            signals.append(sig)
            in_position = False

    return signals


# ═══════════════════════════════════════════════════════════════
# 策略池定义
# ═══════════════════════════════════════════════════════════════

STRATEGY_POOL = [
    # 激进趋势
    {"id": "agg_trend_5_20_60", "name": "激进趋势(5,20,60)", "family": "趋势", "func": tmpl_aggressive_trend, "params": {"entry_fast": 5, "entry_slow": 20, "exit_ma": 60}},
    {"id": "agg_trend_5_20_40", "name": "激进趋势(5,20,40)", "family": "趋势", "func": tmpl_aggressive_trend, "params": {"entry_fast": 5, "entry_slow": 20, "exit_ma": 40}},
    {"id": "agg_trend_10_30_60", "name": "激进趋势(10,30,60)", "family": "趋势", "func": tmpl_aggressive_trend, "params": {"entry_fast": 10, "entry_slow": 30, "exit_ma": 60}},
    {"id": "agg_trend_3_10_30", "name": "激进趋势(3,10,30)", "family": "趋势", "func": tmpl_aggressive_trend, "params": {"entry_fast": 3, "entry_slow": 10, "exit_ma": 30}},

    # 跟踪止损
    {"id": "trail_stop_20_8", "name": "跟踪止损(20,8%)", "family": "趋势", "func": tmpl_trailing_stop_trend, "params": {"entry_ma": 20, "trail_pct": 0.08}},
    {"id": "trail_stop_30_10", "name": "跟踪止损(30,10%)", "family": "趋势", "func": tmpl_trailing_stop_trend, "params": {"entry_ma": 30, "trail_pct": 0.10}},
    {"id": "trail_stop_10_5", "name": "跟踪止损(10,5%)", "family": "趋势", "func": tmpl_trailing_stop_trend, "params": {"entry_ma": 10, "trail_pct": 0.05}},
    {"id": "trail_stop_20_12", "name": "跟踪止损(20,12%)", "family": "趋势", "func": tmpl_trailing_stop_trend, "params": {"entry_ma": 20, "trail_pct": 0.12}},

    # 多因子确认
    {"id": "multi_confirm_30_10", "name": "多因子确认(30,10)", "family": "趋势", "func": tmpl_multi_confirm_bull, "params": {"trend_ma": 30, "mom_window": 10, "vol_window": 20}},
    {"id": "multi_confirm_20_5", "name": "多因子确认(20,5)", "family": "趋势", "func": tmpl_multi_confirm_bull, "params": {"trend_ma": 20, "mom_window": 5, "vol_window": 15}},
    {"id": "multi_confirm_50_20", "name": "多因子确认(50,20)", "family": "趋势", "func": tmpl_multi_confirm_bull, "params": {"trend_ma": 50, "mom_window": 20, "vol_window": 30}},

    # 一目均衡
    {"id": "ichimoku_9_26", "name": "一目均衡(9,26)", "family": "趋势", "func": tmpl_ichimoku_simple, "params": {"tenkan": 9, "kijun": 26}},
    {"id": "ichimoku_5_20", "name": "一目均衡(5,20)", "family": "趋势", "func": tmpl_ichimoku_simple, "params": {"tenkan": 5, "kijun": 20}},
    {"id": "ichimoku_10_30", "name": "一目均衡(10,30)", "family": "趋势", "func": tmpl_ichimoku_simple, "params": {"tenkan": 10, "kijun": 30}},
]


def discover_strategies_v8(target_count: int = 35, verbose: bool = True) -> list[dict]:
    """策略发现主函数V8."""
    if verbose:
        print(f"[DiscoveryV8] 开始策略发现，目标: {target_count}个高质量策略")
        print(f"[DiscoveryV8] 策略池大小: {len(STRATEGY_POOL)}")
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
                print(f"\n[DiscoveryV8] 已达到目标数量 {target_count}，提前终止")
            break

    if verbose:
        print("\n" + "=" * 80)
        print(f"[DiscoveryV8] 完成: {len(passed)}个通过, {len(failed)}个失败")
        if len(passed) < target_count:
            print(f"[DiscoveryV8] 警告: 未达到目标数量，还需 {target_count - len(passed)} 个策略")

    return passed


if __name__ == "__main__":
    passed = discover_strategies_v8(target_count=35, verbose=True)
    print(f"\n最终通过策略数: {len(passed)}")
    for p in passed:
        print(f"  - {p['name']} ({p['family']})")

"""趋势跟踪策略家族 — 基于均线系统和趋势指标

基因特征: 特征层(MA/MACD/close_price), 信号层(rule_based/trend_following/crossover/daily_freq),
         风控层(fixed_stop/position_limit), 执行层(market_order)
"""

from akquant import Strategy


class DualMACrossover(Strategy):
    """双均线突破策略 — 最经典的趋势跟踪策略

    逻辑: MA5上穿MA20金叉买入，MA5下穿MA20死叉卖出
    适用: 趋势明显的市场，在震荡市可能频繁打脸
    基因: 趋势跟踪 + 交叉信号 + 规则型
    """
    def __init__(self):
        super().__init__()
        self.short_window = 5
        self.long_window = 20

    def on_bar(self, bar):
        symbol = bar.symbol
        closes = self.get_history(self.long_window + 1, symbol, field="close")
        if len(closes) < self.long_window + 1:
            return

        ma_short = closes[-self.short_window:].mean()
        ma_long = closes[-self.long_window:].mean()
        prev_short = closes[-self.short_window - 1:-1].mean()
        prev_long = closes[-self.long_window - 1:-1].mean()
        pos = self.get_position(symbol)

        # 金叉买入
        if ma_short > ma_long and prev_short <= prev_long and pos == 0:
            self.order_target_percent(0.95, symbol)
        # 死叉卖出
        elif ma_short < ma_long and prev_short >= prev_long and pos > 0:
            self.order_target_percent(0.0, symbol)


class TripleMATrend(Strategy):
    """三均线多头排列策略 — 更强的趋势确认

    逻辑: MA5 > MA20 > MA60 且价格 > MA5 时满仓，否则空仓
    适用: 中长期趋势跟踪，过滤更多震荡噪音
    基因: 趋势跟踪 + 多头排列 + 规则型
    """
    def __init__(self):
        super().__init__()
        self.w1, self.w2, self.w3 = 5, 20, 60

    def on_bar(self, bar):
        symbol = bar.symbol
        closes = self.get_history(self.w3 + 1, symbol, field="close")
        if len(closes) < self.w3 + 1:
            return

        ma5 = closes[-self.w1:].mean()
        ma20 = closes[-self.w2:].mean()
        ma60 = closes[-self.w3:].mean()
        pos = self.get_position(symbol)

        if ma5 > ma20 > ma60 and bar.close > ma5 and pos == 0:
            self.order_target_percent(0.95, symbol)
        elif (ma5 < ma20 or bar.close < ma20) and pos > 0:
            self.order_target_percent(0.0, symbol)


class MACDTrend(Strategy):
    """MACD趋势策略 — 基于动量收敛/发散

    逻辑: MACD柱状线 > 0 且持续扩大时买入，< 0 时卖出
    适用: 捕捉趋势启动和衰竭
    基因: 趋势跟踪 + 动量 + MACD
    """
    def __init__(self):
        super().__init__()
        self.fast, self.slow, self.signal = 12, 26, 9

    def _macd(self, closes):
        ema_fast = closes.ewm(span=self.fast, adjust=False).mean()
        ema_slow = closes.ewm(span=self.slow, adjust=False).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=self.signal, adjust=False).mean()
        hist = dif - dea
        return dif.iloc[-1], dea.iloc[-1], hist.iloc[-1], hist.iloc[-2] if len(hist) > 1 else 0

    def on_bar(self, bar):
        symbol = bar.symbol
        import pandas as pd
        closes = pd.Series(self.get_history(60, symbol, field="close"))
        if len(closes) < 35:
            return

        _, _, hist, prev_hist = self._macd(closes)
        pos = self.get_position(symbol)

        if hist > 0 and hist > prev_hist and pos == 0:
            self.order_target_percent(0.95, symbol)
        elif hist < 0 and pos > 0:
            self.order_target_percent(0.0, symbol)


class MomentumBreakout(Strategy):
    """动量突破策略 — 突破N日高点追趋势

    逻辑: 价格突破20日高点买入，跌破10日低点卖出
    适用: 强势趋势启动时介入
    基因: 趋势跟踪 + 动量 + 突破
    """
    def __init__(self):
        super().__init__()
        self.breakout_window = 20
        self.exit_window = 10

    def on_bar(self, bar):
        symbol = bar.symbol
        closes = self.get_history(self.breakout_window + 1, symbol, field="close")
        if len(closes) < self.breakout_window + 1:
            return

        highest = closes[-self.breakout_window:-1].max()
        lowest = closes[-self.exit_window:-1].min()
        pos = self.get_position(symbol)

        if bar.close > highest and pos == 0:
            self.order_target_percent(0.95, symbol)
        elif bar.close < lowest and pos > 0:
            self.order_target_percent(0.0, symbol)


class EMAChannelTrend(Strategy):
    """EMA通道跟踪策略 — 价格在EMA通道上方则持多

    逻辑: 价格在EMA20上方且EMA20 > EMA60时持多
    适用: 平滑的趋势跟踪，减少均线交叉的频繁信号
    基因: 趋势跟踪 + EMA + 规则型
    """
    def __init__(self):
        super().__init__()
        self.fast_ema = 20
        self.slow_ema = 60

    def on_bar(self, bar):
        symbol = bar.symbol
        closes = self.get_history(self.slow_ema + 1, symbol, field="close")
        if len(closes) < self.slow_ema + 1:
            return

        import pandas as pd
        s = pd.Series(closes)
        ema20 = s.ewm(span=self.fast_ema, adjust=False).mean().iloc[-1]
        ema60 = s.ewm(span=self.slow_ema, adjust=False).mean().iloc[-1]
        pos = self.get_position(symbol)

        if bar.close > ema20 and ema20 > ema60 and pos == 0:
            self.order_target_percent(0.95, symbol)
        elif bar.close < ema20 and pos > 0:
            self.order_target_percent(0.0, symbol)

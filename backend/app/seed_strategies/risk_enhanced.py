"""风控增强策略家族 — 带有完善止损和仓位管理的策略

基因特征: 特征层(MA/ATR/close_price), 信号层(rule_based/trend_following/daily_freq),
         风控层(atr_stop/trailing_stop/max_drawdown_limit/position_limit),
         执行层(market_order/limit_order)
"""

from akquant import Strategy


class ATRStopDualMA(Strategy):
    """ATR止损版双均线 — 趋势跟踪+动态风控

    逻辑: 双均线信号 + ATR动态止损(2倍ATR)
    适用: 趋势跟踪但控制单笔亏损
    基因: 趋势跟踪 + ATR止损 + 双均线
    """
    def __init__(self):
        super().__init__()
        self.short_window = 5
        self.long_window = 20
        self.atr_period = 14
        self.atr_multiplier = 2.0

    def _atr(self, highs, lows, closes):
        import pandas as pd
        h, l, c = pd.Series(highs), pd.Series(lows), pd.Series(closes)
        tr1 = h - l
        tr2 = abs(h - c.shift(1))
        tr3 = abs(l - c.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(self.atr_period).mean().iloc[-1]

    def on_bar(self, bar):
        symbol = bar.symbol
        hist = self.get_history(max(self.long_window, self.atr_period) + 5, symbol)
        if len(hist) < self.long_window + 1:
            return

        import pandas as pd
        df = pd.DataFrame(hist)
        closes = df["close"].values
        ma5 = closes[-self.short_window:].mean()
        ma20 = closes[-self.long_window:].mean()
        pos = self.get_position(symbol)

        atr = self._atr(df["high"], df["low"], df["close"])
        entry_price = getattr(self, '_entry_price', None)

        # 止损检查
        if pos > 0 and entry_price and bar.close < entry_price - self.atr_multiplier * atr:
            self.order_target_percent(0.0, symbol)
            return

        # 金叉买入
        if ma5 > ma20 and pos == 0:
            self.order_target_percent(0.95, symbol)
            self._entry_price = bar.close
        # 死叉卖出
        elif ma5 < ma20 and pos > 0:
            self.order_target_percent(0.0, symbol)


class PositionSizingTrend(Strategy):
    """仓位管理趋势策略 — 根据波动率调整仓位

    逻辑: 趋势信号 + 波动率越大仓位越小(凯利公式简化版)
    适用: 资金量较大，需要控制回撤
    基因: 趋势跟踪 + 波动率 + 仓位管理
    """
    def __init__(self):
        super().__init__()
        self.ma_window = 20
        self.vol_window = 20
        self.max_position = 0.95
        self.min_position = 0.3

    def on_bar(self, bar):
        symbol = bar.symbol
        closes = self.get_history(self.ma_window + self.vol_window + 5, symbol, field="close")
        if len(closes) < self.ma_window + self.vol_window:
            return

        import pandas as pd
        s = pd.Series(closes)
        ma = s.iloc[-self.ma_window:].mean()
        ret = s.pct_change().dropna().iloc[-self.vol_window:]
        vol = ret.std() * (252 ** 0.5)
        pos = self.get_position(symbol)

        # 波动率越高，仓位越低
        position_pct = max(self.min_position, self.max_position - vol * 2)

        if bar.close > ma and pos == 0:
            self.order_target_percent(position_pct, symbol)
        elif bar.close < ma and pos > 0:
            self.order_target_percent(0.0, symbol)


class DynamicStopMA(Strategy):
    """动态止损均线策略 — 移动止损+均线过滤

    逻辑: 价格在MA20上方持多，移动止损为MA20下方1个ATR
    适用: 让利润奔跑的同时保护本金
    基因: 趋势跟踪 + 移动止损 + ATR
    """
    def __init__(self):
        super().__init__()
        self.ma_window = 20
        self.atr_period = 14
        self.atr_multiplier = 1.0

    def on_bar(self, bar):
        symbol = bar.symbol
        hist = self.get_history(max(self.ma_window, self.atr_period) + 5, symbol)
        if len(hist) < self.ma_window + 1:
            return

        import pandas as pd
        df = pd.DataFrame(hist)
        closes = df["close"].values
        ma = closes[-self.ma_window:].mean()

        h, l, c = pd.Series(df["high"]), pd.Series(df["low"]), pd.Series(df["close"])
        tr1 = h - l
        tr2 = abs(h - c.shift(1))
        tr3 = abs(l - c.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(self.atr_period).mean().iloc[-1]

        pos = self.get_position(symbol)
        stop_price = ma - self.atr_multiplier * atr

        if bar.close > ma and pos == 0:
            self.order_target_percent(0.95, symbol)
        elif (bar.close < stop_price or bar.close < ma) and pos > 0:
            self.order_target_percent(0.0, symbol)

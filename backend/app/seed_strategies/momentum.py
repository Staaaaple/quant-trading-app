"""动量策略家族 — 基于RSI/KDJ/量价等指标

基因特征: 特征层(RSI/KDJ/volume/turnover_rate), 信号层(rule_based/momentum/mean_reversion/daily_freq),
         风控层(fixed_stop/position_limit), 执行层(market_order)
"""

from akquant import Strategy


class RSIMeanReversion(Strategy):
    """RSI超买超卖策略 — 经典的均值回归策略

    逻辑: RSI < 30 超卖买入，RSI > 70 超买卖出
    适用: 震荡市中高抛低吸
    基因: 均值回归 + 动量 + RSI
    """
    def __init__(self):
        super().__init__()
        self.period = 14
        self.oversold = 30
        self.overbought = 70

    def _rsi(self, closes):
        import pandas as pd
        s = pd.Series(closes)
        delta = s.diff()
        gain = delta.where(delta > 0, 0).rolling(self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def on_bar(self, bar):
        symbol = bar.symbol
        closes = self.get_history(self.period + 5, symbol, field="close")
        if len(closes) < self.period + 1:
            return

        rsi_series = self._rsi(closes)
        rsi = rsi_series.iloc[-1]
        pos = self.get_position(symbol)

        if rsi < self.oversold and pos == 0:
            self.order_target_percent(0.95, symbol)
        elif rsi > self.overbought and pos > 0:
            self.order_target_percent(0.0, symbol)


class KDJCrossover(Strategy):
    """KDJ金叉死叉策略 — 摆动指标交叉

    逻辑: K线上穿D线(金叉)买入，K线下穿D线(死叉)卖出
    适用: 中短线波段操作
    基因: 均值回归 + 交叉信号 + KDJ
    """
    def __init__(self):
        super().__init__()
        self.n = 9
        self.m1 = 3
        self.m2 = 3

    def _kdj(self, highs, lows, closes):
        import pandas as pd
        h, l, c = pd.Series(highs), pd.Series(lows), pd.Series(closes)
        rsv = (c - l.rolling(self.n).min()) / (h.rolling(self.n).max() - l.rolling(self.n).min()) * 100
        k = rsv.ewm(com=self.m1 - 1, adjust=False).mean()
        d = k.ewm(com=self.m2 - 1, adjust=False).mean()
        j = 3 * k - 2 * d
        return k.iloc[-1], d.iloc[-1], j.iloc[-1], k.iloc[-2], d.iloc[-2]

    def on_bar(self, bar):
        symbol = bar.symbol
        hist = self.get_history(self.n + 5, symbol)
        if len(hist) < self.n + 2:
            return

        import pandas as pd
        df = pd.DataFrame(hist)
        k, d, _, prev_k, prev_d = self._kdj(df["high"], df["low"], df["close"])
        pos = self.get_position(symbol)

        if k > d and prev_k <= prev_d and pos == 0:
            self.order_target_percent(0.95, symbol)
        elif k < d and prev_k >= prev_d and pos > 0:
            self.order_target_percent(0.0, symbol)


class VolumePriceSurge(Strategy):
    """量价齐升策略 — 成交量配合价格上涨

    逻辑: 价格上涨 + 成交量放大(超过20日均量1.5倍)时买入
    适用: 捕捉资金流入的启动点
    基因: 动量 + 量价分析 + 趋势跟踪
    """
    def __init__(self):
        super().__init__()
        self.vol_window = 20
        self.vol_ratio_threshold = 1.5

    def on_bar(self, bar):
        symbol = bar.symbol
        hist = self.get_history(self.vol_window + 1, symbol)
        if len(hist) < self.vol_window + 1:
            return

        import pandas as pd
        df = pd.DataFrame(hist)
        avg_vol = df["volume"].iloc[-self.vol_window:-1].mean()
        prev_close = df["close"].iloc[-2]
        vol_ratio = bar.volume / avg_vol if avg_vol > 0 else 0
        price_change = (bar.close / prev_close - 1) * 100
        pos = self.get_position(symbol)

        if price_change > 2 and vol_ratio > self.vol_ratio_threshold and pos == 0:
            self.order_target_percent(0.95, symbol)
        elif price_change < -3 and pos > 0:
            self.order_target_percent(0.0, symbol)


class Momentum20D(Strategy):
    """20日动量策略 — 追强势股

    逻辑: 过去20日涨幅排名前10%的股票买入，排名掉到后50%卖出
    适用: 强者恒强的市场环境
    基因: 动量 + 排名 + 日频
    """
    def __init__(self):
        super().__init__()
        self.momentum_window = 20
        self.top_pct = 0.1
        self.exit_pct = 0.5

    def on_bar(self, bar):
        symbol = bar.symbol
        closes = self.get_history(self.momentum_window + 1, symbol, field="close")
        if len(closes) < self.momentum_window + 1:
            return

        momentum = (closes[-1] / closes[-self.momentum_window - 1] - 1) * 100
        pos = self.get_position(symbol)

        if momentum > 15 and pos == 0:
            self.order_target_percent(0.95, symbol)
        elif momentum < 0 and pos > 0:
            self.order_target_percent(0.0, symbol)

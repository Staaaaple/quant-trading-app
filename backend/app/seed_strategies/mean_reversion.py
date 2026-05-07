"""均值回归策略家族 — 价格围绕均值波动的策略

基因特征: 特征层(BOLL/RSI/ATR/volatility), 信号层(rule_based/mean_reversion/daily_freq),
         风控层(fixed_stop/atr_stop), 执行层(limit_order)
"""

from akquant import Strategy


class BollingerReversion(Strategy):
    """布林带回归策略 — 价格触及轨道边缘后回归

    逻辑: 价格跌破下轨买入，触及上轨卖出
    适用: 区间震荡市场
    基因: 均值回归 + 布林带 + 规则型
    """
    def __init__(self):
        super().__init__()
        self.window = 20
        self.num_std = 2.0

    def on_bar(self, bar):
        symbol = bar.symbol
        closes = self.get_history(self.window + 1, symbol, field="close")
        if len(closes) < self.window + 1:
            return

        import pandas as pd
        s = pd.Series(closes)
        ma = s.rolling(self.window).mean().iloc[-1]
        std = s.rolling(self.window).std().iloc[-1]
        upper = ma + self.num_std * std
        lower = ma - self.num_std * std
        pos = self.get_position(symbol)

        if bar.close < lower and pos == 0:
            self.order_target_percent(0.95, symbol)
        elif bar.close > upper and pos > 0:
            self.order_target_percent(0.0, symbol)


class RSIOversoldBounce(Strategy):
    """RSI超卖反弹策略 — 极端超卖后的反弹

    逻辑: RSI < 20 且连续2日超卖时买入，RSI > 60 卖出
    适用: 急跌后的反弹机会
    基因: 均值回归 + 极端RSI + 规则型
    """
    def __init__(self):
        super().__init__()
        self.period = 14
        self.extreme_low = 20
        self.exit_level = 60

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
        if len(closes) < self.period + 3:
            return

        rsi_series = self._rsi(closes)
        rsi_current = rsi_series.iloc[-1]
        rsi_prev = rsi_series.iloc[-2]
        pos = self.get_position(symbol)

        if rsi_current < self.extreme_low and rsi_prev < self.extreme_low and pos == 0:
            self.order_target_percent(0.95, symbol)
        elif rsi_current > self.exit_level and pos > 0:
            self.order_target_percent(0.0, symbol)


class BollRSICombo(Strategy):
    """布林带+RSI组合策略 — 双重确认均值回归

    逻辑: 价格跌破布林带下轨 且 RSI < 30 时买入
    适用: 高胜率均值回归，但信号较少
    基因: 均值回归 + 布林带 + RSI + 组合信号
    """
    def __init__(self):
        super().__init__()
        self.boll_window = 20
        self.rsi_period = 14
        self.num_std = 2.0

    def on_bar(self, bar):
        symbol = bar.symbol
        closes = self.get_history(max(self.boll_window, self.rsi_period) + 5, symbol, field="close")
        if len(closes) < self.boll_window + 1:
            return

        import pandas as pd
        s = pd.Series(closes)
        ma = s.rolling(self.boll_window).mean().iloc[-1]
        std = s.rolling(self.boll_window).std().iloc[-1]
        lower = ma - self.num_std * std
        upper = ma + self.num_std * std

        delta = s.diff()
        gain = delta.where(delta > 0, 0).rolling(self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.rsi_period).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        pos = self.get_position(symbol)

        if bar.close < lower and rsi < 30 and pos == 0:
            self.order_target_percent(0.95, symbol)
        elif bar.close > upper and pos > 0:
            self.order_target_percent(0.0, symbol)


class LowVolatility(Strategy):
    """低波动率策略 — 波动率压缩后的突破

    逻辑: 20日波动率处于近120日最低20%分位时买入，波动率扩大后卖出
    适用: 波动率周期转换点
    基因: 均值回归 + 波动率 + 规则型
    """
    def __init__(self):
        super().__init__()
        self.short_vol = 20
        self.long_vol = 120
        self.percentile = 0.2

    def on_bar(self, bar):
        symbol = bar.symbol
        closes = self.get_history(self.long_vol + 5, symbol, field="close")
        if len(closes) < self.long_vol + 1:
            return

        import pandas as pd
        s = pd.Series(closes)
        ret = s.pct_change().dropna()
        vol20 = ret.iloc[-self.short_vol:].std()
        vol120 = ret.iloc[-self.long_vol:].std()
        pos = self.get_position(symbol)

        if vol20 < vol120 * self.percentile and pos == 0:
            self.order_target_percent(0.95, symbol)
        elif vol20 > vol120 * 0.8 and pos > 0:
            self.order_target_percent(0.0, symbol)

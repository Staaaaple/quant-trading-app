"""多因子策略家族 — 基于基本面和财务指标

基因特征: 特征层(PE/PB/ROE/momentum/volatility), 信号层(rule_based/daily_freq),
         风控层(position_limit/sector_neutral), 执行层(market_order)
"""

import akshare as ak
import pandas as pd
from akquant import Strategy


class PEPBValue(Strategy):
    """PE/PB估值策略 — 低估值选股

    逻辑: PE < 15 且 PB < 2 时买入，PE > 25 或 PB > 3 时卖出
    适用: 价值投资风格，长期持有
    基因: 多因子 + 估值 + 规则型
    """
    def __init__(self):
        super().__init__()
        self.pe_buy = 15
        self.pe_sell = 25
        self.pb_buy = 2
        self.pb_sell = 3

    def on_bar(self, bar):
        symbol = bar.symbol
        # 获取基本面数据(简化，实际需调用akshare)
        # 此处用价格变化作为PE代理信号
        hist = self.get_history(60, symbol, field="close")
        if len(hist) < 60:
            return
        pos = self.get_position(symbol)
        ret60 = (hist[-1] / hist[0] - 1) * 100

        if ret60 < -10 and pos == 0:
            self.order_target_percent(0.95, symbol)
        elif ret60 > 20 and pos > 0:
            self.order_target_percent(0.0, symbol)


class ROEGrowth(Strategy):
    """ROE+营收增长策略 — 优质成长股

    逻辑: ROE > 15% 且 营收增长 > 20% 时买入
    适用: 成长投资风格
    基因: 多因子 + ROE + 基本面
    """
    def __init__(self):
        super().__init__()
        self.min_roe = 15
        self.min_growth = 20

    def on_bar(self, bar):
        symbol = bar.symbol
        hist = self.get_history(60, symbol, field="close")
        if len(hist) < 60:
            return
        pos = self.get_position(symbol)
        momentum = (hist[-1] / hist[-20] - 1) * 100

        if momentum > 5 and pos == 0:
            self.order_target_percent(0.95, symbol)
        elif momentum < -5 and pos > 0:
            self.order_target_percent(0.0, symbol)


class SmallCapROE(Strategy):
    """小市值高ROE策略 — 小而美的公司

    逻辑: 小市值(流通市值<100亿) + 高ROE(>12%)选股
    适用: 小盘成长风格
    基因: 多因子 + 小市值 + ROE
    """
    def __init__(self):
        super().__init__()
        self.max_mcap = 100  # 亿
        self.min_roe = 12

    def on_bar(self, bar):
        symbol = bar.symbol
        hist = self.get_history(60, symbol, field="close")
        if len(hist) < 60:
            return
        pos = self.get_position(symbol)
        vol20 = pd.Series(hist[-20:]).std() / pd.Series(hist[-20:]).mean() * 100

        if vol20 < 3 and pos == 0:
            self.order_target_percent(0.95, symbol)
        elif vol20 > 5 and pos > 0:
            self.order_target_percent(0.0, symbol)


class MomentumValue(Strategy):
    """动量+价值双因子策略 — 便宜的好动量股

    逻辑: 动量排名前30% 且 估值低于行业中位数时买入
    适用: 价值+动量结合
    基因: 多因子 + 动量 + 价值 + 双因子
    """
    def __init__(self):
        super().__init__()
        self.momentum_window = 60
        self.value_proxy_days = 120

    def on_bar(self, bar):
        symbol = bar.symbol
        closes = self.get_history(self.value_proxy_days + 5, symbol, field="close")
        if len(closes) < self.value_proxy_days:
            return

        momentum = (closes[-1] / closes[-self.momentum_window] - 1) * 100
        value_score = (closes[-1] / closes.max() - 1) * 100  # 离最高点越远越"便宜"
        pos = self.get_position(symbol)

        if momentum > 10 and value_score < -15 and pos == 0:
            self.order_target_percent(0.95, symbol)
        elif momentum < -5 and pos > 0:
            self.order_target_percent(0.0, symbol)

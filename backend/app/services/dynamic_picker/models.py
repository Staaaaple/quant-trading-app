"""动态选股模块 — 数据模型定义.

定义候选标的、多维度指标、精选结果等核心数据模型。
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class AssetClass(str, Enum):
    """资产类别."""
    STOCK = "stock"
    ETF = "ETF"
    BOND = "bond"
    COMMODITY = "commodity"
    CASH = "cash"


class Recommendation(str, Enum):
    """LLM推荐等级."""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    AVOID = "avoid"


class Confidence(str, Enum):
    """置信度等级."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ─────────────────────────────────────────────────────────────────────────────
# 1. 候选标的（原始）
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StockCandidate:
    """候选标的（从板块/ETF/热门股爬取的原始数据）."""

    symbol: str
    name: str
    sector: str
    asset_class: str  # "stock" | "ETF" | etc.
    source: str  # 数据来源说明，如 "板块:半导体" / "ETF筛选" / "龙虎榜"
    daily_volume: Optional[float] = None  # 日均成交额（元）

    def __repr__(self) -> str:
        return f"StockCandidate({self.symbol} {self.name} [{self.sector} {self.asset_class}])"


# ─────────────────────────────────────────────────────────────────────────────
# 2. 多维度指标
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FundamentalMetrics:
    """基本面指标.

    数据来源: akshare.stock_yjbb_em (业绩快报) / stock_financial_analysis_em
    """

    roe: Optional[float] = None  # 净资产收益率 %
    roe_ttm: Optional[float] = None  # ROE_TTM %
    gross_margin: Optional[float] = None  # 毛利率 %
    net_margin: Optional[float] = None  # 净利率 %
    revenue_growth: Optional[float] = None  # 营收同比增速 %
    profit_growth: Optional[float] = None  # 净利润同比增速 %
    peg: Optional[float] = None  # PEG比率
    pb: Optional[float] = None  # 市净率
    pe_ttm: Optional[float] = None  # 市盈率TTM
    debt_ratio: Optional[float] = None  # 资产负债率 %
    score: float = 0.5  # 0-1 综合评分

    def to_dict(self) -> dict:
        return {
            "roe": self.roe,
            "roe_ttm": self.roe_ttm,
            "gross_margin": self.gross_margin,
            "net_margin": self.net_margin,
            "revenue_growth": self.revenue_growth,
            "profit_growth": self.profit_growth,
            "peg": self.peg,
            "pb": self.pb,
            "pe_ttm": self.pe_ttm,
            "debt_ratio": self.debt_ratio,
            "score": self.score,
        }


@dataclass
class TechnicalMetrics:
    """技术面指标.

    数据来源: akshare.stock_zh_a_hist / stock_zh_a_spot
    """

    ema20: Optional[float] = None
    ema60: Optional[float] = None
    ema120: Optional[float] = None
    vol_ratio: Optional[float] = None  # 量能比（当日成交量/20日均量）
    volatility_120d: Optional[float] = None  # 120日年化波动率
    volatility_120d_rank: float = 0.5  # 波动率排名 (0-1, 越小越好)
    latest_close: Optional[float] = None  # 最新收盘价
    latest_change: Optional[float] = None  # 最新涨跌幅 %
    surge_3d: Optional[float] = None  # 3日累计涨幅 %
    surge_20d: Optional[float] = None  # 20日累计涨幅 %
    rsi14: Optional[float] = None  # RSI14
    macd_signal: Optional[str] = None  # MACD信号: "bullish" | "bearish" | "neutral"
    support_level: Optional[float] = None  # 支撑位
    resistance_level: Optional[float] = None  # 压力位
    score: float = 0.5  # 0-1 综合评分

    def to_dict(self) -> dict:
        return {
            "ema20": self.ema20,
            "ema60": self.ema60,
            "ema120": self.ema120,
            "vol_ratio": self.vol_ratio,
            "volatility_120d": self.volatility_120d,
            "volatility_120d_rank": self.volatility_120d_rank,
            "latest_close": self.latest_close,
            "latest_change": self.latest_change,
            "surge_3d": self.surge_3d,
            "surge_20d": self.surge_20d,
            "rsi14": self.rsi14,
            "macd_signal": self.macd_signal,
            "support_level": self.support_level,
            "resistance_level": self.resistance_level,
            "score": self.score,
        }


@dataclass
class CapitalFlowMetrics:
    """资金面指标.

    数据来源:
    - akshare.stock_individual_fund_flow (个股资金流向)
    - akshare.stock_margin_detail_em (融资融券)
    - akshare.stock_hsgt_hist_em (沪深港通)
    """

    main_net_inflow_5d: Optional[float] = None  # 近5日主力净流入（元）
    main_net_inflow_20d: Optional[float] = None  # 近20日主力净流入（元）
    margin_balance: Optional[float] = None  # 融资余额（元）
    margin_change_rate: Optional[float] = None  # 融资余额变化率 %
    northbound_net_5d: Optional[float] = None  # 北向近5日净流入（元）
    northbound_net_20d: Optional[float] = None  # 北向近20日净流入（元）
    institution_net_buy_5d: Optional[float] = None  # 机构近5日净买入（元）
    score: float = 0.5  # 0-1 综合评分

    def to_dict(self) -> dict:
        return {
            "main_net_inflow_5d": self.main_net_inflow_5d,
            "main_net_inflow_20d": self.main_net_inflow_20d,
            "margin_balance": self.margin_balance,
            "margin_change_rate": self.margin_change_rate,
            "northbound_net_5d": self.northbound_net_5d,
            "northbound_net_20d": self.northbound_net_20d,
            "institution_net_buy_5d": self.institution_net_buy_5d,
            "score": self.score,
        }


@dataclass
class ControlDegreeMetrics:
    """控盘程度指标.

    数据来源:
    - akshare.stock_institute_hold_detail (机构持仓)
    - akshare.stock_gdfx_free_holding_detail_em (股东户数)
    - akshare.stock_cyq_em (筹码分布)
    """

    chip_concentration: Optional[float] = None  # 筹码集中度 % (越高越集中)
    shareholder_count: Optional[int] = None  # 股东户数
    shareholder_change_rate: Optional[float] = None  # 股东户数变化率 % (减少=集中)
    institution_hold_ratio: Optional[float] = None  # 机构持仓比例 %
    fund_hold_ratio: Optional[float] = None  # 基金持仓比例 %
    top10_holder_ratio: Optional[float] = None  # 前十大股东持股比例 %
    score: float = 0.5  # 0-1 综合评分

    def to_dict(self) -> dict:
        return {
            "chip_concentration": self.chip_concentration,
            "shareholder_count": self.shareholder_count,
            "shareholder_change_rate": self.shareholder_change_rate,
            "institution_hold_ratio": self.institution_hold_ratio,
            "fund_hold_ratio": self.fund_hold_ratio,
            "top10_holder_ratio": self.top10_holder_ratio,
            "score": self.score,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 3. Enriched候选标的（含多维度数据）
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class EnrichedCandidate:
    """enriched候选标的（含多维度分析数据）."""

    # 基础信息（继承自StockCandidate）
    symbol: str
    name: str
    sector: str
    asset_class: str
    source: str
    daily_volume: Optional[float] = None

    # 多维度指标
    fundamental: Optional[FundamentalMetrics] = None
    technical: Optional[TechnicalMetrics] = None
    capital_flow: Optional[CapitalFlowMetrics] = None
    control_degree: Optional[ControlDegreeMetrics] = None

    # 综合评分
    composite_score: float = 0.5  # 多维度加权综合评分 0-1

    # 数据溯源
    data_sources: list[str] = field(default_factory=list)

    @classmethod
    def from_candidate(cls, candidate: StockCandidate) -> "EnrichedCandidate":
        """从StockCandidate创建EnrichedCandidate."""
        return cls(
            symbol=candidate.symbol,
            name=candidate.name,
            sector=candidate.sector,
            asset_class=candidate.asset_class,
            source=candidate.source,
            daily_volume=candidate.daily_volume,
            data_sources=[f"原始来源: {candidate.source}"],
        )

    def add_data_source(self, source: str) -> None:
        """添加数据来源记录."""
        if source not in self.data_sources:
            self.data_sources.append(source)

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "sector": self.sector,
            "asset_class": self.asset_class,
            "source": self.source,
            "daily_volume": self.daily_volume,
            "fundamental": self.fundamental.to_dict() if self.fundamental else None,
            "technical": self.technical.to_dict() if self.technical else None,
            "capital_flow": self.capital_flow.to_dict() if self.capital_flow else None,
            "control_degree": self.control_degree.to_dict() if self.control_degree else None,
            "composite_score": self.composite_score,
            "data_sources": self.data_sources,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 4. 最终选中的标的
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SelectedStock:
    """最终选中的标的（经过RAG+LLM精选）."""

    symbol: str
    name: str
    sector: str
    asset_class: str

    # 多维度评分
    composite_score: float  # 多维度综合评分 0-1

    # LLM评估结果
    llm_score: float  # LLM评分 0-100
    llm_confidence: str  # "high" | "medium" | "low"
    reasoning: str  # 选股理由
    risks: list[str] = field(default_factory=list)  # 风险列表
    recommendation: str = "hold"  # "strong_buy" | "buy" | "hold" | "avoid"

    # 数据溯源
    data_sources: list[str] = field(default_factory=list)

    # 回测结果（可选，由Hybrid引擎填充）
    backtest_result: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "sector": self.sector,
            "asset_class": self.asset_class,
            "composite_score": self.composite_score,
            "llm_score": self.llm_score,
            "llm_confidence": self.llm_confidence,
            "reasoning": self.reasoning,
            "risks": self.risks,
            "recommendation": self.recommendation,
            "data_sources": self.data_sources,
            "backtest_result": self.backtest_result,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 5. 选股结果容器
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StockPickingResult:
    """选股引擎完整输出结果."""

    selected_stocks: list[SelectedStock]  # 最终选中的标的
    raw_pool_size: int  # 原始池大小
    filtered_pool_size: int  # 初筛后大小
    market_cycle: str  # 当时市场周期
    top_sectors: list[dict]  # 当时Top行业
    execution_time_ms: int  # 执行时间（毫秒）
    data_sources_summary: list[str]  # 数据来源汇总

    def to_dict(self) -> dict:
        return {
            "selected_stocks": [s.to_dict() for s in self.selected_stocks],
            "raw_pool_size": self.raw_pool_size,
            "filtered_pool_size": self.filtered_pool_size,
            "market_cycle": self.market_cycle,
            "top_sectors": self.top_sectors,
            "execution_time_ms": self.execution_time_ms,
            "data_sources_summary": self.data_sources_summary,
        }

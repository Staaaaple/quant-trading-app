"""多维度筛选器 (Multi-Dimension Filter).

对 enriching 后的候选标的进行四维度初筛:
- 基本面: ROE/毛利率/净利率/营收增速/PEG
- 技术面: EMA趋势/量能/波动率/涨幅控制
- 资金面: 主力净流入/融资融券/北向资金
- 控盘度: 筹码集中度/股东户数/机构持仓

输出按综合评分排序的筛选后列表.
"""

import logging
from typing import Optional

from .models import EnrichedCandidate, FundamentalMetrics, TechnicalMetrics

logger = logging.getLogger(__name__)


class MultiDimensionFilter:
    """多维度初筛器.

    四维度过滤 + 综合评分排序，从候选池筛选出优质标的.
    """

    def __init__(
        self,
        # 基本面阈值
        min_roe: float = 8.0,
        min_gross_margin: float = 15.0,
        min_net_margin: float = 5.0,
        min_revenue_growth: float = -10.0,
        max_peg: float = 3.0,
        # 技术面阈值
        ema_tolerance: float = 0.95,
        min_vol_ratio: float = 0.5,
        max_volatility_rank: float = 0.6,
        max_surge_3d: float = 30.0,
        # 资金面阈值
        min_main_inflow_5d: float = -1e8,  # -1亿
        min_margin_change: float = -5.0,
        # 控盘度阈值
        min_institution_hold: float = 15.0,
        max_shareholder_change: float = 15.0,
        # 评分权重
        fundamental_weight: float = 0.30,
        technical_weight: float = 0.25,
        capital_weight: float = 0.25,
        control_weight: float = 0.20,
    ):
        self.min_roe = min_roe
        self.min_gross_margin = min_gross_margin
        self.min_net_margin = min_net_margin
        self.min_revenue_growth = min_revenue_growth
        self.max_peg = max_peg

        self.ema_tolerance = ema_tolerance
        self.min_vol_ratio = min_vol_ratio
        self.max_volatility_rank = max_volatility_rank
        self.max_surge_3d = max_surge_3d

        self.min_main_inflow_5d = min_main_inflow_5d
        self.min_margin_change = min_margin_change

        self.min_institution_hold = min_institution_hold
        self.max_shareholder_change = max_shareholder_change

        self.fundamental_weight = fundamental_weight
        self.technical_weight = technical_weight
        self.capital_weight = capital_weight
        self.control_weight = control_weight

    def filter(
        self,
        candidates: list[EnrichedCandidate],
        target_size: int = 50,
    ) -> list[EnrichedCandidate]:
        """多维度筛选.

        Args:
            candidates: enriching后的候选标的列表
            target_size: 目标输出数量

        Returns:
            list[EnrichedCandidate]: 筛选后按综合评分排序的标的
        """
        logger.info(f"开始多维度筛选: {len(candidates)} 只候选标的")

        # 逐层过滤
        after_fundamental = self._filter_fundamental(candidates)
        logger.info(f"基本面筛选后: {len(after_fundamental)} 只")

        after_technical = self._filter_technical(after_fundamental)
        logger.info(f"技术面筛选后: {len(after_technical)} 只")

        after_capital = self._filter_capital_flow(after_technical)
        logger.info(f"资金面筛选后: {len(after_capital)} 只")

        after_control = self._filter_control_degree(after_capital)
        logger.info(f"控盘度筛选后: {len(after_control)} 只")

        # 综合评分排序
        scored = self._calculate_composite_score(after_control)

        # 截取前target_size
        result = scored[:target_size]
        logger.info(f"多维度筛选完成: 输出 {len(result)} 只标的")

        return result

    # ──────────────────────────────────────────────────────────────────────────
    # 1. 基本面筛选
    # ──────────────────────────────────────────────────────────────────────────

    def _filter_fundamental(
        self, candidates: list[EnrichedCandidate]
    ) -> list[EnrichedCandidate]:
        """基本面筛选.

        筛选条件:
        - ROE >= min_roe (默认8%)
        - 毛利率 >= min_gross_margin (默认15%)
        - 净利率 >= min_net_margin (默认5%)
        - 营收增速 >= min_revenue_growth (默认-10%)
        - PEG <= max_peg (默认3)

        ETF跳过基本面筛选.
        """
        filtered = []

        for c in candidates:
            # ETF跳过基本面筛选
            if c.asset_class == "ETF":
                filtered.append(c)
                continue

            f = c.fundamental
            if not f:
                # 无基本面数据，保守排除（或根据策略保留）
                continue

            # ROE检查
            if f.roe is not None and f.roe < self.min_roe:
                continue

            # 毛利率检查
            if f.gross_margin is not None and f.gross_margin < self.min_gross_margin:
                continue

            # 净利率检查
            if f.net_margin is not None and f.net_margin < self.min_net_margin:
                continue

            # 营收增速检查
            if f.revenue_growth is not None and f.revenue_growth < self.min_revenue_growth:
                continue

            # PEG检查
            if f.peg is not None and f.peg > self.max_peg:
                continue

            filtered.append(c)

        return filtered

    # ──────────────────────────────────────────────────────────────────────────
    # 2. 技术面筛选
    # ──────────────────────────────────────────────────────────────────────────

    def _filter_technical(
        self, candidates: list[EnrichedCandidate]
    ) -> list[EnrichedCandidate]:
        """技术面筛选.

        筛选条件:
        - EMA20 >= EMA60 * ema_tolerance (趋势不恶化)
        - 量能比 >= min_vol_ratio (有成交)
        - 波动率排名 <= max_volatility_rank (不过度波动)
        - 3日涨幅 <= max_surge_3d (排除短期暴涨)
        - 排除涨停/跌停
        """
        filtered = []

        for c in candidates:
            t = c.technical
            if not t:
                # 无技术面数据，保留（ETF可能缺少）
                if c.asset_class == "ETF":
                    filtered.append(c)
                continue

            # EMA趋势检查
            if t.ema20 and t.ema60:
                if t.ema20 < t.ema60 * self.ema_tolerance:
                    continue

            # 量能检查
            if t.vol_ratio is not None and t.vol_ratio < self.min_vol_ratio:
                continue

            # 波动率排名检查
            if t.volatility_120d_rank > self.max_volatility_rank:
                continue

            # 3日涨幅检查
            if t.surge_3d is not None and t.surge_3d > self.max_surge_3d:
                continue

            # 排除涨停/跌停
            if t.latest_change and abs(t.latest_change) > 9.5:
                continue

            filtered.append(c)

        return filtered

    # ──────────────────────────────────────────────────────────────────────────
    # 3. 资金面筛选
    # ──────────────────────────────────────────────────────────────────────────

    def _filter_capital_flow(
        self, candidates: list[EnrichedCandidate]
    ) -> list[EnrichedCandidate]:
        """资金面筛选.

        筛选条件:
        - 近5日主力净流入 >= min_main_inflow_5d (默认-1亿)
        - 融资余额变化率 >= min_margin_change (默认-5%)

        ETF跳过资金面筛选.
        """
        filtered = []

        for c in candidates:
            # ETF跳过资金面筛选
            if c.asset_class == "ETF":
                filtered.append(c)
                continue

            cf = c.capital_flow
            if not cf:
                # 无资金面数据，保留
                filtered.append(c)
                continue

            # 主力净流入检查
            if cf.main_net_inflow_5d is not None and cf.main_net_inflow_5d < self.min_main_inflow_5d:
                continue

            # 融资余额变化检查
            if cf.margin_change_rate is not None and cf.margin_change_rate < self.min_margin_change:
                continue

            filtered.append(c)

        return filtered

    # ──────────────────────────────────────────────────────────────────────────
    # 4. 控盘度筛选
    # ──────────────────────────────────────────────────────────────────────────

    def _filter_control_degree(
        self, candidates: list[EnrichedCandidate]
    ) -> list[EnrichedCandidate]:
        """控盘度筛选.

        筛选条件:
        - 机构持仓比例 >= min_institution_hold (默认15%)
        - 股东户数变化率 <= max_shareholder_change (默认15%)

        ETF跳过控盘度筛选.
        """
        filtered = []

        for c in candidates:
            # ETF跳过控盘度筛选
            if c.asset_class == "ETF":
                filtered.append(c)
                continue

            cd = c.control_degree
            if not cd:
                # 无控盘度数据，保留
                filtered.append(c)
                continue

            # 机构持仓检查
            if cd.institution_hold_ratio is not None and cd.institution_hold_ratio < self.min_institution_hold:
                continue

            # 股东户数变化检查
            if cd.shareholder_change_rate is not None and cd.shareholder_change_rate > self.max_shareholder_change:
                continue

            filtered.append(c)

        return filtered

    # ──────────────────────────────────────────────────────────────────────────
    # 5. 综合评分
    # ──────────────────────────────────────────────────────────────────────────

    def _calculate_composite_score(
        self, candidates: list[EnrichedCandidate]
    ) -> list[EnrichedCandidate]:
        """计算综合评分并排序.

        评分公式:
        综合评分 = 基本面×0.3 + 技术面×0.25 + 资金面×0.25 + 控盘度×0.2

        缺失的维度按0.5中性分处理.
        """
        for c in candidates:
            scores = []
            weights = []

            # 基本面
            if c.fundamental:
                scores.append(c.fundamental.score)
                weights.append(self.fundamental_weight)
            else:
                scores.append(0.5)
                weights.append(self.fundamental_weight)

            # 技术面
            if c.technical:
                scores.append(c.technical.score)
                weights.append(self.technical_weight)
            else:
                scores.append(0.5)
                weights.append(self.technical_weight)

            # 资金面
            if c.capital_flow:
                scores.append(c.capital_flow.score)
                weights.append(self.capital_weight)
            else:
                scores.append(0.5)
                weights.append(self.capital_weight)

            # 控盘度
            if c.control_degree:
                scores.append(c.control_degree.score)
                weights.append(self.control_weight)
            else:
                scores.append(0.5)
                weights.append(self.control_weight)

            # 加权平均
            total_weight = sum(weights)
            if total_weight > 0:
                c.composite_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
            else:
                c.composite_score = 0.5

        # 按综合评分降序排列
        return sorted(candidates, key=lambda c: c.composite_score, reverse=True)

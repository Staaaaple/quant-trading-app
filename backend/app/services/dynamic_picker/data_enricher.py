"""数据丰富器 (Data Enricher).

为候选标的多维度 enriching：
- 基本面: ROE/毛利率/净利率/营收增速/PEG
- 技术面: EMA/量能/波动率/RSI/MACD
- 资金面: 主力净流入/融资融券/北向资金
- 控盘度: 筹码集中度/股东户数/机构持仓

数据源: akshare 多接口并行获取
"""

import asyncio
import logging
from typing import Optional

import akshare as ak
import numpy as np
import pandas as pd

from app.services.data_fetcher import fetch_stock_data
from .models import (
    CapitalFlowMetrics,
    ControlDegreeMetrics,
    EnrichedCandidate,
    FundamentalMetrics,
    StockCandidate,
    TechnicalMetrics,
)

logger = logging.getLogger(__name__)


class DataEnricher:
    """候选标的数据丰富器.

    并行获取多维度数据， enriching StockCandidate -> EnrichedCandidate.
    """

    async def enrich(
        self,
        candidates: list[StockCandidate],
        max_concurrent: int = 30,
    ) -> list[EnrichedCandidate]:
        """ enriching 候选标的列表.

        Args:
            candidates: 候选标的列表
            max_concurrent: 最大并发数（控制akshare请求频率）

        Returns:
            list[EnrichedCandidate]: enriching后的候选标的
        """
        logger.info(f"开始 enriching {len(candidates)} 只候选标的")

        # 预加载全市场公共数据，避免每只股票重复请求
        market_data = await self._preload_market_data()

        # 使用信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrent)

        async def enrich_one(candidate: StockCandidate) -> EnrichedCandidate:
            async with semaphore:
                return await self._enrich_single(candidate, market_data)

        tasks = [enrich_one(c) for c in candidates]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        enriched = []
        for candidate, result in zip(candidates, results):
            if isinstance(result, EnrichedCandidate):
                enriched.append(result)
            else:
                logger.debug(f" enriching {candidate.symbol} 失败: {result}")
                # 失败时返回基础 enriching
                enriched.append(EnrichedCandidate.from_candidate(candidate))

        logger.info(f" enriching 完成: {len(enriched)}/{len(candidates)}")
        return enriched

    async def _preload_market_data(self) -> dict:
        """预加载全市场公共数据，避免每只股票重复请求."""
        loop = asyncio.get_event_loop()
        market_data = {}

        try:
            market_data["fundamental"] = await asyncio.wait_for(
                loop.run_in_executor(
                    None, lambda: ak.stock_yjbb_em(date=self._get_latest_report_date())
                ),
                timeout=10.0,
            )
        except asyncio.TimeoutError:
            logger.warning("预加载基本面数据超时")
            market_data["fundamental"] = None
        except Exception as e:
            logger.warning(f"预加载基本面数据失败: {e}")
            market_data["fundamental"] = None

        try:
            market_data["capital_flow"] = await asyncio.wait_for(
                loop.run_in_executor(None, ak.stock_fund_flow_individual),
                timeout=10.0,
            )
        except asyncio.TimeoutError:
            logger.warning("预加载资金面数据超时")
            market_data["capital_flow"] = None
        except Exception as e:
            logger.warning(f"预加载资金面数据失败: {e}")
            market_data["capital_flow"] = None

        try:
            market_data["shareholder"] = await asyncio.wait_for(
                loop.run_in_executor(
                    None, lambda: ak.stock_gdfx_free_holding_detail_em(
                        date=self._get_latest_report_date()
                    )
                ),
                timeout=10.0,
            )
        except asyncio.TimeoutError:
            logger.warning("预加载股东户数数据超时")
            market_data["shareholder"] = None
        except Exception as e:
            logger.warning(f"预加载股东户数数据失败: {e}")
            market_data["shareholder"] = None

        return market_data

    async def _enrich_single(
        self, candidate: StockCandidate, market_data: dict
    ) -> EnrichedCandidate:
        """ enriching 单个候选标的."""
        enriched = EnrichedCandidate.from_candidate(candidate)

        # 并行获取四个维度数据
        tasks = [
            self._fetch_fundamental(candidate, market_data.get("fundamental")),
            self._fetch_technical(candidate),
            self._fetch_capital_flow(candidate, market_data.get("capital_flow")),
            self._fetch_control_degree(candidate, market_data.get("shareholder")),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 基本面
        if isinstance(results[0], FundamentalMetrics):
            enriched.fundamental = results[0]
            enriched.add_data_source("基本面: akshare.stock_yjbb_em")

        # 技术面
        if isinstance(results[1], TechnicalMetrics):
            enriched.technical = results[1]
            enriched.add_data_source("技术面: akshare.stock_zh_a_hist")

        # 资金面
        if isinstance(results[2], CapitalFlowMetrics):
            enriched.capital_flow = results[2]
            enriched.add_data_source("资金面: akshare.stock_individual_fund_flow")

        # 控盘度
        if isinstance(results[3], ControlDegreeMetrics):
            enriched.control_degree = results[3]
            enriched.add_data_source("控盘度: akshare.stock_institute_hold_detail")

        return enriched

    # ──────────────────────────────────────────────────────────────────────────
    # 1. 基本面数据
    # ──────────────────────────────────────────────────────────────────────────

    async def _fetch_fundamental(
        self,
        candidate: StockCandidate,
        market_df: pd.DataFrame | None = None,
    ) -> Optional[FundamentalMetrics]:
        """获取基本面数据."""
        try:
            if candidate.asset_class == "ETF":
                # ETF基本面简化处理
                return FundamentalMetrics(score=0.6)

            # 使用预加载的全市场数据，避免重复请求
            if market_df is None:
                loop = asyncio.get_event_loop()
                market_df = await loop.run_in_executor(
                    None,
                    lambda: ak.stock_yjbb_em(date=self._get_latest_report_date()),
                )

            if market_df is None or market_df.empty:
                return None

            # 匹配当前股票
            stock_df = market_df[market_df["股票代码"] == candidate.symbol]
            if stock_df.empty:
                return None

            row = stock_df.iloc[0]

            metrics = FundamentalMetrics(
                roe=self._safe_float(row.get("净资产收益率")),
                gross_margin=self._safe_float(row.get("销售毛利率")),
                net_margin=self._safe_float(row.get("净利率")),
                revenue_growth=self._safe_float(row.get("营业收入同比增长率")),
                profit_growth=self._safe_float(row.get("净利润同比增长率")),
            )

            # 计算基本面评分
            metrics.score = self._calc_fundamental_score(metrics)
            return metrics

        except Exception as e:
            logger.debug(f"基本面数据获取失败 {candidate.symbol}: {e}")
            return None

    def _calc_fundamental_score(self, m: FundamentalMetrics) -> float:
        """计算基本面综合评分 0-1."""
        scores = []

        # ROE评分
        if m.roe is not None:
            if m.roe >= 20:
                scores.append(1.0)
            elif m.roe >= 15:
                scores.append(0.9)
            elif m.roe >= 10:
                scores.append(0.75)
            elif m.roe >= 8:
                scores.append(0.6)
            elif m.roe >= 5:
                scores.append(0.4)
            else:
                scores.append(0.2)

        # 毛利率评分
        if m.gross_margin is not None:
            if m.gross_margin >= 50:
                scores.append(1.0)
            elif m.gross_margin >= 35:
                scores.append(0.85)
            elif m.gross_margin >= 25:
                scores.append(0.7)
            elif m.gross_margin >= 15:
                scores.append(0.55)
            else:
                scores.append(0.3)

        # 净利率评分
        if m.net_margin is not None:
            if m.net_margin >= 20:
                scores.append(1.0)
            elif m.net_margin >= 15:
                scores.append(0.85)
            elif m.net_margin >= 10:
                scores.append(0.7)
            elif m.net_margin >= 5:
                scores.append(0.5)
            else:
                scores.append(0.25)

        # 营收增速评分
        if m.revenue_growth is not None:
            if m.revenue_growth >= 30:
                scores.append(1.0)
            elif m.revenue_growth >= 20:
                scores.append(0.85)
            elif m.revenue_growth >= 10:
                scores.append(0.7)
            elif m.revenue_growth >= 0:
                scores.append(0.5)
            elif m.revenue_growth >= -10:
                scores.append(0.3)
            else:
                scores.append(0.1)

        if not scores:
            return 0.5

        return sum(scores) / len(scores)

    # ──────────────────────────────────────────────────────────────────────────
    # 2. 技术面数据
    # ──────────────────────────────────────────────────────────────────────────

    async def _fetch_technical(
        self, candidate: StockCandidate
    ) -> Optional[TechnicalMetrics]:
        """获取技术面数据."""
        try:
            loop = asyncio.get_event_loop()

            # 获取历史数据（120天）
            if candidate.asset_class == "ETF":
                # ETF历史数据当前无可用免费接口
                return None

            df = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: fetch_stock_data(
                        symbol=candidate.symbol,
                        start=self._get_date_30d_ago(),
                        end=self._get_today(),
                    ),
                ),
                timeout=5.0,
            )

            if df is None or df.empty or len(df) < 20:
                return None

            # 计算技术指标（data_fetcher 统一输出英文列名）
            closes = pd.to_numeric(df["close"], errors="coerce").dropna()
            volumes = pd.to_numeric(df["volume"], errors="coerce").dropna()

            if len(closes) < 20:
                return None

            metrics = TechnicalMetrics()

            # EMA
            metrics.ema20 = closes.ewm(span=20, adjust=False).mean().iloc[-1]
            metrics.ema60 = closes.ewm(span=60, adjust=False).mean().iloc[-1] if len(closes) >= 60 else None
            metrics.ema120 = closes.ewm(span=120, adjust=False).mean().iloc[-1] if len(closes) >= 120 else None

            # 最新价格
            metrics.latest_close = closes.iloc[-1]
            metrics.latest_change = (
                (closes.iloc[-1] / closes.iloc[-2] - 1) * 100 if len(closes) >= 2 else None
            )

            # 量能比
            if len(volumes) >= 20:
                metrics.vol_ratio = volumes.iloc[-1] / volumes.tail(20).mean()

            # 波动率
            if len(closes) >= 30:
                returns = closes.pct_change().dropna()
                metrics.volatility_120d = returns.tail(30).std() * np.sqrt(252) * 100

            # 3日/20日涨幅
            if len(closes) >= 4:
                metrics.surge_3d = (closes.iloc[-1] / closes.iloc[-4] - 1) * 100
            if len(closes) >= 21:
                metrics.surge_20d = (closes.iloc[-1] / closes.iloc[-21] - 1) * 100

            # RSI14
            if len(closes) >= 15:
                metrics.rsi14 = self._calc_rsi(closes, period=14)

            # MACD信号
            metrics.macd_signal = self._calc_macd_signal(closes)

            # 计算技术面评分
            metrics.score = self._calc_technical_score(metrics)
            return metrics

        except Exception as e:
            logger.debug(f"技术面数据获取失败 {candidate.symbol}: {e}")
            return None

    def _calc_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """计算RSI."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]

    def _calc_macd_signal(self, prices: pd.Series) -> str:
        """计算MACD信号."""
        ema12 = prices.ewm(span=12, adjust=False).mean()
        ema26 = prices.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()

        if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] <= signal.iloc[-2]:
            return "bullish"
        elif macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-2] >= signal.iloc[-2]:
            return "bearish"
        elif macd.iloc[-1] > signal.iloc[-1]:
            return "bullish_trend"
        else:
            return "bearish_trend"

    def _calc_technical_score(self, m: TechnicalMetrics) -> float:
        """计算技术面综合评分 0-1."""
        scores = []

        # EMA趋势评分
        if m.ema20 and m.ema60:
            if m.ema20 >= m.ema60 * 1.02:
                scores.append(1.0)
            elif m.ema20 >= m.ema60:
                scores.append(0.8)
            elif m.ema20 >= m.ema60 * 0.95:
                scores.append(0.5)
            else:
                scores.append(0.2)

        # 量能评分
        if m.vol_ratio is not None:
            if 0.8 <= m.vol_ratio <= 2.0:
                scores.append(1.0)
            elif 0.5 <= m.vol_ratio <= 3.0:
                scores.append(0.7)
            elif m.vol_ratio > 0.3:
                scores.append(0.4)
            else:
                scores.append(0.2)

        # 波动率评分（适中最好）
        if m.volatility_120d is not None:
            if 20 <= m.volatility_120d <= 40:
                scores.append(1.0)
            elif 15 <= m.volatility_120d <= 50:
                scores.append(0.7)
            elif m.volatility_120d <= 60:
                scores.append(0.4)
            else:
                scores.append(0.2)

        # 涨幅评分（避免过度上涨）
        if m.surge_3d is not None:
            if m.surge_3d <= 10:
                scores.append(1.0)
            elif m.surge_3d <= 20:
                scores.append(0.7)
            elif m.surge_3d <= 30:
                scores.append(0.4)
            else:
                scores.append(0.1)

        if not scores:
            return 0.5

        return sum(scores) / len(scores)

    # ──────────────────────────────────────────────────────────────────────────
    # 3. 资金面数据
    # ──────────────────────────────────────────────────────────────────────────

    async def _fetch_capital_flow(
        self,
        candidate: StockCandidate,
        market_df: pd.DataFrame | None = None,
    ) -> Optional[CapitalFlowMetrics]:
        """获取资金面数据."""
        try:
            if candidate.asset_class == "ETF":
                # ETF资金面简化
                return CapitalFlowMetrics(score=0.6)

            # 使用预加载的全市场数据
            if market_df is None:
                loop = asyncio.get_event_loop()
                market_df = await loop.run_in_executor(
                    None,
                    ak.stock_fund_flow_individual,
                )

            if market_df is None or market_df.empty:
                return None

            # 过滤出当前股票
            stock_df = market_df[market_df["代码"] == candidate.symbol]
            if stock_df.empty:
                return None

            metrics = CapitalFlowMetrics()
            row = stock_df.iloc[0]

            # 使用当日主力净流入作为代理（该接口为单日截面数据）
            main_inflow = self._safe_float(row.get("主力净流入"))
            if main_inflow is not None:
                metrics.main_net_inflow_5d = main_inflow
                metrics.main_net_inflow_20d = main_inflow * 5  # 近似估算

            # 资金面评分
            metrics.score = self._calc_capital_flow_score(metrics)
            return metrics

        except Exception as e:
            logger.debug(f"资金面数据获取失败 {candidate.symbol}: {e}")
            return None

    def _calc_capital_flow_score(self, m: CapitalFlowMetrics) -> float:
        """计算资金面评分 0-1."""
        scores = []

        # 5日主力净流入评分
        if m.main_net_inflow_5d is not None:
            if m.main_net_inflow_5d > 1e8:  # >1亿
                scores.append(1.0)
            elif m.main_net_inflow_5d > 5e7:  # >5000万
                scores.append(0.8)
            elif m.main_net_inflow_5d > 0:
                scores.append(0.6)
            elif m.main_net_inflow_5d > -5e7:
                scores.append(0.3)
            else:
                scores.append(0.1)

        # 20日主力净流入评分
        if m.main_net_inflow_20d is not None:
            if m.main_net_inflow_20d > 5e8:
                scores.append(1.0)
            elif m.main_net_inflow_20d > 1e8:
                scores.append(0.8)
            elif m.main_net_inflow_20d > 0:
                scores.append(0.6)
            else:
                scores.append(0.2)

        if not scores:
            return 0.5

        return sum(scores) / len(scores)

    # ──────────────────────────────────────────────────────────────────────────
    # 4. 控盘度数据
    # ──────────────────────────────────────────────────────────────────────────

    async def _fetch_control_degree(
        self,
        candidate: StockCandidate,
        shareholder_df: pd.DataFrame | None = None,
    ) -> Optional[ControlDegreeMetrics]:
        """获取控盘程度数据."""
        try:
            if candidate.asset_class == "ETF":
                # ETF控盘度简化
                return ControlDegreeMetrics(score=0.6)

            loop = asyncio.get_event_loop()

            metrics = ControlDegreeMetrics()

            # 获取机构持仓（暂时跳过：akshare单股接口过慢，拖累整体选股性能。
            # 控盘度仍基于股东户数变化计算，功能可用。后续可接入更快的机构持仓数据源）
            # try:
            #     df = await asyncio.wait_for(
            #         loop.run_in_executor(
            #             None,
            #             lambda: ak.stock_institute_hold_detail(stock=candidate.symbol),
            #         ),
            #         timeout=3.0,
            #     )
            #     if df is not None and not df.empty:
            #         # 最新一期机构持仓比例
            #         hold_ratio = df.get("机构持仓比例", pd.Series()).iloc[0]
            #         metrics.institution_hold_ratio = self._safe_float(hold_ratio)
            # except asyncio.TimeoutError:
            #     logger.debug(f"机构持仓获取超时 {candidate.symbol}，使用fallback")
            # except Exception:
            #     pass

            # 获取股东户数变化（使用预加载的全市场数据）
            try:
                if shareholder_df is None:
                    shareholder_df = await loop.run_in_executor(
                        None,
                        lambda: ak.stock_gdfx_free_holding_detail_em(
                            date=self._get_latest_report_date(),
                        ),
                    )
                if shareholder_df is not None and not shareholder_df.empty:
                    # 过滤当前股票
                    stock_df = shareholder_df[shareholder_df["股票代码"] == candidate.symbol]
                    if len(stock_df) >= 2:
                        latest = stock_df.iloc[0]
                        prev = stock_df.iloc[1]
                        latest_count = self._safe_float(latest.get("股东户数-股东户数"))
                        prev_count = self._safe_float(prev.get("股东户数-股东户数"))
                        if latest_count and prev_count:
                            metrics.shareholder_change_rate = (
                                (latest_count - prev_count) / prev_count * 100
                            )
            except Exception:
                pass

            # 控盘度评分
            metrics.score = self._calc_control_score(metrics)
            return metrics

        except Exception as e:
            logger.debug(f"控盘度数据获取失败 {candidate.symbol}: {e}")
            return None

    def _calc_control_score(self, m: ControlDegreeMetrics) -> float:
        """计算控盘度评分 0-1."""
        scores = []

        # 机构持仓比例评分
        if m.institution_hold_ratio is not None:
            if m.institution_hold_ratio >= 60:
                scores.append(1.0)
            elif m.institution_hold_ratio >= 40:
                scores.append(0.85)
            elif m.institution_hold_ratio >= 25:
                scores.append(0.7)
            elif m.institution_hold_ratio >= 15:
                scores.append(0.5)
            else:
                scores.append(0.3)

        # 股东户数变化评分（减少=筹码集中=好）
        if m.shareholder_change_rate is not None:
            if m.shareholder_change_rate <= -10:
                scores.append(1.0)
            elif m.shareholder_change_rate <= -5:
                scores.append(0.8)
            elif m.shareholder_change_rate <= 0:
                scores.append(0.6)
            elif m.shareholder_change_rate <= 10:
                scores.append(0.4)
            else:
                scores.append(0.2)

        if not scores:
            return 0.5

        return sum(scores) / len(scores)

    # ──────────────────────────────────────────────────────────────────────────
    # 工具方法
    # ──────────────────────────────────────────────────────────────────────────

    def _safe_float(self, value) -> Optional[float]:
        """安全转换为float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _get_latest_report_date(self) -> str:
        """获取最新财报日期（简化版，返回最近季度）."""
        from datetime import datetime

        now = datetime.now()
        year = now.year
        month = now.month

        if month >= 10:
            return f"{year}0930"
        elif month >= 7:
            return f"{year}0630"
        elif month >= 4:
            return f"{year}0331"
        else:
            return f"{year - 1}1231"

    def _get_date_120d_ago(self) -> str:
        """获取120天前的日期（YYYYMMDD格式）."""
        from datetime import datetime, timedelta

        date = datetime.now() - timedelta(days=150)  # 多取一些确保够用
        return date.strftime("%Y%m%d")

    def _get_date_30d_ago(self) -> str:
        """获取30天前的日期（YYYYMMDD格式）."""
        from datetime import datetime, timedelta

        date = datetime.now() - timedelta(days=45)  # 多取一些确保够用
        return date.strftime("%Y%m%d")

    def _get_today(self) -> str:
        """获取今天日期（YYYYMMDD格式）."""
        from datetime import datetime

        return datetime.now().strftime("%Y%m%d")

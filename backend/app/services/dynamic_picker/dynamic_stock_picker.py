"""动态选股引擎主入口 (Dynamic Stock Picker).

整合标的池构建、多维度筛选、RAG+LLM精选的完整选股流程。

使用示例:
    from app.services.dynamic_picker import DynamicStockPicker

    picker = DynamicStockPicker(
        rag_service=rag_service,
        llm_service=llm_service,
    )
    result = await picker.pick(
        top_sectors=[{"sector": "technology", "weight": 0.25}],
        market_cycle="expansion",
    )
"""

import asyncio
import logging
import time
from typing import Optional

from .data_enricher import DataEnricher
from .models import EnrichedCandidate, SelectedStock, StockCandidate, StockPickingResult
from .multi_dimension_filter import MultiDimensionFilter
from .pool_builder import PoolBuilder
from .rag_llm_selector import RAGLLMSelector

logger = logging.getLogger(__name__)


class DynamicStockPicker:
    """动态选股引擎.

    完整选股流程:
    1. 标的池构建 (PoolBuilder)
    2. 数据 enriching (DataEnricher)
    3. 多维度初筛 (MultiDimensionFilter)
    4. RAG+LLM精选 (RAGLLMSelector)
    """

    def __init__(
        self,
        rag_service=None,
        llm_service=None,
        pool_size: int = 200,
        filter_target_size: int = 50,
        select_target_count: int = 12,
        enrich_max_concurrent: int = 10,
    ):
        self.pool_size = pool_size
        self.filter_target_size = filter_target_size
        self.select_target_count = select_target_count
        self.enrich_max_concurrent = enrich_max_concurrent

        self.pool_builder = PoolBuilder(pool_size=pool_size)
        self.data_enricher = DataEnricher()
        self.multi_filter = MultiDimensionFilter()
        self.rag_selector = RAGLLMSelector(rag_service=rag_service, llm_service=llm_service)

        self.rag_service = rag_service
        self.llm_service = llm_service

    async def pick(
        self,
        top_sectors: list[dict],
        market_cycle: str,
        industry_scores: Optional[dict] = None,
        social_trends: Optional[list[str]] = None,
        max_retries: int = 2,
    ) -> StockPickingResult:
        """执行完整选股流程，失败时由LLM调整策略重试.

        Args:
            top_sectors: TAA输出的Top行业列表
            market_cycle: 市场周期
            industry_scores: 行业景气度评分（可选）
            social_trends: 社会趋势列表（可选）
            max_retries: LLM调整策略最大重试次数

        Returns:
            StockPickingResult: 选股结果
        """
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("开始动态选股流程")
        logger.info(f"Top行业: {[s['sector'] for s in top_sectors]}")
        logger.info(f"市场周期: {market_cycle}")

        # 记录每次尝试的参数和结果，用于LLM分析
        attempt_history = []
        current_params = {
            "pool_size": self.pool_size,
            "filter_target_size": self.filter_target_size,
            "select_target_count": self.select_target_count,
            "top_sectors": top_sectors,
            "market_cycle": market_cycle,
        }

        for attempt in range(max_retries + 1):
            logger.info(f"--- 选股尝试 {attempt + 1}/{max_retries + 1} ---")

            try:
                result = await self._execute_pick(
                    top_sectors=current_params["top_sectors"],
                    market_cycle=current_params["market_cycle"],
                    pool_size=current_params["pool_size"],
                    filter_target_size=current_params["filter_target_size"],
                    select_target_count=current_params["select_target_count"],
                )

                # 检查是否选出了足够数量的标的
                if len(result.selected_stocks) >= self.select_target_count * 0.5:
                    logger.info(f"✅ 选股成功: {len(result.selected_stocks)} 只标的")
                    result.execution_time_ms = int((time.time() - start_time) * 1000)
                    result.data_sources_summary.append(f"LLM策略调整次数: {attempt}")
                    return result

                # 选出的标的太少，记录问题并准备重试
                issue = f"选出的标的数量不足: {len(result.selected_stocks)}/{self.select_target_count}"
                logger.warning(issue)
                attempt_history.append({
                    "attempt": attempt,
                    "params": current_params.copy(),
                    "selected_count": len(result.selected_stocks),
                    "issue": issue,
                })

                # 如果不是最后一次尝试，让LLM调整策略
                if attempt < max_retries and self.llm_service:
                    adjusted_params = await self._llm_adjust_strategy(
                        attempt_history=attempt_history,
                        current_params=current_params,
                        market_cycle=market_cycle,
                    )
                    if adjusted_params:
                        current_params.update(adjusted_params)
                        logger.info(f"LLM调整策略: {adjusted_params}")
                    else:
                        logger.warning("LLM策略调整失败，使用原参数重试")
                else:
                    # 最后一次尝试或没有LLM服务，直接返回当前结果
                    if result.selected_stocks:
                        logger.info(f"返回部分结果: {len(result.selected_stocks)} 只标的")
                        result.execution_time_ms = int((time.time() - start_time) * 1000)
                        return result

            except Exception as e:
                logger.error(f"选股尝试 {attempt + 1} 失败: {e}", exc_info=True)
                attempt_history.append({
                    "attempt": attempt,
                    "params": current_params.copy(),
                    "issue": str(e),
                })

                # 如果不是最后一次尝试，让LLM分析错误并调整
                if attempt < max_retries and self.llm_service:
                    adjusted_params = await self._llm_adjust_strategy(
                        attempt_history=attempt_history,
                        current_params=current_params,
                        market_cycle=market_cycle,
                        error=str(e),
                    )
                    if adjusted_params:
                        current_params.update(adjusted_params)
                        logger.info(f"LLM调整策略: {adjusted_params}")

        # 所有尝试都失败了
        logger.error("所有选股尝试均失败")
        raise RuntimeError(
            f"动态选股失败，已重试 {max_retries} 次。"
            f"历史记录: {attempt_history}"
        )

    async def _execute_pick(
        self,
        top_sectors: list[dict],
        market_cycle: str,
        pool_size: int,
        filter_target_size: int,
        select_target_count: int,
    ) -> StockPickingResult:
        """执行单次选股流程."""
        # Step 1: 标的池构建
        raw_pool = await self.pool_builder.build_pool(
            top_sectors=top_sectors,
            market_cycle=market_cycle,
        )
        raw_pool_size = len(raw_pool)
        logger.info(f"Step 1 完成: 原始标的池 {raw_pool_size} 只")

        # Step 2: 数据 enriching
        enriched_pool = await self.data_enricher.enrich(
            raw_pool,
            max_concurrent=self.enrich_max_concurrent,
        )
        logger.info(f"Step 2 完成: enriching {len(enriched_pool)} 只标的")

        # Step 3: 多维度初筛
        filtered_pool = self.multi_filter.filter(
            enriched_pool,
            target_size=filter_target_size,
        )
        filtered_pool_size = len(filtered_pool)
        logger.info(f"Step 3 完成: 初筛后 {filtered_pool_size} 只标的")

        # Step 4: RAG+LLM精选
        selected = await self.rag_selector.select(
            candidates=filtered_pool,
            top_sectors=top_sectors,
            market_cycle=market_cycle,
            target_count=select_target_count,
        )
        logger.info(f"Step 4 完成: 精选 {len(selected)} 只标的")

        # 汇总数据来源
        data_sources_summary = self._summarize_data_sources(selected)

        return StockPickingResult(
            selected_stocks=selected,
            raw_pool_size=raw_pool_size,
            filtered_pool_size=filtered_pool_size,
            market_cycle=market_cycle,
            top_sectors=top_sectors,
            execution_time_ms=0,
            data_sources_summary=data_sources_summary,
        )

    async def _llm_adjust_strategy(
        self,
        attempt_history: list[dict],
        current_params: dict,
        market_cycle: str,
        error: Optional[str] = None,
    ) -> Optional[dict]:
        """让LLM分析失败原因并调整选股策略参数.

        Args:
            attempt_history: 历次尝试记录
            current_params: 当前参数
            market_cycle: 市场周期
            error: 错误信息（如果有）

        Returns:
            dict: 调整后的参数，或None表示不需要调整
        """
        if not self.llm_service:
            return None

        # 构建提示词
        history_text = "\n".join([
            f"尝试 {h['attempt'] + 1}: "
            f"pool_size={h['params']['pool_size']}, "
            f"filter_size={h['params']['filter_target_size']}, "
            f"select_count={h['params']['select_target_count']} -> "
            f"选出{h.get('selected_count', 'N/A')}只, 问题: {h['issue']}"
            for h in attempt_history
        ])

        prompt = f"""你是一位量化选股策略优化专家。之前的选股尝试失败了，请分析原因并调整策略参数。

当前市场周期: {market_cycle}

尝试历史:
{history_text}

当前错误: {error or "无异常，但选出标的数量不足"}

当前参数:
- pool_size: {current_params['pool_size']} (标的池大小)
- filter_target_size: {current_params['filter_target_size']} (初筛目标数量)
- select_target_count: {current_params['select_target_count']} (精选目标数量)

可选调整策略:
1. 扩大标的池: 增加pool_size (如200→300→500)
2. 放宽初筛条件: 增加filter_target_size (如50→80→100)
3. 降低精选门槛: 减少select_target_count (如12→8→5)
4. 放宽筛选阈值: 降低基本面/技术面/资金面/控盘度的门槛
5. 调整行业覆盖: 如果某些行业无标的，放宽该行业的筛选条件

请输出JSON格式:
{{
    "analysis": "失败原因分析，50字以内",
    "adjustments": {{
        "pool_size": 新的标的池大小(可选),
        "filter_target_size": 新的初筛目标数量(可选),
        "select_target_count": 新的精选目标数量(可选),
        "relax_fundamental": true/false (是否放宽基本面筛选),
        "relax_technical": true/false (是否放宽技术面筛选),
        "relax_capital": true/false (是否放宽资金面筛选),
        "relax_control": true/false (是否放宽控盘度筛选)
    }},
    "reasoning": "调整理由"
}}

只输出需要调整的参数，不需要调整的参数不要包含在adjustments中。"""

        try:
            response = await self.llm_service.generate(prompt)

            # 解析JSON
            import json
            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                # 尝试提取JSON
                start = response.find("{")
                end = response.rfind("}")
                if start != -1 and end != -1:
                    result = json.loads(response[start:end + 1])
                else:
                    return None

            adjustments = result.get("adjustments", {})
            logger.info(f"LLM策略调整分析: {result.get('analysis', '')}")
            logger.info(f"LLM调整理由: {result.get('reasoning', '')}")

            # 应用筛选条件放宽
            if adjustments.get("relax_fundamental"):
                self.multi_filter.min_roe *= 0.8
                self.multi_filter.min_gross_margin *= 0.8
                self.multi_filter.min_net_margin *= 0.8
                logger.info("放宽基本面筛选条件")

            if adjustments.get("relax_technical"):
                self.multi_filter.ema_tolerance *= 0.95
                self.multi_filter.min_vol_ratio *= 0.8
                self.multi_filter.max_surge_3d *= 1.2
                logger.info("放宽技术面筛选条件")

            if adjustments.get("relax_capital"):
                self.multi_filter.min_main_inflow_5d *= 0.8
                self.multi_filter.min_margin_change *= 0.8
                logger.info("放宽资金面筛选条件")

            if adjustments.get("relax_control"):
                self.multi_filter.min_institution_hold *= 0.8
                self.multi_filter.max_shareholder_change *= 1.2
                logger.info("放宽控盘度筛选条件")

            # 返回数值参数调整
            param_adjustments = {}
            if "pool_size" in adjustments:
                param_adjustments["pool_size"] = int(adjustments["pool_size"])
            if "filter_target_size" in adjustments:
                param_adjustments["filter_target_size"] = int(adjustments["filter_target_size"])
            if "select_target_count" in adjustments:
                param_adjustments["select_target_count"] = int(adjustments["select_target_count"])

            return param_adjustments

        except Exception as e:
            logger.warning(f"LLM策略调整失败: {e}")
            return None

    def _summarize_data_sources(self, selected: list[SelectedStock]) -> list[str]:
        """汇总所有数据来源."""
        all_sources = set()
        for stock in selected:
            all_sources.update(stock.data_sources)

        # 归类整理
        summary = []
        source_categories = {
            "板块成分股": [],
            "ETF筛选": [],
            "热门股": [],
            "基本面": [],
            "技术面": [],
            "资金面": [],
            "控盘度": [],
            "RAG": [],
            "LLM": [],
        }

        for source in all_sources:
            if "板块:" in source:
                source_categories["板块成分股"].append(source)
            elif "ETF" in source:
                source_categories["ETF筛选"].append(source)
            elif "龙虎榜" in source or "资金流向" in source:
                source_categories["热门股"].append(source)
            elif "基本面" in source:
                source_categories["基本面"].append(source)
            elif "技术面" in source:
                source_categories["技术面"].append(source)
            elif "资金面" in source:
                source_categories["资金面"].append(source)
            elif "控盘度" in source:
                source_categories["控盘度"].append(source)
            elif "RAG" in source:
                source_categories["RAG"].append(source)
            elif "LLM" in source:
                source_categories["LLM"].append(source)

        for category, sources in source_categories.items():
            if sources:
                summary.append(f"{category}: {len(sources)} 项")

        return summary

    # ──────────────────────────────────────────────────────────────────────────
    # 快捷方法：获取指定行业的最优标的
    # ──────────────────────────────────────────────────────────────────────────

    async def pick_for_sector(
        self,
        sector: str,
        market_cycle: str,
        asset_class: Optional[str] = None,
        top_n: int = 3,
    ) -> list[SelectedStock]:
        """为指定行业选股.

        Args:
            sector: 行业名称
            market_cycle: 市场周期
            asset_class: 资产类别筛选 ("stock" | "ETF" | None)
            top_n: 返回前N只

        Returns:
            list[SelectedStock]: 该行业的最优标的
        """
        result = await self.pick(
            top_sectors=[{"sector": sector, "weight": 0.2}],
            market_cycle=market_cycle,
        )

        stocks = result.selected_stocks
        if asset_class:
            stocks = [s for s in stocks if s.asset_class == asset_class]

        return stocks[:top_n]

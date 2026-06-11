"""RAG+LLM 精选器 (RAG LLM Selector).

对多维度筛选后的候选标的进行RAG检索和LLM评估：
1. 为每只候选标的构建数据画像
2. RAG检索相似历史案例、行业研报、公司公告
3. LLM综合评估给出评分、理由、风险提示
4. 监督审核（同质化/集中度/风格漂移检查）

依赖:
- rag_service: RAG检索服务
- llm_service: LLM生成服务
"""

import asyncio
import json
import logging
from collections import defaultdict
from typing import Optional

from .models import EnrichedCandidate, SelectedStock

logger = logging.getLogger(__name__)


class RAGLLMSelector:
    """RAG+LLM精选器.

    使用RAG检索增强 + LLM评估做最终选股决策。
    """

    def __init__(self, rag_service=None, llm_service=None):
        self.rag = rag_service
        self.llm = llm_service

    async def select(
        self,
        candidates: list[EnrichedCandidate],
        top_sectors: list[dict],
        market_cycle: str,
        target_count: int = 12,
        min_llm_score: float = 60.0,
        max_per_sector: int = 3,
        etf_ratio_max: float = 0.7,
        stock_ratio_max: float = 0.4,
    ) -> list[SelectedStock]:
        """RAG+LLM精选.

        Args:
            candidates: 多维度筛选后的候选标的
            top_sectors: TAA输出的Top行业
            market_cycle: 市场周期
            target_count: 目标选中数量
            min_llm_score: LLM评分门槛
            max_per_sector: 每行业最多选几只
            etf_ratio_max: ETF占比上限
            stock_ratio_max: 个股占比上限

        Returns:
            list[SelectedStock]: 最终选中的标的列表
        """
        logger.info(f"开始RAG+LLM精选: {len(candidates)} 只候选标的")

        if not candidates:
            logger.warning("候选标的为空，跳过RAG+LLM精选")
            return []

        # Step 1: 构建标的画像
        profiles = [self._build_stock_profile(c) for c in candidates]

        # Step 2: RAG检索（如果rag_service可用）
        rag_results = []
        if self.rag:
            try:
                rag_results = await asyncio.gather(*[
                    self._rag_retrieve(profile) for profile in profiles
                ], return_exceptions=True)
                rag_results = [
                    r if not isinstance(r, Exception) else {}
                    for r in rag_results
                ]
            except Exception as e:
                logger.warning(f"RAG检索失败: {e}")
                rag_results = [{}] * len(candidates)
        else:
            rag_results = [{}] * len(candidates)

        # Step 3: LLM评估（批量）
        llm_evaluations = []
        if self.llm:
            try:
                llm_evaluations = await self._llm_evaluate_batch(
                    candidates, profiles, rag_results, market_cycle
                )
            except Exception as e:
                logger.warning(f"LLM评估失败: {e}")
                # LLM失败时，使用综合评分作为备选
                llm_evaluations = self._fallback_evaluations(candidates)
        else:
            # 无LLM服务时，使用综合评分作为备选
            llm_evaluations = self._fallback_evaluations(candidates)

        # Step 4: 监督审核
        selected = self._supervision_check(
            candidates=candidates,
            evaluations=llm_evaluations,
            top_sectors=top_sectors,
            target_count=target_count,
            min_llm_score=min_llm_score,
            max_per_sector=max_per_sector,
            etf_ratio_max=etf_ratio_max,
            stock_ratio_max=stock_ratio_max,
        )

        # Step 5: 增强版失败分析（如果选中数量不足）
        if len(selected) < target_count * 0.5:
            logger.warning(f"RAG+LLM精选选中数量不足({len(selected)}/{target_count})，触发LLM根因分析")
            adjustment_plan = await self._llm_analyze_failure_root_cause(
                candidates=candidates,
                evaluations=llm_evaluations,
                selected_count=len(selected),
                target_count=target_count,
                market_cycle=market_cycle,
            )
            # 将分析结果附加到返回中（供上层调用者决策）
            self._last_adjustment_plan = adjustment_plan
            logger.info(f"LLM根因分析完成: {adjustment_plan}")

        logger.info(f"RAG+LLM精选完成: 选中 {len(selected)} 只标的")
        return selected

    # ──────────────────────────────────────────────────────────────────────────
    # 5. 增强版失败根因分析（LLM分析→智能调整策略参数）
    # ──────────────────────────────────────────────────────────────────────────

    async def _llm_analyze_failure_root_cause(
        self,
        candidates: list[EnrichedCandidate],
        evaluations: list[dict],
        selected_count: int,
        target_count: int,
        market_cycle: str,
    ) -> dict:
        """LLM分析选股失败根因，并给出智能调整策略.

        分析维度:
        1. 标的池太小？ → 扩大pool_size
        2. 筛选太严格？ → 放宽阈值
        3. 目标太高？ → 降低select_count
        4. 某行业无标的？ → 放宽该行业条件
        5. 数据获取失败？ → 调整数据源
        """
        # 统计失败原因
        avoid_count = sum(1 for e in evaluations if e.get("recommendation") == "avoid")
        low_score_count = sum(1 for e in evaluations if e.get("score", 0) < 60)
        sector_coverage = len(set(c.sector for c in candidates))

        # 构建分析提示词
        prompt = f"""你是一位量化选股策略分析师。当前选股结果不足，请分析根因并给出调整方案。

当前状态:
- 候选池: {len(candidates)} 只
- 选中: {selected_count} 只
- 目标: {target_count} 只
- 推荐avoid: {avoid_count} 只
- 评分<60: {low_score_count} 只
- 覆盖行业数: {sector_coverage}
- 市场周期: {market_cycle}

评估摘要:
{self._format_evaluations_summary(evaluations)}

请分析失败根因并输出JSON格式:
{{
    "root_cause": "主要原因",
    "root_cause_type": "pool_too_small|too_strict|target_too_high|missing_sector|data_failure",
    "analysis": "详细分析",
    "adjustments": {{
        "expand_pool": true/false,
        "pool_size_increase": 50,
        "relax_thresholds": true/false,
        "threshold_relax_pct": 0.1,
        "lower_target": true/false,
        "new_target_count": 8,
        "relax_sector": "",
        "adjust_data_source": true/false
    }},
    "confidence": "high|medium|low"
}}"""

        try:
            if self.llm:
                response = await self.llm.generate(prompt)
                # 尝试解析JSON
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    plan = json.loads(response[json_start:json_end])
                    return plan
        except Exception as e:
            logger.warning(f"LLM根因分析失败: {e}")

        # Fallback: 基于规则推断
        return self._infer_adjustment_plan(
            candidates, evaluations, selected_count, target_count
        )

    def _infer_adjustment_plan(
        self,
        candidates: list[EnrichedCandidate],
        evaluations: list[dict],
        selected_count: int,
        target_count: int,
    ) -> dict:
        """基于规则推断调整方案（LLM失败时的fallback）."""
        plan = {
            "root_cause": "",
            "root_cause_type": "",
            "analysis": "",
            "adjustments": {},
            "confidence": "medium",
        }

        ratio = selected_count / target_count if target_count > 0 else 0

        if len(candidates) < target_count * 3:
            plan["root_cause"] = "候选池太小"
            plan["root_cause_type"] = "pool_too_small"
            plan["adjustments"]["expand_pool"] = True
            plan["adjustments"]["pool_size_increase"] = max(50, target_count * 5 - len(candidates))
        elif ratio < 0.3:
            plan["root_cause"] = "筛选太严格，大量候选被排除"
            plan["root_cause_type"] = "too_strict"
            plan["adjustments"]["relax_thresholds"] = True
            plan["adjustments"]["threshold_relax_pct"] = 0.15
        elif selected_count < target_count * 0.5:
            plan["root_cause"] = "目标数量偏高"
            plan["root_cause_type"] = "target_too_high"
            plan["adjustments"]["lower_target"] = True
            plan["adjustments"]["new_target_count"] = max(selected_count + 2, target_count - 3)
        else:
            plan["root_cause"] = "综合因素"
            plan["root_cause_type"] = "mixed"
            plan["adjustments"]["expand_pool"] = True
            plan["adjustments"]["pool_size_increase"] = 30
            plan["adjustments"]["relax_thresholds"] = True
            plan["adjustments"]["threshold_relax_pct"] = 0.1

        return plan

    def _format_evaluations_summary(self, evaluations: list[dict]) -> str:
        """格式化评估摘要."""
        parts = []
        score_dist = {"90-100": 0, "75-89": 0, "60-74": 0, "40-59": 0, "0-39": 0}
        for e in evaluations:
            score = e.get("score", 0)
            if score >= 90:
                score_dist["90-100"] += 1
            elif score >= 75:
                score_dist["75-89"] += 1
            elif score >= 60:
                score_dist["60-74"] += 1
            elif score >= 40:
                score_dist["40-59"] += 1
            else:
                score_dist["0-39"] += 1

        parts.append(f"评分分布: {score_dist}")
        parts.append(f"strong_buy: {sum(1 for e in evaluations if e.get('recommendation') == 'strong_buy')}")
        parts.append(f"buy: {sum(1 for e in evaluations if e.get('recommendation') == 'buy')}")
        parts.append(f"hold: {sum(1 for e in evaluations if e.get('recommendation') == 'hold')}")
        parts.append(f"avoid: {sum(1 for e in evaluations if e.get('recommendation') == 'avoid')}")

        return "\n".join(parts)

    # ──────────────────────────────────────────────────────────────────────────
    # 1. 标的画像构建
    # ──────────────────────────────────────────────────────────────────────────

    def _build_stock_profile(self, candidate: EnrichedCandidate) -> str:
        """构建标的文字画像，用于RAG检索和LLM评估."""
        parts = [
            f"标的: {candidate.name}({candidate.symbol})",
            f"行业: {candidate.sector}",
            f"类型: {candidate.asset_class}",
            f"多维度综合评分: {candidate.composite_score:.2f}",
        ]

        # 基本面
        if candidate.fundamental:
            f = candidate.fundamental
            fund_parts = []
            if f.roe is not None:
                fund_parts.append(f"ROE={f.roe:.1f}%")
            if f.gross_margin is not None:
                fund_parts.append(f"毛利率={f.gross_margin:.1f}%")
            if f.net_margin is not None:
                fund_parts.append(f"净利率={f.net_margin:.1f}%")
            if f.revenue_growth is not None:
                fund_parts.append(f"营收增速={f.revenue_growth:.1f}%")
            if f.peg is not None:
                fund_parts.append(f"PEG={f.peg:.2f}")
            if fund_parts:
                parts.append(f"基本面: {' '.join(fund_parts)} (评分{f.score:.2f})")

        # 技术面
        if candidate.technical:
            t = candidate.technical
            tech_parts = []
            if t.ema20 and t.ema60:
                tech_parts.append(f"EMA20/60={t.ema20:.1f}/{t.ema60:.1f}")
            if t.vol_ratio is not None:
                tech_parts.append(f"量能比={t.vol_ratio:.2f}")
            if t.volatility_120d is not None:
                tech_parts.append(f"120日波动率={t.volatility_120d:.1f}%")
            if t.latest_change is not None:
                tech_parts.append(f"最新涨幅={t.latest_change:.2f}%")
            if t.rsi14 is not None:
                tech_parts.append(f"RSI14={t.rsi14:.1f}")
            if t.macd_signal:
                tech_parts.append(f"MACD={t.macd_signal}")
            if tech_parts:
                parts.append(f"技术面: {' '.join(tech_parts)} (评分{t.score:.2f})")

        # 资金面
        if candidate.capital_flow:
            cf = candidate.capital_flow
            cap_parts = []
            if cf.main_net_inflow_5d is not None:
                cap_parts.append(f"5日主力净流入={cf.main_net_inflow_5d/1e8:.2f}亿")
            if cf.margin_change_rate is not None:
                cap_parts.append(f"融资变化={cf.margin_change_rate:.1f}%")
            if cf.northbound_net_5d is not None:
                cap_parts.append(f"北向5日={cf.northbound_net_5d/1e8:.2f}亿")
            if cap_parts:
                parts.append(f"资金面: {' '.join(cap_parts)} (评分{cf.score:.2f})")

        # 控盘度
        if candidate.control_degree:
            cd = candidate.control_degree
            ctrl_parts = []
            if cd.chip_concentration is not None:
                ctrl_parts.append(f"筹码集中度={cd.chip_concentration:.1f}%")
            if cd.shareholder_change_rate is not None:
                ctrl_parts.append(f"股东户数变化={cd.shareholder_change_rate:.1f}%")
            if cd.institution_hold_ratio is not None:
                ctrl_parts.append(f"机构持仓={cd.institution_hold_ratio:.1f}%")
            if ctrl_parts:
                parts.append(f"控盘度: {' '.join(ctrl_parts)} (评分{cd.score:.2f})")

        return "\n".join(parts)

    # ──────────────────────────────────────────────────────────────────────────
    # 2. RAG检索
    # ──────────────────────────────────────────────────────────────────────────

    async def _rag_retrieve(self, profile: str) -> dict:
        """RAG检索：相似历史案例、行业研报、公司公告."""
        result = {}

        try:
            # 检索相似历史案例
            similar_cases = await self.rag.similarity_search(
                query=profile,
                filter={"type": "historical_pattern"},
                top_k=2,
            )
            result["similar_cases"] = similar_cases
        except Exception as e:
            logger.debug(f"RAG相似案例检索失败: {e}")

        try:
            # 检索行业研报
            research_reports = await self.rag.similarity_search(
                query=profile,
                filter={"type": "research_report"},
                top_k=2,
            )
            result["research_reports"] = research_reports
        except Exception as e:
            logger.debug(f"RAG研报检索失败: {e}")

        try:
            # 检索公司公告
            announcements = await self.rag.similarity_search(
                query=profile,
                filter={"type": "announcement"},
                top_k=2,
            )
            result["announcements"] = announcements
        except Exception as e:
            logger.debug(f"RAG公告检索失败: {e}")

        return result

    def _format_rag_results(self, rag_result: dict) -> str:
        """格式化RAG检索结果为文本."""
        parts = []

        if "similar_cases" in rag_result and rag_result["similar_cases"]:
            parts.append("相似历史案例:")
            for i, case in enumerate(rag_result["similar_cases"][:2], 1):
                content = case.get("content", "") if isinstance(case, dict) else str(case)
                parts.append(f"  {i}. {content[:100]}...")

        if "research_reports" in rag_result and rag_result["research_reports"]:
            parts.append("行业研报:")
            for i, report in enumerate(rag_result["research_reports"][:2], 1):
                content = report.get("content", "") if isinstance(report, dict) else str(report)
                parts.append(f"  {i}. {content[:100]}...")

        if "announcements" in rag_result and rag_result["announcements"]:
            parts.append("公司公告:")
            for i, ann in enumerate(rag_result["announcements"][:2], 1):
                content = ann.get("content", "") if isinstance(ann, dict) else str(ann)
                parts.append(f"  {i}. {content[:100]}...")

        if not parts:
            return "无RAG检索结果"

        return "\n".join(parts)

    # ──────────────────────────────────────────────────────────────────────────
    # 3. LLM评估
    # ──────────────────────────────────────────────────────────────────────────

    async def _llm_evaluate_batch(
        self,
        candidates: list[EnrichedCandidate],
        profiles: list[str],
        rag_results: list[dict],
        market_cycle: str,
    ) -> list[dict]:
        """批量LLM评估."""
        evaluations = []

        # 分批处理，避免单次请求过大
        batch_size = 5
        for i in range(0, len(candidates), batch_size):
            batch_candidates = candidates[i:i + batch_size]
            batch_profiles = profiles[i:i + batch_size]
            batch_rag = rag_results[i:i + batch_size]

            batch_evaluations = await self._llm_evaluate_single_batch(
                batch_candidates, batch_profiles, batch_rag, market_cycle
            )
            evaluations.extend(batch_evaluations)

        return evaluations

    async def _llm_evaluate_single_batch(
        self,
        candidates: list[EnrichedCandidate],
        profiles: list[str],
        rag_results: list[dict],
        market_cycle: str,
    ) -> list[dict]:
        """评估单批候选标的."""
        # 构建批量提示词
        stocks_text = []
        for idx, (profile, rag) in enumerate(zip(profiles, rag_results), 1):
            stocks_text.append(f"\n=== 标的 {idx} ===\n{profile}\n\nRAG检索结果:\n{self._format_rag_results(rag)}")

        prompt = f"""你是一位资深量化选股分析师。请根据以下标的画像和RAG检索结果，对每只标的给出综合评估。

当前市场周期: {market_cycle}

请对以下 {len(candidates)} 只标的逐一评估：
{''.join(stocks_text)}

对每只标的，请输出以下JSON格式:
{{
    "symbol": "股票代码",
    "score": 0-100的综合评分,
    "confidence": "high|medium|low",
    "reasoning": "选股理由，80字以内，说明为什么这只标的好或不好",
    "risks": ["风险1", "风险2"],
    "recommendation": "strong_buy|buy|hold|avoid"
}}

评分标准:
- 90-100: 极佳标的，各方面优秀，强烈推荐
- 75-89: 良好标的，符合当前市场周期，推荐
- 60-74: 一般标的，有亮点但也有风险，可持有
- 40-59: 较差标的，存在明显问题，建议回避
- 0-39: 差标的，有重大风险，强烈回避

请确保输出是合法的JSON数组格式。["""

        try:
            response = await self.llm.generate(prompt)
            # 尝试解析JSON
            evaluations = self._parse_llm_response(response, candidates)
            return evaluations
        except Exception as e:
            logger.warning(f"LLM批量评估失败: {e}")
            return self._fallback_evaluations(candidates)

    def _parse_llm_response(
        self, response: str, candidates: list[EnrichedCandidate]
    ) -> list[dict]:
        """解析LLM返回的JSON."""
        try:
            # 尝试直接解析
            evaluations = json.loads(response)
            if isinstance(evaluations, list):
                return self._match_evaluations(evaluations, candidates)
        except json.JSONDecodeError:
            pass

        # 尝试提取JSON数组
        try:
            start = response.find("[")
            end = response.rfind("]")
            if start != -1 and end != -1:
                evaluations = json.loads(response[start:end + 1])
                if isinstance(evaluations, list):
                    return self._match_evaluations(evaluations, candidates)
        except (json.JSONDecodeError, ValueError):
            pass

        # 尝试逐行解析JSON对象
        evaluations = []
        for line in response.split("\n"):
            line = line.strip()
            if line and line.startswith("{") and line.endswith("}"):
                try:
                    eval_obj = json.loads(line)
                    evaluations.append(eval_obj)
                except json.JSONDecodeError:
                    continue

        if evaluations:
            return self._match_evaluations(evaluations, candidates)

        # 解析失败，返回fallback
        logger.warning("LLM响应JSON解析失败，使用fallback评估")
        return self._fallback_evaluations(candidates)

    def _match_evaluations(
        self, evaluations: list[dict], candidates: list[EnrichedCandidate]
    ) -> list[dict]:
        """将LLM评估结果与候选标的匹配."""
        result = []
        eval_map = {e.get("symbol", ""): e for e in evaluations}

        for candidate in candidates:
            eval_obj = eval_map.get(candidate.symbol, {})
            if eval_obj:
                result.append({
                    "symbol": candidate.symbol,
                    "score": float(eval_obj.get("score", 60)),
                    "confidence": eval_obj.get("confidence", "medium"),
                    "reasoning": eval_obj.get("reasoning", ""),
                    "risks": eval_obj.get("risks", []),
                    "recommendation": eval_obj.get("recommendation", "hold"),
                })
            else:
                # 未匹配到评估，使用fallback
                result.append(self._single_fallback_evaluation(candidate))

        return result

    def _fallback_evaluations(self, candidates: list[EnrichedCandidate]) -> list[dict]:
        """LLM失败时的备选评估（基于综合评分）."""
        return [self._single_fallback_evaluation(c) for c in candidates]

    def _single_fallback_evaluation(self, candidate: EnrichedCandidate) -> dict:
        """单只标的的fallback评估."""
        score = candidate.composite_score * 100

        if score >= 80:
            recommendation = "buy"
            confidence = "medium"
        elif score >= 65:
            recommendation = "buy"
            confidence = "medium"
        elif score >= 50:
            recommendation = "hold"
            confidence = "low"
        else:
            recommendation = "avoid"
            confidence = "low"

        return {
            "symbol": candidate.symbol,
            "score": score,
            "confidence": confidence,
            "reasoning": f"综合评分{candidate.composite_score:.2f}，基于基本面/技术面/资金面/控盘度多维度评估",
            "risks": ["LLM评估不可用，评分基于量化模型"],
            "recommendation": recommendation,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # 4. 监督审核
    # ──────────────────────────────────────────────────────────────────────────

    def _supervision_check(
        self,
        candidates: list[EnrichedCandidate],
        evaluations: list[dict],
        top_sectors: list[dict],
        target_count: int,
        min_llm_score: float,
        max_per_sector: int,
        etf_ratio_max: float,
        stock_ratio_max: float,
    ) -> list[SelectedStock]:
        """
        监督审核：
        1. 质量门槛：LLM评分 >= min_llm_score
        2. 同质化检查：同一行业标的不超过max_per_sector只
        3. 风格漂移检查：ETF和个股比例符合配置
        4. 推荐等级过滤：排除avoid
        """
        # 按LLM评分排序
        scored = list(zip(candidates, evaluations))
        scored.sort(key=lambda x: x[1].get("score", 0), reverse=True)

        selected = []
        sector_counts = defaultdict(int)
        etf_count = 0
        stock_count = 0

        # 提取top_sectors中的sector名称
        top_sector_names = {s["sector"] for s in top_sectors}

        for candidate, eval_result in scored:
            # 质量门槛
            if eval_result.get("score", 0) < min_llm_score:
                continue

            # 推荐等级过滤
            if eval_result.get("recommendation") == "avoid":
                continue

            # 同质化检查
            if sector_counts[candidate.sector] >= max_per_sector:
                continue

            # 风格漂移检查：ETF:个股比例
            if candidate.asset_class == "ETF":
                if etf_count >= target_count * etf_ratio_max:
                    continue
            elif candidate.asset_class == "stock":
                if stock_count >= target_count * stock_ratio_max:
                    continue

            # 构建SelectedStock
            selected.append(SelectedStock(
                symbol=candidate.symbol,
                name=candidate.name,
                sector=candidate.sector,
                asset_class=candidate.asset_class,
                composite_score=candidate.composite_score,
                llm_score=eval_result.get("score", 0),
                llm_confidence=eval_result.get("confidence", "low"),
                reasoning=eval_result.get("reasoning", ""),
                risks=eval_result.get("risks", []),
                recommendation=eval_result.get("recommendation", "hold"),
                data_sources=candidate.data_sources + ["RAG检索", "LLM评估"],
            ))

            sector_counts[candidate.sector] += 1
            if candidate.asset_class == "ETF":
                etf_count += 1
            else:
                stock_count += 1

            if len(selected) >= target_count:
                break

        return selected

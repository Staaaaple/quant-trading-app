"""投资顾问生成服务.

整合检索结果 + Prompt模板 + Qwen3生成投资顾问式回答.
"""

import json
from typing import Any
from dataclasses import dataclass

from .retriever_v2 import InvestmentRetriever, get_retriever_v2
from .llm_service import LLMService, get_llm_service
from .prompt_templates import PromptTemplates


@dataclass
class AdvisorResponse:
    """投资顾问回答."""

    answer: str
    query_type: str
    sources: list[dict[str, Any]]
    model: str
    usage: dict[str, int] | None = None


class InvestmentAdvisor:
    """投资顾问服务."""

    def __init__(
        self,
        retriever: InvestmentRetriever | None = None,
        llm_service: LLMService | None = None,
    ):
        self.retriever = retriever or get_retriever_v2()
        self.llm = llm_service or get_llm_service()
        self.prompts = PromptTemplates()

    async def answer(
        self,
        query: str,
        user_profile: dict[str, Any] | None = None,
    ) -> AdvisorResponse:
        """回答用户投资问题.

        Args:
            query: 用户查询
            user_profile: 用户画像（可选）

        Returns:
            AdvisorResponse
        """
        # 1. 分类查询意图
        query_type = self.retriever.classify_query(query)

        # 2. 检索相关知识
        context = await self.retriever.retrieve(query, query_type)

        # 3. 构建Prompt
        prompt = self._build_prompt(query, query_type, context, user_profile)

        # 4. 调用LLM生成回答
        response = await self.llm.generate_async(
            prompt=prompt,
            system_prompt=PromptTemplates.SYSTEM_PROMPT,
        )

        # 5. 整理来源
        sources = self._collect_sources(context)

        return AdvisorResponse(
            answer=response.text,
            query_type=query_type,
            sources=sources,
            model=response.model,
            usage=response.usage,
        )

    def _build_prompt(
        self,
        query: str,
        query_type: str,
        context: Any,
        user_profile: dict[str, Any] | None,
    ) -> str:
        """构建Prompt.

        Args:
            query: 用户查询
            query_type: 查询类型
            context: 检索上下文
            user_profile: 用户画像

        Returns:
            完整Prompt
        """
        # 将context转为字典格式
        context_dict = {
            "stock_cases": [
                {"id": r.id, "text": r.text, "metadata": r.metadata}
                for r in context.stock_cases
            ],
            "valuation_cases": [
                {"id": r.id, "text": r.text, "metadata": r.metadata}
                for r in context.valuation_cases
            ],
            "theories": [
                {"id": r.id, "text": r.text, "metadata": r.metadata}
                for r in context.theories
            ],
            "basics": [
                {"id": r.id, "text": r.text, "metadata": r.metadata}
                for r in context.basics
            ],
            "behavioral_cases": [
                {"id": r.id, "text": r.text, "metadata": r.metadata}
                for r in context.behavioral_cases
            ],
            "paper_chunks": [
                {"id": r.id, "text": r.text, "metadata": r.metadata}
                for r in context.paper_chunks
            ],
        }

        if query_type == "个股分析":
            return self.prompts.build_stock_analysis_prompt(
                query=query,
                context=context_dict,
                stock_info={"name": self._extract_stock_name(query)},
            )
        elif query_type == "估值分析":
            return self.prompts.build_valuation_prompt(
                query=query,
                context=context_dict,
            )
        elif query_type == "组合构建":
            return self.prompts.build_portfolio_prompt(
                query=query,
                context=context_dict,
                profile=user_profile or {},
            )
        elif query_type in ["概念解释", "理论解释"]:
            return self.prompts.build_concept_prompt(
                query=query,
                context=context_dict,
            )
        else:
            # 通用Prompt
            context_text = self.prompts.build_context(
                [
                    {"text": r.text}
                    for r in (
                        context.stock_cases
                        + context.valuation_cases
                        + context.theories
                        + context.basics
                    )
                ]
            )

            return f"""请基于以下资料，回答投资问题。

## 用户问题
{query}

## 参考资料
{context_text}

## 要求
1. 给出明确结论
2. 提供数据支撑
3. 提示风险
4. 引用参考资料"""

    def _collect_sources(self, context: Any) -> list[dict[str, Any]]:
        """收集引用来源."""
        sources = []

        for r in context.stock_cases:
            sources.append({
                "id": r.id,
                "type": "个股案例",
                "score": r.score,
                "metadata": r.metadata,
            })

        for r in context.valuation_cases:
            sources.append({
                "id": r.id,
                "type": "估值案例",
                "score": r.score,
                "metadata": r.metadata,
            })

        for r in context.theories:
            sources.append({
                "id": r.id,
                "type": "理论",
                "score": r.score,
                "metadata": r.metadata,
            })

        for r in context.basics:
            sources.append({
                "id": r.id,
                "type": "基础知识",
                "score": r.score,
                "metadata": r.metadata,
            })

        for r in context.behavioral_cases:
            sources.append({
                "id": r.id,
                "type": "行为金融",
                "score": r.score,
                "metadata": r.metadata,
            })

        for r in context.paper_chunks:
            sources.append({
                "id": r.id,
                "type": "论文",
                "score": r.score,
                "metadata": r.metadata,
            })

        # 按相关度排序
        sources.sort(key=lambda x: x["score"], reverse=True)
        return sources[:10]  # 最多返回10个来源

    def _extract_stock_name(self, query: str) -> str:
        """从查询中提取股票名称."""
        # 简单实现，实际可用NER
        stock_names = {
            "茅台": "贵州茅台",
            "宁德": "宁德时代",
            "比亚迪": "比亚迪",
            "中际": "中际旭创",
            "长江电力": "长江电力",
            "神华": "中国神华",
        }

        for key, name in stock_names.items():
            if key in query:
                return name

        return "该股票"


async def get_investment_advice(
    query: str,
    user_profile: dict[str, Any] | None = None,
) -> AdvisorResponse:
    """获取投资建议（便捷函数）."""
    advisor = InvestmentAdvisor()
    return await advisor.answer(query, user_profile)

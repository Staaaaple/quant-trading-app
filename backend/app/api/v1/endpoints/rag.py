"""RAG 投资顾问 API 端点."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.rag.investment_advisor import (
    InvestmentAdvisor,
    get_investment_advice,
    AdvisorResponse,
)
from app.services.rag.index_builder_v2 import IndexBuilderV2
from app.services.rag.retriever_v2 import get_retriever_v2
from app.services.rag.data_loader import load_all_knowledge

router = APIRouter()


@router.post("/query", response_model=dict[str, Any])
async def rag_query(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
):
    """投资顾问问答.

    请求:
        {
            "query": "分析宁德时代",
            "user_id": 1  // 可选
        }

    响应:
        {
            "answer": "📊 宁德时代...",
            "query_type": "个股分析",
            "sources": [...],
            "model": "Qwen3-14B-MLX-4bit"
        }
    """
    query = payload.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="query is required")

    # 获取用户画像（如有user_id）
    user_profile = None
    user_id = payload.get("user_id")
    if user_id:
        # TODO: 从数据库获取用户画像
        pass

    # 调用投资顾问
    response = await get_investment_advice(query, user_profile)

    return {
        "answer": response.answer,
        "query_type": response.query_type,
        "sources": response.sources,
        "model": response.model,
        "usage": response.usage,
    }


@router.post("/stock-analysis", response_model=dict[str, Any])
async def stock_analysis(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
):
    """个股分析.

    请求:
        {
            "symbol": "300750",
            "user_id": 1  // 可选
        }
    """
    symbol = payload.get("symbol")
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")

    query = f"分析{symbol}"
    response = await get_investment_advice(query)

    return {
        "symbol": symbol,
        "analysis": response.answer,
        "sources": response.sources,
        "model": response.model,
    }


@router.post("/portfolio-advice", response_model=dict[str, Any])
async def portfolio_advice(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
):
    """组合建议.

    请求:
        {
            "risk_profile": "稳健型",
            "capital": 500000,
            "market_cycle": "复苏期"
        }
    """
    risk_profile = payload.get("risk_profile", "稳健型")
    capital = payload.get("capital", 500000)
    market_cycle = payload.get("market_cycle", "复苏期")

    query = f"{risk_profile}投资者，{capital/10000:.0f}万资金，{market_cycle}怎么配置"

    user_profile = {
        "risk_profile": risk_profile,
        "capital": capital,
        "market_cycle": market_cycle,
    }

    response = await get_investment_advice(query, user_profile)

    return {
        "risk_profile": risk_profile,
        "capital": capital,
        "allocation": response.answer,
        "sources": response.sources,
        "model": response.model,
    }


@router.post("/valuation", response_model=dict[str, Any])
async def valuation_analysis(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
):
    """估值分析.

    请求:
        {
            "symbol": "600519"
        }
    """
    symbol = payload.get("symbol")
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")

    query = f"{symbol}估值分析"
    response = await get_investment_advice(query)

    return {
        "symbol": symbol,
        "valuation": response.answer,
        "sources": response.sources,
        "model": response.model,
    }


@router.post("/concept", response_model=dict[str, Any])
async def concept_explain(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
):
    """概念解释.

    请求:
        {
            "concept": "市盈率"
        }
    """
    concept = payload.get("concept")
    if not concept:
        raise HTTPException(status_code=400, detail="concept is required")

    query = f"什么是{concept}"
    response = await get_investment_advice(query)

    return {
        "concept": concept,
        "explanation": response.answer,
        "sources": response.sources,
        "model": response.model,
    }


@router.post("/build-index", response_model=dict[str, Any])
async def build_index(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
):
    """构建/重建向量索引.

    请求:
        {
            "force_rebuild": false
        }
    """
    force_rebuild = payload.get("force_rebuild", False)

    # 先加载数据（如有新YAML文件）
    data_dir = payload.get("data_dir")
    if data_dir:
        load_results = load_all_knowledge(db, data_dir)
    else:
        load_results = {}

    # 构建索引
    builder = IndexBuilderV2()
    index_results = builder.build_all(db, force_rebuild=force_rebuild)

    return {
        "load_results": load_results,
        "index_results": index_results,
        "status": "success",
    }


@router.get("/stats", response_model=dict[str, Any])
async def get_stats():
    """获取RAG系统统计信息."""
    retriever = get_retriever_v2()
    return retriever.get_stats()


@router.get("/health", response_model=dict[str, Any])
async def health_check():
    """健康检查."""
    retriever = get_retriever_v2()
    stats = retriever.get_stats()

    # 检查各索引是否存在
    all_exists = all(
        s.get("exists", False) for s in stats.values()
        if isinstance(s, dict) and "exists" in s
    )

    return {
        "status": "healthy" if all_exists else "degraded",
        "indexes": stats,
    }

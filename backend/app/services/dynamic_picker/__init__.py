"""动态选股模块 (Dynamic Stock Picker).

根据信号仪表盘实时爬取板块成分股、ETF、热门股，
通过基本面/技术面/资金面/控盘程度多维度筛选，
最终由RAG+LLM做挑选和监督。

使用示例:
    from app.services.dynamic_picker import DynamicStockPicker

    picker = DynamicStockPicker(rag_service=rag, llm_service=llm)
    result = await picker.pick(
        top_sectors=[{"sector": "technology", "weight": 0.25}],
        market_cycle="expansion",
    )
"""

from .dynamic_stock_picker import DynamicStockPicker
from .models import (
    AssetClass,
    Confidence,
    Recommendation,
    StockCandidate,
    FundamentalMetrics,
    TechnicalMetrics,
    CapitalFlowMetrics,
    ControlDegreeMetrics,
    EnrichedCandidate,
    SelectedStock,
    StockPickingResult,
)
from .pool_builder import PoolBuilder
from .data_enricher import DataEnricher
from .multi_dimension_filter import MultiDimensionFilter
from .rag_llm_selector import RAGLLMSelector

__all__ = [
    # 主入口
    "DynamicStockPicker",
    # 子模块
    "PoolBuilder",
    "DataEnricher",
    "MultiDimensionFilter",
    "RAGLLMSelector",
    # 数据模型
    "AssetClass",
    "Confidence",
    "Recommendation",
    "StockCandidate",
    "FundamentalMetrics",
    "TechnicalMetrics",
    "CapitalFlowMetrics",
    "ControlDegreeMetrics",
    "EnrichedCandidate",
    "SelectedStock",
    "StockPickingResult",
]

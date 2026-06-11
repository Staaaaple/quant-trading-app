"""RAG 投资顾问知识库模型.

六大知识源:
1. stock_analysis_cases - 个股深度分析案例
2. allocation_theory - 资产配置理论
3. finance_basics - 基础金融与投资常识
4. valuation_timing_cases - 估值与买卖节点案例
5. behavioral_cases - 行为金融与投资者心理
6. paper_chunks - 高质量论文片段
"""

import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, Boolean
from app.db.base import Base


class StockAnalysisCase(Base):
    """个股深度分析案例库.

    记录近几年大涨股票的深度复盘，包含买点/卖点/认知。
    """
    __tablename__ = "stock_analysis_cases"

    id = Column(Integer, primary_key=True)
    case_id = Column(String(64), unique=True, index=True, nullable=False)

    # 标的
    symbol = Column(String(16), index=True, nullable=False)
    name = Column(String(64), nullable=False)
    industry = Column(String(32), index=True)

    # 大涨时期
    bull_period = Column(String(32))
    price_start = Column(Float)
    price_peak = Column(Float)
    return_pct = Column(Float)

    # 投资逻辑
    industry_trend = Column(Text)
    company_moat = Column(Text)
    growth_driver = Column(JSON)
    competitive_advantage = Column(Text)

    # 关键指标
    key_metrics = Column(JSON)

    # 估值分析
    valuation_at_buy = Column(JSON)
    valuation_at_peak = Column(JSON)

    # 买点识别
    entry_signals = Column(JSON)

    # 卖点识别
    exit_signals = Column(JSON)

    # 关键认知
    key_insights = Column(JSON)

    # 经验教训
    lessons = Column(JSON)

    # 内容（用于Embedding）
    content = Column(Text, nullable=False)

    # 元数据
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class AllocationTheory(Base):
    """资产配置理论库.

    CAPM、Barra、风险平价等经典理论。
    """
    __tablename__ = "allocation_theory"

    id = Column(Integer, primary_key=True)
    theory_id = Column(String(64), unique=True, index=True, nullable=False)

    # 基本信息
    name = Column(String(128), nullable=False)
    name_cn = Column(String(128))
    category = Column(String(32), index=True)  # 经典理论/因子投资/行为金融

    # 来源
    origin_authors = Column(String(256))
    origin_year = Column(Integer)
    origin_paper = Column(String(512))

    # 核心内容
    core_formula = Column(String(256))
    explanation = Column(JSON)  # 要点列表
    assumptions = Column(JSON)
    limitations = Column(JSON)
    application = Column(JSON)

    # 中国市场适配
    china_adaptation = Column(Text)

    # 内容（用于Embedding）
    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class FinanceBasic(Base):
    """基础金融与投资常识库.

    从入门到进阶的完整知识体系。
    """
    __tablename__ = "finance_basics"

    id = Column(Integer, primary_key=True)
    entry_id = Column(String(64), unique=True, index=True, nullable=False)

    # 分类
    topic = Column(String(128), nullable=False)
    category = Column(String(32), index=True)  # 投资工具/财报分析/估值/风险/宏观/心理
    difficulty = Column(String(16), index=True)  # 入门/进阶/专业

    # 内容
    definition = Column(Text)
    simple_explanation = Column(Text)
    usage = Column(JSON)
    cautions = Column(JSON)
    example = Column(Text)

    # 关联
    related_concepts = Column(JSON)
    common_questions = Column(JSON)

    # 内容（用于Embedding）
    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ValuationTimingCase(Base):
    """估值与买卖节点案例库.

    基于估值和企业认知的买卖决策案例。
    """
    __tablename__ = "valuation_timing_cases"

    id = Column(Integer, primary_key=True)
    case_id = Column(String(64), unique=True, index=True, nullable=False)

    # 类型
    case_type = Column(String(16), index=True)  # 低估买入/高估卖出/持有不动

    # 标的
    symbol = Column(String(16), index=True)
    name = Column(String(64))
    period = Column(String(32))

    # 背景
    background = Column(JSON)

    # 估值
    valuation_at_bottom = Column(JSON)
    valuation_at_peak = Column(JSON)

    # 投资逻辑
    investment_logic = Column(JSON)

    # 结果
    outcome = Column(JSON)

    # 经验教训
    lessons = Column(JSON)

    # 内容（用于Embedding）
    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class BehavioralCase(Base):
    """行为金融与投资者心理案例库."""
    __tablename__ = "behavioral_cases"

    id = Column(Integer, primary_key=True)
    case_id = Column(String(64), unique=True, index=True, nullable=False)

    # 偏差类型
    bias_name = Column(String(64), nullable=False)
    bias_name_cn = Column(String(64))
    category = Column(String(32), index=True)  # 认知偏差/情绪偏差/决策偏差

    # 来源
    source_authors = Column(String(256))
    source_year = Column(Integer)

    # 内容
    phenomenon = Column(Text)
    china_example = Column(Text)
    coping_strategy = Column(JSON)
    system_countermeasure = Column(JSON)

    # 内容（用于Embedding）
    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class PaperChunk(Base):
    """高质量论文片段库.

    2020年后的前沿研究，已审核质量与关联度。
    """
    __tablename__ = "paper_chunks"

    id = Column(Integer, primary_key=True)
    chunk_id = Column(String(64), unique=True, index=True, nullable=False)
    paper_id = Column(String(64), index=True, nullable=False)

    # 论文元数据
    title = Column(String(512), nullable=False)
    authors = Column(String(512))
    year = Column(Integer, index=True)
    journal = Column(String(256))

    # 片段位置
    section = Column(String(64))  # Abstract/Introduction/Methodology/Results/Conclusion
    section_order = Column(Integer)
    chunk_order = Column(Integer)

    # 内容
    content = Column(Text, nullable=False)  # 原文（用于Embedding）
    content_zh = Column(Text)  # 中文摘要

    # 结构化提取
    key_findings = Column(JSON)
    methodology = Column(JSON)
    data_sample = Column(JSON)
    conclusions = Column(JSON)
    limitations = Column(JSON)

    # 标签
    keywords = Column(JSON)
    applicable_scenarios = Column(JSON)
    investment_applications = Column(JSON)

    # A股相关度
    a_relevance = Column(String(16))  # 高/中/低
    a_adaptation = Column(Text)

    # 引用信息
    related_chunks = Column(JSON)

    # 质量
    quality_score = Column(Integer)
    review_status = Column(String(16), default="待审核")  # 待审核/已审核/需修改
    reviewer = Column(String(64))
    review_date = Column(DateTime)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

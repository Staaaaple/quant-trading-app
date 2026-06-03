import datetime
from sqlalchemy import Column, Integer, String, JSON, Float, DateTime, Text
from app.db.base import Base


class PaperKnowledge(Base):
    __tablename__ = "paper_knowledges"

    id = Column(Integer, primary_key=True, index=True)

    # 论文元数据
    title = Column(String(512), nullable=False)
    authors = Column(String(512), nullable=True)
    arxiv_id = Column(String(64), nullable=True, index=True)
    publish_date = Column(String(16), nullable=True)  # YYYY-MM
    url = Column(String(512), nullable=True)

    # 所属策略家族
    family = Column(String(32), nullable=False, index=True)

    # 核心结论
    core_conclusion = Column(Text, nullable=True)
    key_findings = Column(JSON, nullable=True)  # ["发现1", "发现2"]

    # 参数范围
    param_space = Column(JSON, nullable=True)  # {"fast_ma": [5, 10, 20], "slow_ma": [30, 60]}

    # 适用条件
    suitable_cycles = Column(JSON, nullable=True)
    suitable_markets = Column(JSON, nullable=True)  # ["A股", "美股"]

    # 回测结果（论文中的或复现的）
    backtest_sharpe = Column(Float, nullable=True)
    backtest_max_drawdown = Column(Float, nullable=True)
    backtest_win_rate = Column(Float, nullable=True)
    backtest_annual_return = Column(Float, nullable=True)

    # 与现有策略的关联
    related_template_ids = Column(JSON, nullable=True)  # ["template_001"]

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

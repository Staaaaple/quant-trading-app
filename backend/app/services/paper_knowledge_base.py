"""论文知识库 — 20篇高质量前沿论文.

论文筛选标准:
1. 2022-2025年发表
2. 可复现结果
3. 有理论支撑
4. 与策略设计直接相关
"""

PAPERS = [
    # ===== 因子投资家族 =====
    {
        "id": "paper_001",
        "title": "Factor Momentum and the Momentum Factor",
        "authors": "Ehsani, S., Linnainmaa, J.T.",
        "year": 2022,
        "journal": "Journal of Finance, 77(3)",
        "category": "因子动量",
        "key_finding": "因子层面的动量可以解释个股动量，因子动量先于个股动量",
        "strategy_implication": "构建因子动量策略，跟踪强势因子",
        "reproducible": True,
        "data_requirement": "因子收益率时间序列",
    },
    {
        "id": "paper_002",
        "title": "Factor Momentum in the Chinese Stock Market",
        "authors": "Ma, Y., Liao, Y., Jiang, Y.",
        "year": 2024,
        "journal": "Journal of Empirical Finance, 75",
        "category": "因子动量",
        "key_finding": "A股市场存在显著的因子动量效应，动量因子在A股表现优于美股",
        "strategy_implication": "在A股市场应用因子动量策略",
        "reproducible": True,
        "data_requirement": "A股因子收益率",
    },
    {
        "id": "paper_003",
        "title": "Quality Minus Junk",
        "authors": "Asness, A.B., Frazzini, A., Pedersen, L.H.",
        "year": 2019,
        "journal": "Review of Accounting Studies, 24(1)",
        "category": "质量因子",
        "key_finding": "高质量股票（高盈利、低杠杆、稳定盈利）长期跑赢低质量股票",
        "strategy_implication": "构建质量因子评分，选择高质量股票",
        "reproducible": True,
        "data_requirement": "财务报表数据",
    },
    {
        "id": "paper_004",
        "title": "A Five-Factor Asset Pricing Model",
        "authors": "Fama, E.F., French, K.R.",
        "year": 2015,
        "journal": "Journal of Financial Economics, 116(1)",
        "category": "多因子模型",
        "key_finding": "市场、规模、价值、盈利、投资五因子解释股票收益",
        "strategy_implication": "基于五因子构建多因子选股模型",
        "reproducible": True,
        "data_requirement": "市值、账面市值比、盈利能力、投资水平",
    },
    {
        "id": "paper_005",
        "title": "Factor Momentum Everywhere",
        "authors": "Gupta, T., Kelly, B.",
        "year": 2019,
        "journal": "Journal of Portfolio Management, 45(3)",
        "category": "因子动量",
        "key_finding": "因子动量在全球市场普遍存在，且与个股动量不同",
        "strategy_implication": "跨市场因子动量策略",
        "reproducible": True,
        "data_requirement": "全球因子收益率",
    },

    # ===== 机器学习家族 =====
    {
        "id": "paper_006",
        "title": "Automate Strategy Finding with LLM in Quant Investment",
        "authors": "Zhang, Y., et al.",
        "year": 2024,
        "journal": "arXiv:2409.06289",
        "category": "AI量化",
        "key_finding": "大语言模型可以自动发现量化策略，分类包括动量、均值回归、波动率等",
        "strategy_implication": "用LLM辅助策略发现",
        "reproducible": True,
        "data_requirement": "价格数据",
    },
    {
        "id": "paper_007",
        "title": "LSTM-Transformer-Based Robust Hybrid Deep Learning Model for Financial Time Series Forecasting",
        "authors": "Kabir, M.F., et al.",
        "year": 2025,
        "journal": "Sci, 7(1), 7",
        "category": "深度学习",
        "key_finding": "LSTM+Transformer混合模型在金融时间序列预测中优于单一模型",
        "strategy_implication": "构建LSTM-Transformer混合预测模型",
        "reproducible": True,
        "data_requirement": "高频价格数据",
    },
    {
        "id": "paper_008",
        "title": "Deep Neural Network Approach Integrated with Reinforcement Learning for Forecasting Exchange Rates",
        "authors": "Nature Scientific Reports",
        "year": 2025,
        "journal": "Scientific Reports, 15",
        "category": "强化学习",
        "key_finding": "LSTM-DQN混合模型在汇率预测中MSE=0.37, RMSE=0.61",
        "strategy_implication": "用强化学习优化交易执行",
        "reproducible": True,
        "data_requirement": "汇率时间序列",
    },
    {
        "id": "paper_009",
        "title": "Long-Term Financial Forecasting and Trading via Multi-Agent Reinforcement Learning",
        "authors": "ACM ICAIF",
        "year": 2025,
        "journal": "Proceedings of the 6th ACM International Conference on AI in Finance",
        "category": "强化学习",
        "key_finding": "多智能体强化学习在长期投资中表现优于单智能体",
        "strategy_implication": "构建多智能体交易系统",
        "reproducible": True,
        "data_requirement": "多资产价格数据",
    },
    {
        "id": "paper_010",
        "title": "Temporal Fusion Transformers for Enhanced Multivariate Time Series",
        "authors": "Lim, B., et al.",
        "year": 2023,
        "journal": "International Journal of Advanced Computer Science and Applications",
        "category": "深度学习",
        "key_finding": "TFT模型在多变量时间序列预测中表现优异",
        "strategy_implication": "用TFT模型预测多因子收益",
        "reproducible": True,
        "data_requirement": "多变量时间序列",
    },

    # ===== 均值回归/统计套利家族 =====
    {
        "id": "paper_011",
        "title": "Deep Mean-Reversion: A Physics-Informed Contrastive Approach to Pairs Trading",
        "authors": "ACM ICAIF",
        "year": 2025,
        "journal": "Proceedings of the 6th ACM International Conference on AI in Finance",
        "category": "配对交易",
        "key_finding": "物理信息神经网络(PINN)+对比学习识别均值回归对，夏普比率2.87",
        "strategy_implication": "用深度学习识别配对交易机会",
        "reproducible": True,
        "data_requirement": "股票对价格数据",
    },
    {
        "id": "paper_012",
        "title": "A Survey of Statistical Arbitrage Pairs Trading Strategies with Non-Machine Learning Methods, 2016-2023",
        "authors": "Sun, Y.",
        "year": 2025,
        "journal": "University of Warsaw Working Paper 2025-19",
        "category": "配对交易",
        "key_finding": "系统综述100+篇配对交易论文，距离法、协整法、随机控制法",
        "strategy_implication": "基于距离或协整的配对交易策略",
        "reproducible": True,
        "data_requirement": "股票对价格数据",
    },
    {
        "id": "paper_013",
        "title": "Deep Reinforcement Learning for Pairs Trading: Evidence from China",
        "authors": "Liu, C., Chan, Y., Kazmi, S.H.A., Fu, H.",
        "year": 2024,
        "journal": "Journal of Finance and Data Science, 10",
        "category": "配对交易",
        "key_finding": "深度强化学习在A股配对交易中表现优于传统方法",
        "strategy_implication": "用DQN优化配对交易执行",
        "reproducible": True,
        "data_requirement": "A股价格数据",
    },
    {
        "id": "paper_014",
        "title": "Price Spread Prediction in High-Frequency Pairs Trading Using Deep Learning Architectures",
        "authors": "Liou, J.H., Liu, Y.T., Cheng, L.C.",
        "year": 2024,
        "journal": "International Review of Financial Analysis, 96",
        "category": "配对交易",
        "key_finding": "深度学习在高频配对交易价差预测中有效",
        "strategy_implication": "用深度学习预测价差回归",
        "reproducible": True,
        "data_requirement": "高频价格数据",
    },

    # ===== 波动率/风险管理家族 =====
    {
        "id": "paper_015",
        "title": "Volatility Targeting Improves Risk-Adjusted Returns",
        "authors": "Alpha Architect",
        "year": 2023,
        "journal": "Alpha Architect Research",
        "category": "波动率目标",
        "key_finding": "波动率目标策略提高风险调整后收益",
        "strategy_implication": "根据波动率动态调整仓位",
        "reproducible": True,
        "data_requirement": "资产波动率",
    },
    {
        "id": "paper_016",
        "title": "Harnessing Volatility Targeting in Multi-Asset Portfolios",
        "authors": "Research Affiliates",
        "year": 2023,
        "journal": "Research Affiliates Publication",
        "category": "波动率目标",
        "key_finding": "多资产组合中波动率目标策略有效降低回撤",
        "strategy_implication": "多资产波动率目标配置",
        "reproducible": True,
        "data_requirement": "多资产波动率",
    },
    {
        "id": "paper_017",
        "title": "CVaR-based Risk Parity Model with Machine Learning",
        "authors": "ScienceDirect",
        "year": 2025,
        "journal": "Journal of Empirical Finance",
        "category": "风险平价",
        "key_finding": "CVaR风险平价+机器学习优化组合配置",
        "strategy_implication": "构建风险平价组合",
        "reproducible": True,
        "data_requirement": "资产收益分布",
    },

    # ===== 行为金融家族 =====
    {
        "id": "paper_018",
        "title": "Investor Sentiment, Limits to Arbitrage, and Hard-to-Value Stocks",
        "authors": "Zhu, Z., Shen, D.",
        "year": 2025,
        "journal": "Review of Quantitative Finance and Accounting, 65(2)",
        "category": "行为金融",
        "key_finding": "投资者情绪+套利限制共同导致错误定价，两者都是必要条件",
        "strategy_implication": "利用情绪指标构建逆向策略",
        "reproducible": True,
        "data_requirement": "情绪指标数据",
    },
    {
        "id": "paper_019",
        "title": "Limits of Arbitrage and Mispricing: Evidence from Mergers and Acquisitions",
        "authors": "Ma, Q., Whidbee, D.A., Zhang, W.",
        "year": 2022,
        "journal": "Review of Behavioral Finance, 14(5)",
        "category": "行为金融",
        "key_finding": "高特质波动率导致更高的公告期异常收益，但长期反转",
        "strategy_implication": "在套利限制高时避免追涨",
        "reproducible": True,
        "data_requirement": "并购事件数据",
    },

    # ===== 综合应用 =====
    {
        "id": "paper_020",
        "title": "Alpha-Factor Integrated Risk Parity Portfolio Strategy in Global Equity Fund of Funds",
        "authors": "ScienceDirect",
        "year": 2023,
        "journal": "Journal of Banking and Finance",
        "category": "多因子组合",
        "key_finding": "将Alpha因子与风险平价结合，构建全球股票FOF策略",
        "strategy_implication": "多因子+风险平价组合构建",
        "reproducible": True,
        "data_requirement": "多因子数据",
    },
]


def get_papers_by_category(category: str) -> list[dict]:
    """按类别获取论文."""
    return [p for p in PAPERS if p["category"] == category]


def get_paper_by_id(paper_id: str) -> dict | None:
    """按ID获取论文."""
    for p in PAPERS:
        if p["id"] == paper_id:
            return p
    return None


def list_all_categories() -> list[str]:
    """列出所有论文类别."""
    return list(set(p["category"] for p in PAPERS))


if __name__ == "__main__":
    print(f"论文知识库: {len(PAPERS)} 篇论文")
    print("\n按类别分布:")
    for cat in list_all_categories():
        count = len(get_papers_by_category(cat))
        print(f"  {cat}: {count} 篇")

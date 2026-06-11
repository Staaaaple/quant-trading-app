# 动态选股架构设计 v1.0

## 1. 设计目标

将原有的**静态映射表选股**（symbol_mappings.py 预定义ETF+龙头股）升级为**动态实时选股**：

- **选股模块**：根据信号仪表盘实时爬取板块成分股、ETF、热门股
- **多维度筛选**：基本面 / 技术面 / 控盘程度 / 资金流向
- **RAG+LLM**：最终挑选和监督，确保选股逻辑透明可解释

---

## 2. 架构概览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         信号仪表盘 (Signal Dashboard)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ 宏观基本面   │  │ 地缘政治     │  │ 行业景气度   │  │ 社会实事/资产内部   │ │
│  │ (GDP/CPI..) │  │ (新闻爬虫)   │  │ (新闻频率)   │  │ (股债利差/情绪)     │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         └─────────────────┴─────────────────┴────────────────────┘            │
│                                    │                                         │
│                         market_signal_service.py                              │
│                         输出: top_sectors, market_cycle,                      │
│                             industry_scores, social_trends                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      动态选股引擎 (Dynamic Stock Picker)                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Step 1: 标的池构建 (Pool Builder)                                       ││
│  │  ├── 板块成分股爬取: akshare 行业/概念板块成分股接口                      ││
│  │  ├── ETF筛选: 根据行业匹配相关ETF (规模/流动性/跟踪误差筛选)              ││
│  │  └── 热门股补充: 资金流向/涨幅榜/龙虎榜                                  ││
│  │  输出: raw_pool (100~300只候选标的)                                     ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Step 2: 多维度初筛 (Multi-Dimension Filter)                             ││
│  │  ├── 基本面: ROE/毛利率/净利率/营收增速/PEG (排除ST/退市/停牌)           ││
│  │  ├── 技术面: EMA趋势/量能/波动率/支撑压力位 (排除涨停/暴跌/异常波动)     ││
│  │  ├── 资金面: 主力净流入/融资融券/北向资金/机构持仓变化                   ││
│  │  └── 控盘度: 筹码集中度/股东户数变化/机构控盘比例                        ││
│  │  输出: filtered_pool (30~60只)                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Step 3: RAG+LLM 精选 (RAG LLM Selector)                                 ││
│  │  ├── 构建标的画像: 每只候选标的多维度数据摘要                             ││
│  │  ├── RAG检索: 相似历史行情/行业研报/公司公告/舆情                         ││
│  │  ├── LLM评估: 综合评分 + 选股理由 + 风险提示                              ││
│  │  └── 监督审核: 同质化检查/集中度检查/风格漂移检查                         ││
│  │  输出: selected_pool (5~15只，每只含评分和理由)                         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Hybrid组合引擎 (Portfolio Designer)                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Step 4: 策略-标的绑定 (Strategy Binding)                                ││
│  │  ├── 主仓位: 行业ETF (从selected_pool中筛选ETF类标的)                    ││
│  │  ├── 卫星仓位: 个股增强 (从selected_pool中筛选个股类标的，权重>15%时)    ││
│  │  └── 标的替换: 同一行业多候选时，按LLM评分排序选择                       ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Step 5: 回测验证 (Backtest Validation)                                  ││
│  │  ├── 真实历史数据回测 (akshare)                                          ││
│  │  ├── 多时段验证 (牛市/熊市/震荡)                                         ││
│  │  └── 失败标的自动排除                                                    ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Step 6: RAG质检门控 (Quality Gate)                                      ││
│  │  ├── SAA/TAA/绑定/风控/可靠性/最终 六步审核                              ││
│  │  └── 不通过则返回重选                                                    ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 核心模块设计

### 3.1 标的池构建器 (Pool Builder)

```python
# app/services/dynamic_picker/pool_builder.py

class PoolBuilder:
    """根据信号仪表盘构建候选标的池"""

    async def build_pool(
        self,
        top_sectors: list[dict],        # TAA输出的Top行业
        market_cycle: str,              # 市场周期
        industry_scores: dict,          # 行业景气度评分
        social_trends: list[str],       # 社会趋势列表
        pool_size: int = 200,           # 目标池大小
    ) -> list[StockCandidate]:
        """
        构建候选标的池，包含三类标的：
        1. 板块成分股: 根据top_sectors爬取对应板块的所有成分股
        2. 行业ETF: 筛选与top_sectors相关的ETF
        3. 热门股: 根据资金流向/涨幅榜补充
        """
        candidates = []

        for sector_info in top_sectors:
            sector = sector_info["sector"]
            sector_name = sector_info.get("name", sector)

            # 1. 爬取板块成分股
            stocks = await self._fetch_sector_stocks(sector, sector_name)
            candidates.extend(stocks)

            # 2. 筛选相关ETF
            etfs = await self._fetch_sector_etfs(sector, sector_name)
            candidates.extend(etfs)

        # 3. 补充热门股（去重）
        hot_stocks = await self._fetch_hot_stocks()
        existing_symbols = {c.symbol for c in candidates}
        for hot in hot_stocks:
            if hot.symbol not in existing_symbols:
                candidates.append(hot)

        # 4. 按流动性排序，截取前pool_size
        candidates.sort(key=lambda c: c.daily_volume or 0, reverse=True)
        return candidates[:pool_size]

    async def _fetch_sector_stocks(self, sector: str, sector_name: str) -> list[StockCandidate]:
        """
        根据行业/概念爬取板块成分股

        数据源:
        - akshare.stock_board_industry_cons_em()  # 行业板块成分股
        - akshare.stock_board_concept_cons_em()   # 概念板块成分股
        - akshare.stock_sector_fund_flow_rank()   # 板块资金流向
        """
        # 行业名称映射到akshare板块名称
        sector_mapping = {
            "technology": "半导体", "软件服务", "通信设备", ...
            "finance": "银行", "证券", "保险", ...
            "healthcare": "医疗器械", "生物制品", "化学制药", ...
            # ... 更多映射
        }

        all_stocks = []
        for board_name in sector_mapping.get(sector, [sector_name]):
            try:
                df = ak.stock_board_industry_cons_em(symbol=board_name)
                for _, row in df.iterrows():
                    all_stocks.append(StockCandidate(
                        symbol=row["代码"],
                        name=row["名称"],
                        sector=sector,
                        asset_class="stock",
                        source=f"板块:{board_name}",
                    ))
            except Exception:
                continue

        return all_stocks

    async def _fetch_sector_etfs(self, sector: str, sector_name: str) -> list[StockCandidate]:
        """
        筛选与行业相关的ETF

        数据源:
        - akshare.fund_etf_category_sina()  # ETF分类列表
        - akshare.fund_etf_hist_em()        # ETF历史数据（计算规模/流动性）

        筛选条件:
        - 基金规模 > 2亿
        - 日均成交额 > 1000万
        - 跟踪误差 < 0.3%
        """
        # 获取所有ETF列表
        etf_list = ak.fund_etf_category_sina(symbol="ETF基金")

        # 根据行业关键词筛选
        sector_keywords = {
            "technology": ["科技", "半导体", "芯片", "5G", "AI", "人工智能"],
            "finance": ["银行", "金融", "证券", "保险"],
            "healthcare": ["医疗", "医药", "生物科技", "健康"],
            # ...
        }

        keywords = sector_keywords.get(sector, [sector_name])
        matched_etfs = []

        for _, etf in etf_list.iterrows():
            etf_name = etf.get("名称", "")
            if any(kw in etf_name for kw in keywords):
                # 获取ETF详细信息进行筛选
                symbol = etf.get("代码", "")
                # TODO: 获取规模、成交额、跟踪误差
                matched_etfs.append(StockCandidate(
                    symbol=symbol,
                    name=etf_name,
                    sector=sector,
                    asset_class="ETF",
                    source="ETF筛选",
                ))

        return matched_etfs

    async def _fetch_hot_stocks(self) -> list[StockCandidate]:
        """
        获取热门股补充

        数据源:
        - akshare.stock_zt_pool_em()          # 涨停池（排除）
        - akshare.stock_lhb_detail_daily_sina() # 龙虎榜
        - akshare.stock_sector_fund_flow_rank() # 板块资金流向
        """
        hot_stocks = []

        # 龙虎榜
        try:
            lhb = ak.stock_lhb_detail_daily_sina()
            for _, row in lhb.head(20).iterrows():
                hot_stocks.append(StockCandidate(
                    symbol=row["代码"],
                    name=row["名称"],
                    sector="hot",
                    asset_class="stock",
                    source="龙虎榜",
                ))
        except Exception:
            pass

        return hot_stocks
```

### 3.2 多维度筛选器 (Multi-Dimension Filter)

```python
# app/services/dynamic_picker/multi_dimension_filter.py

class MultiDimensionFilter:
    """多维度初筛，从候选池筛选出优质标的"""

    async def filter(
        self,
        candidates: list[StockCandidate],
        target_size: int = 50,
    ) -> list[StockCandidate]:
        """
        四维度筛选：基本面 + 技术面 + 资金面 + 控盘度
        """
        # 并行获取所有候选标的数据
        enriched = await self._enrich_candidates(candidates)

        # 逐层过滤
        after_fundamental = self._filter_fundamental(enriched)
        after_technical = self._filter_technical(after_fundamental)
        after_capital = self._filter_capital_flow(after_technical)
        after_control = self._filter_control_degree(after_capital)

        # 综合评分排序
        scored = self._calculate_composite_score(after_control)
        return scored[:target_size]

    def _filter_fundamental(self, candidates: list[EnrichedCandidate]) -> list[EnrichedCandidate]:
        """
        基本面筛选
        - ROE >= 8% (或行业前50%)
        - 毛利率 >= 15%
        - 净利率 >= 5%
        - 营收增速 >= 0% (非负增长)
        - PEG <= 3 (估值合理)
        - 排除ST/退市/停牌
        """
        filtered = []
        for c in candidates:
            f = c.fundamental
            if not f:
                continue
            if f.roe is not None and f.roe < 8:
                continue
            if f.gross_margin is not None and f.gross_margin < 15:
                continue
            if f.net_margin is not None and f.net_margin < 5:
                continue
            if f.revenue_growth is not None and f.revenue_growth < -10:
                continue
            if f.peg is not None and f.peg > 3:
                continue
            filtered.append(c)
        return filtered

    def _filter_technical(self, candidates: list[EnrichedCandidate]) -> list[EnrichedCandidate]:
        """
        技术面筛选
        - EMA20 >= EMA60 * 0.95 (趋势不恶化)
        - EMA60 >= EMA120 * 0.97 (中长期趋势)
        - 量能比 >= 0.5 (有成交)
        - 120日波动率 <= 前60% (不过度波动)
        - 排除涨停/跌停/异常波动
        - 3日涨幅 < 30% (排除短期暴涨)
        """
        filtered = []
        for c in candidates:
            t = c.technical
            if not t:
                continue
            if t.ema20 and t.ema60 and t.ema20 < t.ema60 * 0.95:
                continue
            if t.ema60 and t.ema120 and t.ema60 < t.ema120 * 0.97:
                continue
            if t.vol_ratio is not None and t.vol_ratio < 0.5:
                continue
            if t.volatility_120d is not None and t.volatility_120d_rank > 0.6:
                continue
            if t.latest_change and abs(t.latest_change) > 9.5:
                continue
            if t.surge_3d is not None and t.surge_3d > 30:
                continue
            filtered.append(c)
        return filtered

    def _filter_capital_flow(self, candidates: list[EnrichedCandidate]) -> list[EnrichedCandidate]:
        """
        资金面筛选
        - 近5日主力净流入 > 0 (资金流入)
        - 融资余额变化率 >= -5% (杠杆资金未大幅撤离)
        - 北向资金近5日净流入 >= 0 (外资未撤离)
        """
        filtered = []
        for c in candidates:
            cf = c.capital_flow
            if not cf:
                continue
            if cf.main_net_inflow_5d is not None and cf.main_net_inflow_5d < 0:
                continue
            if cf.margin_change_rate is not None and cf.margin_change_rate < -5:
                continue
            if cf.northbound_net_5d is not None and cf.northbound_net_5d < 0:
                continue
            filtered.append(c)
        return filtered

    def _filter_control_degree(self, candidates: list[EnrichedCandidate]) -> list[EnrichedCandidate]:
        """
        控盘程度筛选
        - 筹码集中度 >= 适中 (非过度分散)
        - 股东户数变化率 <= 10% (未大量散户涌入)
        - 机构持仓比例 >= 20% (有机构关注)
        """
        filtered = []
        for c in candidates:
            cd = c.control_degree
            if not cd:
                continue
            if cd.chip_concentration is not None and cd.chip_concentration < 30:
                continue
            if cd.shareholder_change_rate is not None and cd.shareholder_change_rate > 15:
                continue
            if cd.institution_hold_ratio is not None and cd.institution_hold_ratio < 15:
                continue
            filtered.append(c)
        return filtered

    def _calculate_composite_score(self, candidates: list[EnrichedCandidate]) -> list[EnrichedCandidate]:
        """
        综合评分 = 基本面×0.3 + 技术面×0.25 + 资金面×0.25 + 控盘度×0.2
        """
        for c in candidates:
            scores = []
            weights = []

            if c.fundamental:
                scores.append(c.fundamental.score)
                weights.append(0.30)
            if c.technical:
                scores.append(c.technical.score)
                weights.append(0.25)
            if c.capital_flow:
                scores.append(c.capital_flow.score)
                weights.append(0.25)
            if c.control_degree:
                scores.append(c.control_degree.score)
                weights.append(0.20)

            if scores:
                total_weight = sum(weights)
                c.composite_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
            else:
                c.composite_score = 0.5

        return sorted(candidates, key=lambda c: c.composite_score, reverse=True)
```

### 3.3 RAG+LLM 精选器 (RAG LLM Selector)

```python
# app/services/dynamic_picker/rag_llm_selector.py

class RAGLLMSelector:
    """RAG+LLM做最终挑选和监督"""

    def __init__(self, rag_service, llm_service):
        self.rag = rag_service
        self.llm = llm_service

    async def select(
        self,
        candidates: list[EnrichedCandidate],
        top_sectors: list[dict],
        market_cycle: str,
        target_count: int = 10,
    ) -> list[SelectedStock]:
        """
        RAG+LLM精选流程:
        1. 为每只候选标的构建数据画像
        2. RAG检索相似历史案例和研报
        3. LLM综合评估给出评分和理由
        4. 监督审核（同质化/集中度/风格漂移）
        """
        # 1. 构建标的画像
        profiles = [self._build_stock_profile(c) for c in candidates]

        # 2. RAG检索（并行）
        rag_results = await asyncio.gather(*[
            self._rag_retrieve(profile) for profile in profiles
        ])

        # 3. LLM评估（批量）
        llm_evaluations = await self._llm_evaluate_batch(
            profiles, rag_results, market_cycle
        )

        # 4. 监督审核
        selected = self._supervision_check(
            candidates, llm_evaluations, top_sectors, target_count
        )

        return selected

    def _build_stock_profile(self, candidate: EnrichedCandidate) -> str:
        """构建标的文字画像，用于RAG检索和LLM评估"""
        parts = [
            f"标的: {candidate.name}({candidate.symbol})",
            f"行业: {candidate.sector}",
            f"类型: {candidate.asset_class}",
        ]

        if candidate.fundamental:
            f = candidate.fundamental
            parts.append(
                f"基本面: ROE={f.roe:.1f}% 毛利率={f.gross_margin:.1f}% "
                f"净利率={f.net_margin:.1f}% 营收增速={f.revenue_growth:.1f}% PEG={f.peg:.2f}"
            )

        if candidate.technical:
            t = candidate.technical
            parts.append(
                f"技术面: EMA20={t.ema20:.2f} EMA60={t.ema60:.2f} "
                f"量能比={t.vol_ratio:.2f} 120日波动率排名={t.volatility_120d_rank:.1%} "
                f"最新涨幅={t.latest_change:.2f}%"
            )

        if candidate.capital_flow:
            cf = candidate.capital_flow
            parts.append(
                f"资金面: 5日主力净流入={cf.main_net_inflow_5d/1e8:.2f}亿 "
                f"融资变化={cf.margin_change_rate:.1f}% 北向5日={cf.northbound_net_5d/1e8:.2f}亿"
            )

        if candidate.control_degree:
            cd = candidate.control_degree
            parts.append(
                f"控盘度: 筹码集中度={cd.chip_concentration:.1f}% "
                f"股东户数变化={cd.shareholder_change_rate:.1f}% 机构持仓={cd.institution_hold_ratio:.1f}%"
            )

        return "\n".join(parts)

    async def _rag_retrieve(self, profile: str) -> dict:
        """RAG检索：相似历史行情、行业研报、公司公告"""
        # 检索相似历史案例
        similar_cases = await self.rag.similarity_search(
            query=profile,
            filter={"type": "historical_pattern"},
            top_k=3,
        )

        # 检索行业研报
        research_reports = await self.rag.similarity_search(
            query=profile,
            filter={"type": "research_report"},
            top_k=2,
        )

        # 检索公司公告
        announcements = await self.rag.similarity_search(
            query=profile,
            filter={"type": "announcement"},
            top_k=2,
        )

        return {
            "similar_cases": similar_cases,
            "research_reports": research_reports,
            "announcements": announcements,
        }

    async def _llm_evaluate_batch(
        self,
        profiles: list[str],
        rag_results: list[dict],
        market_cycle: str,
    ) -> list[dict]:
        """批量LLM评估"""
        evaluations = []

        for profile, rag in zip(profiles, rag_results):
            prompt = f"""你是一位资深量化选股分析师。请根据以下标的画像和RAG检索结果，给出综合评估。

市场周期: {market_cycle}

标的画像:
{profile}

RAG检索结果:
相似历史案例:
{self._format_rag_results(rag["similar_cases"])}

行业研报摘要:
{self._format_rag_results(rag["research_reports"])}

公司公告摘要:
{self._format_rag_results(rag["announcements"])}

请输出JSON格式:
{{
    "score": 0-100的综合评分,
    "confidence": "high|medium|low",
    "reasoning": "选股理由，100字以内",
    "risks": ["风险1", "风险2"],
    "recommendation": "strong_buy|buy|hold|avoid"
}}
"""
            result = await self.llm.generate_json(prompt)
            evaluations.append(result)

        return evaluations

    def _supervision_check(
        self,
        candidates: list[EnrichedCandidate],
        evaluations: list[dict],
        top_sectors: list[dict],
        target_count: int,
    ) -> list[SelectedStock]:
        """
        监督审核：
        1. 同质化检查：同一行业标的不超过3只
        2. 集中度检查：单只标的权重不超过20%
        3. 风格漂移检查：ETF和个股比例符合SAA配置
        4. 质量门槛：LLM评分 >= 60分
        """
        # 按LLM评分排序
        scored = list(zip(candidates, evaluations))
        scored.sort(key=lambda x: x[1].get("score", 0), reverse=True)

        selected = []
        sector_counts = defaultdict(int)
        etf_count = 0
        stock_count = 0

        for candidate, eval_result in scored:
            # 质量门槛
            if eval_result.get("score", 0) < 60:
                continue

            # 同质化检查
            if sector_counts[candidate.sector] >= 3:
                continue

            # 风格漂移检查：ETF:个股 ≈ 7:3
            if candidate.asset_class == "ETF" and etf_count >= target_count * 0.7:
                continue
            if candidate.asset_class == "stock" and stock_count >= target_count * 0.4:
                continue

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
                data_sources=candidate.data_sources,
            ))

            sector_counts[candidate.sector] += 1
            if candidate.asset_class == "ETF":
                etf_count += 1
            else:
                stock_count += 1

            if len(selected) >= target_count:
                break

        return selected
```

### 3.4 数据模型

```python
# app/services/dynamic_picker/models.py

from dataclasses import dataclass, field
from typing import Optional

@dataclass
class StockCandidate:
    """候选标的（原始）"""
    symbol: str
    name: str
    sector: str
    asset_class: str  # "stock" | "ETF"
    source: str  # 数据来源说明
    daily_volume: Optional[float] = None  # 日均成交额

@dataclass
class FundamentalMetrics:
    """基本面指标"""
    roe: Optional[float] = None  # 净资产收益率 %
    gross_margin: Optional[float] = None  # 毛利率 %
    net_margin: Optional[float] = None  # 净利率 %
    revenue_growth: Optional[float] = None  # 营收增速 %
    peg: Optional[float] = None  # PEG比率
    score: float = 0.5  # 0-1评分

@dataclass
class TechnicalMetrics:
    """技术面指标"""
    ema20: Optional[float] = None
    ema60: Optional[float] = None
    ema120: Optional[float] = None
    vol_ratio: Optional[float] = None  # 量能比
    volatility_120d: Optional[float] = None  # 120日波动率
    volatility_120d_rank: float = 0.5  # 波动率排名 (0-1)
    latest_change: Optional[float] = None  # 最新涨幅 %
    surge_3d: Optional[float] = None  # 3日涨幅 %
    score: float = 0.5

@dataclass
class CapitalFlowMetrics:
    """资金面指标"""
    main_net_inflow_5d: Optional[float] = None  # 主力净流入（元）
    margin_change_rate: Optional[float] = None  # 融资余额变化率 %
    northbound_net_5d: Optional[float] = None  # 北向5日净流入（元）
    score: float = 0.5

@dataclass
class ControlDegreeMetrics:
    """控盘程度指标"""
    chip_concentration: Optional[float] = None  # 筹码集中度 %
    shareholder_change_rate: Optional[float] = None  # 股东户数变化率 %
    institution_hold_ratio: Optional[float] = None  # 机构持仓比例 %
    score: float = 0.5

@dataclass
class EnrichedCandidate(StockCandidate):
    """ enriched候选标的（含多维度数据）"""
    fundamental: Optional[FundamentalMetrics] = None
    technical: Optional[TechnicalMetrics] = None
    capital_flow: Optional[CapitalFlowMetrics] = None
    control_degree: Optional[ControlDegreeMetrics] = None
    composite_score: float = 0.5
    data_sources: list[str] = field(default_factory=list)

@dataclass
class SelectedStock:
    """最终选中的标的"""
    symbol: str
    name: str
    sector: str
    asset_class: str
    composite_score: float  # 多维度综合评分
    llm_score: float  # LLM评分 0-100
    llm_confidence: str  # high|medium|low
    reasoning: str  # 选股理由
    risks: list[str]  # 风险列表
    recommendation: str  # strong_buy|buy|hold|avoid
    data_sources: list[str]  # 数据来源追溯
```

---

## 4. 与Hybrid引擎的集成

### 4.1 替换原有的静态映射

```python
# hybrid_portfolio_designer_v2.py 修改点

# 原代码（静态映射）:
# etf_info = get_sector_etf(sector_info["sector"])
# stocks = get_sector_stocks(sector_info["sector"], n=1)

# 新代码（动态选股）:
from app.services.dynamic_picker import PoolBuilder, MultiDimensionFilter, RAGLLMSelector

async def _dynamic_stock_selection(
    self,
    top_sectors: list[dict],
    market_cycle: str,
    industry_scores: dict,
    social_trends: list[str],
) -> list[SelectedStock]:
    """动态选股替代静态映射"""

    # Step 1: 构建标的池
    builder = PoolBuilder()
    raw_pool = await builder.build_pool(
        top_sectors=top_sectors,
        market_cycle=market_cycle,
        industry_scores=industry_scores,
        social_trends=social_trends,
        pool_size=200,
    )

    # Step 2: 多维度初筛
    filter_engine = MultiDimensionFilter()
    filtered_pool = await filter_engine.filter(raw_pool, target_size=50)

    # Step 3: RAG+LLM精选
    selector = RAGLLMSelector(rag_service=self.rag, llm_service=self.llm)
    selected = await selector.select(
        candidates=filtered_pool,
        top_sectors=top_sectors,
        market_cycle=market_cycle,
        target_count=15,  # 预留一些给后续排除
    )

    return selected

# 在策略-标的绑定步骤中使用:
async def step3_strategy_binding(self, ...):
    # 动态选股
    selected_stocks = await self._dynamic_stock_selection(...)

    # 绑定逻辑：从selected_stocks中筛选ETF和个股
    for sector_info in top_sectors:
        sector = sector_info["sector"]

        # 主仓位：该行业的ETF（按LLM评分选最优）
        sector_etfs = [s for s in selected_stocks if s.sector == sector and s.asset_class == "ETF"]
        if sector_etfs:
            best_etf = max(sector_etfs, key=lambda s: s.llm_score)
            bindings.append({
                "symbol": best_etf.symbol,
                "name": best_etf.name,
                "asset_class": "ETF",
                "llm_score": best_etf.llm_score,
                "reasoning": best_etf.reasoning,
                ...
            })

        # 卫星仓位：该行业的个股（权重大于15%时）
        if sector_info["weight"] > 0.15:
            sector_stocks = [s for s in selected_stocks if s.sector == sector and s.asset_class == "stock"]
            if sector_stocks:
                best_stock = max(sector_stocks, key=lambda s: s.llm_score)
                bindings.append({
                    "symbol": best_stock.symbol,
                    "name": best_stock.name,
                    "asset_class": "stock",
                    "weight": sector_info["weight"] * 0.3,
                    "llm_score": best_stock.llm_score,
                    "reasoning": best_stock.reasoning,
                    ...
                })
```

### 4.2 数据溯源

每个选中的标的都包含完整的 `data_sources` 字段：

```python
{
    "symbol": "688981",
    "name": "中芯国际",
    "data_sources": [
        "板块成分股: 半导体 (akshare.stock_board_industry_cons_em)",
        "基本面: ROE/毛利率/净利率 (akshare.stock_yjbb_em)",
        "技术面: EMA/量能/波动率 (akshare.stock_zh_a_hist)",
        "资金面: 主力净流入/融资融券 (akshare.stock_individual_fund_flow)",
        "控盘度: 筹码集中度/机构持仓 (akshare.stock_institute_hold_detail)",
        "RAG检索: 相似历史案例/研报/公告",
        "LLM评估: 综合评分和选股理由"
    ]
}
```

---

## 5. 数据源清单

| 维度 | 数据项 | akshare接口 | 说明 |
|------|--------|-------------|------|
| **板块成分股** | 行业板块成分股 | `stock_board_industry_cons_em` | 东方财富行业板块 |
| | 概念板块成分股 | `stock_board_concept_cons_em` | 概念板块 |
| | 板块资金流向 | `stock_sector_fund_flow_rank` | 板块资金排名 |
| **ETF筛选** | ETF分类列表 | `fund_etf_category_sina` | 新浪ETF分类 |
| | ETF历史数据 | `fund_etf_hist_em` | 计算规模/流动性 |
| **基本面** | 业绩快报 | `stock_yjbb_em` | ROE/毛利率/净利率 |
| | 财务指标 | `stock_financial_analysis_em` | 更多财务数据 |
| **技术面** | A股历史数据 | `stock_zh_a_hist` | EMA/波动率/涨幅 |
| | 实时行情 | `stock_zh_a_spot` | 最新价格/涨幅 |
| **资金面** | 个股资金流向 | `stock_individual_fund_flow` | 主力净流入 |
| | 融资融券 | `stock_margin_detail_em` | 融资余额变化 |
| | 北向资金 | `stock_hsgt_hist_em` | 沪深港通资金流向 |
| **控盘度** | 机构持仓 | `stock_institute_hold_detail` | 机构持仓比例 |
| | 股东户数 | `stock_gdfx_free_holding_detail_em` | 股东户数变化 |
| | 筹码分布 | `stock_cyq_em` | 筹码集中度 |
| **热门股** | 龙虎榜 | `stock_lhb_detail_daily_sina` | 每日龙虎榜 |
| | 涨停池 | `stock_zt_pool_em` | 涨停股票（排除用） |

---

## 6. 实现计划

### Phase 1: 基础数据结构 (1天)
- [ ] 创建 `app/services/dynamic_picker/` 包
- [ ] 定义数据模型 (`models.py`)
- [ ] 创建 `__init__.py` 导出

### Phase 2: 标的池构建器 (2天)
- [ ] 实现 `PoolBuilder`
- [ ] 板块成分股爬取
- [ ] ETF筛选逻辑
- [ ] 热门股补充
- [ ] 单元测试

### Phase 3: 多维度筛选器 (2天)
- [ ] 实现 `MultiDimensionFilter`
- [ ] 基本面筛选
- [ ] 技术面筛选
- [ ] 资金面筛选
- [ ] 控盘度筛选
- [ ] 综合评分
- [ ] 单元测试

### Phase 4: RAG+LLM精选器 (2天)
- [ ] 实现 `RAGLLMSelector`
- [ ] 标的画像构建
- [ ] RAG检索集成
- [ ] LLM评估提示词优化
- [ ] 监督审核逻辑
- [ ] 单元测试

### Phase 5: Hybrid引擎集成 (1天)
- [ ] 修改 `hybrid_portfolio_designer_v2.py`
- [ ] 替换静态映射为动态选股
- [ ] 更新绑定逻辑
- [ ] 数据溯源字段
- [ ] 集成测试

### Phase 6: 性能优化 (1天)
- [ ] 并行数据获取
- [ ] 缓存优化
- [ ] 超时处理
- [ ] 降级策略

**总计: 约9天**

---

## 7. 降级策略

当动态选股失败时，回退到静态映射：

```python
async def select_stocks_with_fallback(...):
    try:
        return await dynamic_selector.select(...)
    except Exception as e:
        logger.warning(f"动态选股失败，回退到静态映射: {e}")
        return static_symbol_mappings.get_fallback_stocks(top_sectors)
```

---

## 8. 与现有系统的对比

| 维度 | 原方案 (静态映射) | 新方案 (动态选股) |
|------|------------------|------------------|
| **标的来源** | 预定义ETF+龙头股 (30只) | 实时爬取板块成分股 (100~300只) |
| **选股逻辑** | 行业映射 | 基本面+技术面+资金面+控盘度 |
| **ETF选择** | 固定1只/行业 | 按规模/流动性/跟踪误差筛选 |
| **个股选择** | 固定2只/行业 | 多维度评分+LLM精选 |
| **时效性** | 静态 | 实时 |
| **透明度** | 映射表 | 完整数据溯源 |
| **RAG+LLM** | 仅质检 | 选股+质检 |
| **计算成本** | 低 | 中 (可优化) |
| **可靠性** | 高 | 中 (有降级策略) |

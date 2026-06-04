# 后端待办清单

**日期**: 2026-06-04
**状态**: 前端已完成，后端待实现

---

## 一、已完成的前端页面

| 页面 | 状态 | 说明 |
|------|------|------|
| HomeView.vue | ✅ | 首页双状态（空状态/Dashboard） |
| ProfileWizard.vue | ✅ | 15题问卷向导 |
| ProfileResult.vue | ✅ | 画像结果展示 |
| MarketSignalView.vue | ✅ | 五层市场信号展示 |
| PortfolioBuilder.vue | ✅ | 组合构建器 |
| StrategyRecommendation.vue | ✅ | 策略推荐 |
| LifespanCenter.vue | ✅ | 寿命监控中心 |
| BacktestCenter.vue | ✅ | 回测中心 |
| BacktestDetail.vue | ✅ | 回测详情 |
| **TodayOperation.vue** | ✅ **新增** | 今日操作（买入/卖出/持有信号+一键确认） |
| **WeeklyReport.vue** | ✅ **新增** | 周报（组合表现/市场回顾/下周展望） |
| OnboardingGuide.vue | ✅ | 新用户引导（4步） |
| **AlertBar.vue** | ✅ **新增** | 告警条（寿命预警/周期切换/偏离度） |
| **NotificationBadge.vue** | ✅ **新增** | 通知角标（下拉通知列表+已读管理） |

**前端 API 客户端**:
- `fullchain.ts` ✅ — 封装所有 Phase D 接口

---

## 二、已完成的后端服务（Phase D）

| 服务 | 文件 | 功能 |
|------|------|------|
| 教学引导 | `onboarding_service.py` | 4步教学引导内容生成 |
| 建仓助手 | `building_service.py` | 分批建仓计划+金额计算 |
| 推送系统 | `push_service.py` | 今日操作/寿命预警/周期切换 |
| 调仓提醒 | `rebalance_service.py` | 5种触发检测+替代策略推荐 |
| 周报生成 | `weekly_report.py` | 组合表现+市场回顾+下周展望 |

**API 端点**:
- `fullchain.py` ✅ — 11个全链路服务接口

---

## 三、待实现的后端模块

### 3.1 RAG 模块（最高优先级）

**设计文档**: `docs/rag-module-design.md`

| 子模块 | 文件 | 功能 | 依赖 |
|--------|------|------|------|
| 知识库管理 | `services/rag/knowledge_base.py` | 论文/案例/规则库管理 | sentence-transformers, chromadb |
| 检索引擎 | `services/rag/retrieval_engine.py` | 向量检索+结构化过滤+混合排序 | chromadb |
| LLM 客户端 | `services/rag/llm_client.py` | 本地 Qwen3-14B-MLX-4bit 调用 | mlx-lm |
| Prompt 构建 | `services/rag/prompt_builder.py` | 三阶段各自的 prompt 模板 | - |
| 输出解析 | `services/rag/output_parser.py` | JSON 提取和验证 | - |
| 硬指标检查 | `services/rag/hard_metrics.py` | 选股/组合/策略硬指标 | - |
| **主类** | `services/rag/advisor.py` | RAGInvestmentAdvisor 对外接口 | 以上全部 |

**实现步骤**:
1. 初始化 Chroma 向量库
2. 加载现有论文数据到向量库
3. 实现检索引擎（向量+结构化+关键词）
4. 实现 LLM 客户端（封装 mlx-lm）
5. 实现硬指标检查
6. 实现 Prompt 构建和输出解析
7. 组装 RAGInvestmentAdvisor 主类
8. 测试端到端流程

### 3.2 静态选股器（RAG 驱动）

**设计文档**: `docs/architecture-v3-rag-driven.md` 第3.1节

| 子模块 | 文件 | 功能 |
|--------|------|------|
| 硬过滤 | `services/static_stock_picker.py` | 排除ST/流动性/估值过滤 |
| 画像匹配 | `services/static_stock_picker.py` | 风险等级→波动率筛选 |
| 周期匹配 | `services/static_stock_picker.py` | 市场周期→风格偏好 |
| 多因子评分 | `services/static_stock_picker.py` | 质量/估值/动量/低波 |
| **RAG 监督** | `services/rag/advisor.py` | 评估+微调循环 |

**硬指标门槛**:
- 股票数量 ≥ 30
- 行业集中度 ≤ 25%
- 平均 ROE ≥ 10%
- 与画像风险等级匹配

### 3.3 资产组合器（RAG 驱动）

**设计文档**: `docs/architecture-v3-rag-driven.md` 第3.2节

| 子模块 | 文件 | 功能 |
|--------|------|------|
| SAA | `services/portfolio_builder.py` | 战略资产配置 |
| TAA | `services/portfolio_builder.py` | 战术行业配置 |
| 个股精选 | `services/portfolio_builder.py` | 从候选中选20-30只 |
| 权重优化 | `services/portfolio_builder.py` | 等权/风险平价 |
| **RAG 监督** | `services/rag/advisor.py` | 评估+微调循环 |

**硬指标门槛**:
- 权重和 = 100%
- 单只 ≤ 15%（稳健型）
- 行业集中度 ≤ 30%
- 夏普比率 > 0.3

### 3.4 策略绑定器（RAG 驱动）

**设计文档**: `docs/architecture-v3-rag-driven.md` 第3.3节

| 子模块 | 文件 | 功能 |
|--------|------|------|
| 特征分析 | `services/strategy_binder.py` | 波动率/趋势/估值/行业/市值 |
| 类型匹配 | `services/strategy_binder.py` | 高波动→趋势跟踪，低波动→均值回归 |
| 参数优化 | `services/strategy_binder.py` | 贝叶斯优化/网格搜索 |
| **RAG 监督** | `services/rag/advisor.py` | 评估+微调循环 |

**硬指标门槛**:
- 策略-特征匹配度 > 70%
- 回测胜率 > 40%
- 止损线在 2%-15%
- 策略类型多样性 ≥ 3种

### 3.5 组合寿命系统

**设计文档**: `docs/portfolio-lifespan-design.md`

| 子模块 | 文件 | 功能 |
|--------|------|------|
| 配置有效性 | `services/portfolio_lifespan.py` | 周期匹配度+切换概率 |
| 选股新鲜度 | `services/portfolio_lifespan.py` | 时间衰减+基本面漂移+估值变化 |
| 策略有效性 | `services/portfolio_lifespan.py` | 近期胜率+市场匹配+回撤控制 |
| 寿命聚合 | `services/portfolio_lifespan.py` | 三维加权+短板效应 |
| 动态更新 | `services/portfolio_lifespan.py` | 波动率/周期/拥挤度加速因子 |
| 预警推送 | `services/portfolio_lifespan.py` | 三级预警+调仓建议 |

**公式**:
```
组合寿命 = min(配置寿命×0.4, 选股寿命×0.3, 策略寿命×0.3)
```

### 3.6 模型下载

| 模型 | 状态 | 说明 |
|------|------|------|
| Qwen3-14B-MLX-4bit | ❌ 失败 | 网络问题，需配置代理或 HF_TOKEN |
| sentence-transformers | ✅ 已安装 | all-MiniLM-L6-v2 |
| chromadb | ✅ 已安装 | 本地向量库 |
| mlx-lm | ✅ 已安装 | MLX 推理框架 |

---

## 四、实施优先级

| 优先级 | 模块 | 预计时间 | 阻塞项 |
|--------|------|---------|--------|
| P0 | 下载 Qwen3-14B-MLX-4bit | 30分钟 | 网络/代理/HF_TOKEN |
| P0 | RAG 模块核心 | 2-3天 | 模型下载 |
| P0 | 静态选股器 | 1-2天 | RAG 模块 |
| P1 | 资产组合器 | 1-2天 | 选股器 |
| P1 | 策略绑定器 | 1-2天 | 组合器 |
| P2 | 组合寿命系统 | 1天 | 策略绑定器 |
| P2 | 集成测试 | 1天 | 全部 |

---

## 五、已知问题

1. **模型下载失败** — Hugging Face 连接问题，需配置代理或 HF_TOKEN
2. **Python 3.13** — 部分包可能不兼容（目前 mlx-lm 安装成功）
3. **16GB 内存** — 跑 14B-4bit 约需 8GB，余量紧张

---

## 六、下一步行动

1. 配置 Hugging Face 代理或 Token
2. 重新下载 Qwen3-14B-MLX-4bit
3. 实现 RAG 模块核心代码
4. 测试 RAG 端到端流程

# RAG 接入 Hybrid 组合引擎 — 使用文档

## 概述

RAG投资顾问已接入Hybrid组合引擎，作为"质量总监"在每个阶段间进行控制、把关和调节。

## 核心特性

### 1. 6个质检点

| 质检点 | 功能 | 严格程度 |
|--------|------|---------|
| SAA审核 | 结合市场信号微调资产配置 | 市场驱动 |
| TAA审核 | 行业集中度、风格平衡 | 标准 |
| 绑定审核 | 回测验证（必须跑赢买入持有） | 严格 |
| 风控审核 | 止损线、仓位上限匹配画像 | 标准 |
| 可靠性审核 | 组合必须跑赢买入持有 | 最严格（不降低标准） |
| 最终审核 | 画像匹配度、可执行性 | 标准 |

### 2. 调节机制

- **SAA**：权重截断、增配避险资产
- **TAA**：行业分散、风格平衡
- **绑定**：调参、换策略、换标的、排除
- **风控**：止损线校准、仓位调整
- **可靠性**：调参、换策略、重建（不降低标准）

### 3. 重试机制

| 步骤 | 最大重试次数 |
|------|-------------|
| SAA | 2次 |
| TAA | 2次 |
| 绑定 | 3次 |
| 风控 | 2次 |
| 可靠性 | 5次（严格） |
| 最终 | 1次 |

## API使用

### 设计组合（带RAG质检）

```bash
POST /api/v1/portfolios/design-with-rag
```

请求体：
```json
{
  "profile_vector": {
    "risk_tolerance": 0.5,
    "loss_aversion": 0.5,
    "time_horizon": "long"
  },
  "market_signal": {
    "macro_score": 0.7,
    "geo_risk": 0.3,
    "market_internal": {
      "vix": 20,
      "equity_bond_spread": 4.0
    }
  },
  "use_rag_gate": true
}
```

响应：
```json
{
  "success": true,
  "portfolio": {...},
  "rag_reviews": [
    {
      "step": "saa",
      "passed": false,
      "score": 0.6,
      "issues": ["股票权重过高"],
      "adjustments": [{"type": "weight_cap", "asset": "stock", "cap": 0.7}],
      "theory_cited": ["theory_markowitz"]
    }
  ],
  "rag_adjusted": true,
  "rag_adjustment_count": 1
}
```

### 设计组合（不带RAG质检）

```bash
POST /api/v1/portfolios/design-with-rag
```

```json
{
  "profile_vector": {...},
  "market_signal": {...},
  "use_rag_gate": false
}
```

## 知识库

### 新增案例库

| 知识库 | 数量 | 用途 |
|--------|------|------|
| 资产配置案例 | 16 | 4画像×4周期的配置方案 |
| 风控案例 | 8 | 止损线、仓位、回撤设置 |
| 策略绑定案例 | 8 | 成功/失败经验教训 |

### 索引统计

| 索引 | 数量 |
|------|------|
| 个股案例 | 16 |
| 资产配置理论 | 10 |
| 基础常识 | 20 |
| 估值案例 | 20 |
| 行为金融 | 15 |
| 论文片段 | 20 |
| **资产配置案例** | **16** |
| **风控案例** | **8** |
| **策略绑定案例** | **8** |
| **总计** | **131** |

## 文件清单

### 新增文件

```
backend/app/services/rag/
├── portfolio_quality_gate.py    # RAG质检服务
├── adjustment_engine.py         # 调节引擎

backend/app/services/
├── hybrid_portfolio_designer_v2.py  # 集成RAG的Hybrid引擎

backend/data/knowledge/
├── allocation_cases/            # 16种配置案例
├── risk_control_cases/          # 8种风控案例
└── strategy_binding_cases/      # 8种绑定案例

backend/tests/
├── test_rag_quality_gate.py     # 单元测试（13用例）
└── test_rag_hybrid_integration.py  # 集成测试（12用例）
```

### 修改文件

```
backend/app/services/rag/
├── __init__.py                  # 新增导出
├── index_builder_v2.py          # 支持新目录
└── vector_store.py              # 修复索引加载bug

backend/app/api/v1/endpoints/
└── portfolios.py                # 新增/design-with-rag端点

backend/app/services/
└── saa_engine.py                # 修复time_horizon字符串处理
```

## 测试

### 运行单元测试

```bash
cd backend
pytest tests/test_rag_quality_gate.py -v
```

### 运行集成测试

```bash
cd backend
pytest tests/test_rag_hybrid_integration.py -v
```

### 测试覆盖

- RAGGateResult数据类
- SAA权重截断/增配避险
- 绑定参数调整/排除
- 风控止损调整
- 完整调节流程
- 保守型+熊市组合
- 积极型+牛市组合
- 极端画像测试
- 空策略池测试

## 注意事项

1. **RAG质检需要LLM服务**：当前使用mock模式，生产环境需配置真实LLM
2. **回测验证**：绑定审核需要真实的回测服务，当前为模拟数据
3. **性能**：RAG质检会增加组合生成时间（约+200-500ms/质检点）
4. **知识库更新**：新增案例后需要重建索引

## 后续优化

- [ ] 接入真实LLM（Qwen3-14B-MLX）
- [ ] 接入真实回测服务
- [ ] 前端展示RAG质检记录
- [ ] 知识库持续扩充
- [ ] 调节阈值基于实盘数据校准

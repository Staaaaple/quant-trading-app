# QuantEvo — 策略即有机体的量化投资平台

> **项目名称**: QuantEvo（原 Quant Trading App）  
> **版本**: v2.0  
> **更新日期**: 2026-06-11

一个将**策略视为有机体**的量化投资平台。不只是回测和交易，QuantEvo 用生物学的视角审视你的策略群落——测序它们的基因、追踪它们的家族、测量它们的代谢、预测它们的寿命。

> "策略不是代码，是生态。"

---

## 项目特点

### 策略生态系统（Strategy Ecosystem）

平台的核心创新是将每个交易策略视为一个**活的有机体**，从四个生物学维度进行全生命周期分析：

#### 🧬 DNA 测序
通过 AST 静态解析 + 关键词模式匹配，自动提取策略的四层基因结构：
- **特征层**：技术指标（MA、MACD、RSI、布林带等）
- **信号层**：交易逻辑类型（趋势跟踪、均值回归、动量突破等）
- **风控层**：止损、仓位管理、回撤控制
- **执行层**：市价单、限价单、目标仓位

输出：基因多样性分数、健康出生分数、近亲系数、32 维基因向量

#### 🌳 系统发育（Phylogeny）
基于 32 维基因向量的余弦相似度，自动为策略聚类分家族：
- 识别策略间的亲缘关系
- 构建策略家族关系网络图
- **近亲繁殖预警**：当新策略与已有策略相似度过高时发出警告
- 同质性风险量化

#### 🔥 代谢分析
衡量策略对数据环境的依赖程度：
- **信息代谢率**：策略每天需要处理的信息量（K 线/数据更新频率）
- **生态位宽度**：策略适用的市场场景广度
- **代谢综合征**：数据饥渴风险，过度依赖实时数据会导致策略脆弱

#### ⏳ 寿命预测
综合代谢率、生态位宽度、同质性风险，预测策略的有效剩余寿命：
- 年轻期（36+ 月）、成熟期（12-36 月）、衰老期（3-12 月）、濒危（<3 月）
- 月老化速度追踪
- 个性化优化建议

> 生态系统在首页以可视化仪表盘呈现，单策略详情在基因报告页展示。

---

## 核心功能

### 策略工坊（Strategy Workshop）
策略中枢，包含四个子页面：

- **选股策略（Picker）**：基于 akshare 获取 A 股数据，编写自定义选股逻辑；内置每周五自动运行的量价活跃选股策略
- **交易策略（Trade）**：在线编写 Python 量化策略，内置 CodeMirror 编辑器 + 内嵌 API 参考面板，基于 akquant 框架
- **风控策略（Risk）**：A+B 混合模式——Python 代码扩展（`risk_check(context)`）+ 表单化规则配置（仓位上限、日最大回撤、黑名单）
- **策略流（Flow）**：将选股、风控、交易策略强绑定为流水线。回测/模拟盘运行时自动完成选股 → 风控 → 交易的执行链路

### 回测中心（Backtest Center）
- 策略/策略流回测，调用 akquant 引擎执行
- **基准对比**：每个回测自动运行买入持有（Buy & Hold）基准对照组，详情页可查看策略 vs 基准的 11 项指标对比及超额收益
- **回测详情页**：点击任意回测记录可进入详情页，查看完整指标对比、策略生态快照（健康度/代谢/寿命/家族）及运行日志
- 策略流回测：自动执行选股节点 → 交易节点；选股为空则终止并提示

### 模拟盘监控（Paper Trading Monitor）
- akquant Paper Trading 模式运行策略/策略流
- 实时展示模拟持仓、盈亏与交易信号
- 支持策略流自动执行：选股 → 风控参数注入 → 交易

### 真实持仓同步（Real Position Sync）
- **双账本并行**：模拟账本（akquant）+ 真实账本（独立维护）
- 一键同步券商真实成交数据
- 收盘自动对账，生成差异清单
- 表结构兼容未来 MiniQMT Gateway 自动接入

> 详细设计见 [docs/sync-scheme.md](./docs/sync-scheme.md)

### 投资者画像 & 智能组合（v2.0 新增）
- **15 题问卷**：风险承受能力、投资经验、收益预期、行为偏好
- **五层市场评估**：估值面、技术面、情绪面、宏观面、资金流向
- **Hybrid 组合引擎**：SAA 战略配置 + TAA 战术调整，生成个性化投资组合
- **全链路服务**：画像 → 市场信号 → 组合推荐 → 回测验证 → 今日操作

### RAG 知识库（v2.0 新增）
- **论文知识库**：量化投资经典论文结构化存储
- **策略模板库**：内置双均线、RSI、布林带等核心模板
- **向量检索**：基于 FAISS + Sentence Transformers 的语义搜索
- **智能问答**：结合本地 LLM 的投资知识问答

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Vue 3 + Vite + TypeScript + Pinia + Vue Router + ECharts + Vue I18n + CodeMirror + Tailwind CSS |
| **后端** | FastAPI + SQLAlchemy + SQLite + APScheduler + Pydantic |
| **量化引擎** | [akquant](https://github.com/akfamily/akquant)（回测/模拟盘）+ [akshare](https://www.akshare.xyz/)（数据获取）|
| **本地 LLM** | [MLX](https://github.com/ml-explore/mlx) + [Qwen3-14B-MLX-4bit](https://huggingface.co/Qwen/Qwen3-14B-MLX-4bit)（Apple Silicon）|
| **向量检索** | FAISS + Sentence Transformers |
| **测试** | pytest + httpx |

---

## 项目结构

```
quant-trading-app/
├── frontend/              # Vue 3 前端
│   ├── src/
│   │   ├── api/           # 后端 API 封装
│   │   ├── components/    # 公共组件
│   │   ├── i18n/          # 国际化（中/英/日）
│   │   ├── router/        # 路由配置
│   │   ├── stores/        # Pinia 状态管理
│   │   ├── views/         # 页面视图
│   │   │   └── strategies/# 策略工坊子页面（picker/trade/risk/flow）
│   │   ├── App.vue
│   │   └── main.ts
│   └── package.json
├── backend/               # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/        # API 路由与端点
│   │   ├── core/          # 配置项
│   │   ├── db/            # 数据库模型与会话
│   │   ├── models/        # SQLAlchemy ORM 模型（20+ 张表）
│   │   │   ├── strategy.py
│   │   │   ├── risk_strategy.py
│   │   │   ├── strategy_flow.py
│   │   │   ├── strategy_dna.py       # 策略 DNA 与系统发育
│   │   │   ├── investor_profile.py   # 投资者画像
│   │   │   ├── portfolio.py          # 投资组合
│   │   │   ├── market_signal.py      # 市场信号
│   │   │   └── rag_knowledge.py      # RAG 知识库
│   │   ├── schemas/       # Pydantic 数据校验
│   │   ├── services/      # 业务逻辑层
│   │   └── main.py        # 应用入口
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example       # 环境变量模板
│   └── seed_strategies.py # 策略种子数据
├── docs/                  # 设计文档
│   ├── architecture-v2.md # 架构文档
│   ├── user-journey-v2.md # 用户旅程
│   └── sync-scheme.md     # 真实持仓同步方案
├── docker-compose.yml     # Docker 生产部署
├── start.py               # 一键启动前后端开发环境
├── RUNTIME_REQUIREMENTS.md # 运行环境要求文档
└── package.json
```

---

## 快速开始

### 环境要求

- **Node.js**: `^20.19.0 || >=22.12.0`
- **Python**: `>=3.10`（推荐 3.11）
- **Apple Silicon Mac**: 可选，用于本地 LLM 推理（推荐 16GB+ 内存）

完整依赖和配置说明见 [RUNTIME_REQUIREMENTS.md](./RUNTIME_REQUIREMENTS.md)。

### 安装依赖

```bash
# 前端
cd frontend && npm install

# 后端
cd backend
pip install -r requirements.txt
```

### 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env，配置 LLM 路径等
```

### 下载 LLM 模型（Apple Silicon 推荐）

```bash
pip install huggingface-hub
huggingface-cli download Qwen/Qwen3-14B-MLX-4bit \
  --local-dir ~/.cache/huggingface/hub/models--Qwen--Qwen3-14B-MLX-4bit
```

更多模型见 [Hugging Face Qwen 模型库](https://huggingface.co/Qwen)。

### 启动开发环境

```bash
python start.py
```

同时启动：
- **后端**：`http://127.0.0.1:8000`
- **前端**：`http://localhost:3000`

### 手动启动

```bash
# 后端
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 前端（新终端）
cd frontend
npm run dev
```

---

## 生产部署

```bash
# Docker 一键部署
./deploy.sh

# 或手动
sudo docker-compose up -d --build
```

详细部署说明见 [DEPLOY.md](./DEPLOY.md)。

---

## API 文档

启动后端后访问：
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

| 模块 | 前缀 |
|------|------|
| 策略管理 | `/api/v1/strategies` |
| 风控策略配置 | `/api/v1/risk-strategies` |
| 策略流 | `/api/v1/strategy-flows` |
| 回测管理 | `/api/v1/backtests` |
| 模拟盘 | `/api/v1/paper-trading` |
| 持仓同步 | `/api/v1/sync` |
| 策略 DNA / 生态 | `/api/v1/dna` |
| 投资者画像 | `/api/v1/profiles` |
| 市场信号 | `/api/v1/market-signals` |
| 投资组合 | `/api/v1/portfolios` |
| 知识库 | `/api/v1/rag` |
| 健康检查 | `/health` |

---

## 策略 API 规范

平台基于 [akquant](https://github.com/akfamily/akquant) 框架运行策略。

### 基本结构

```python
from akquant import Strategy

class MyStrategy(Strategy):
    def __init__(self):
        super().__init__()
        self.ma_window = 20

    def on_bar(self, bar):
        symbol = bar.symbol
        closes = self.get_history(self.ma_window + 1, symbol, field="close")
        if len(closes) < self.ma_window + 1:
            return

        ma = closes[-self.ma_window:].mean()
        pos = self.get_position(symbol)

        if bar.close > ma and pos == 0:
            self.order_target_percent(0.95, symbol)
        elif bar.close < ma and pos > 0:
            self.order_target_percent(0.0, symbol)
```

### 核心方法

| 方法 | 说明 |
|------|------|
| `on_bar(bar)` | 每个 K 线到达时触发 |
| `get_history(count, symbol, field='close')` | 获取历史数据。field 可选 close/open/high/low/volume，省略返回完整 DataFrame |
| `set_history_depth(n)` | 设置历史数据缓存深度，必须在 get_history 前调用 |
| `order_target_percent(weight, symbol)` | 目标仓位下单，weight 为 0.0~1.0 |
| `get_position(symbol)` | 获取当前持仓数量 |

### Bar 对象

| 属性 | 说明 |
|------|------|
| `bar.symbol` | 股票代码 |
| `bar.close` / `bar.open` / `bar.high` / `bar.low` | 价格 |
| `bar.volume` | 成交量 |
| `bar.extra['amount']` | 成交额 |
| `bar.extra['turnover']` | 换手率 |

### 风控扩展

```python
def risk_check(self, context):
    """返回 True 允许交易，False 阻止"""
    if context['drawdown'] > 0.05:
        return False
    return True
```

> 策略工坊编辑器内置 API 参考面板，可边写边查。

---

## 运行测试

```bash
cd backend
pytest
```

---

## 配置文件

`backend/app/core/config.py`，支持 `.env` 覆盖：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `API_V1_STR` | `/api/v1` | API 前缀 |
| `BACKEND_CORS_ORIGINS` | `*` | 跨域来源 |
| `SQLITE_DB_PATH` | `./quant_trading.db` | 数据库路径 |
| `LLM_BACKEND` | `mlx` | LLM 后端：mlx / openai / mock |
| `EMBEDDING_BACKEND` | `sentence_transformers` | Embedding 后端 |

完整配置说明见 [RUNTIME_REQUIREMENTS.md#四环境变量配置](./RUNTIME_REQUIREMENTS.md#四环境变量配置)。

---

## 设计原则

1. **策略即有机体**：每个策略都有 DNA、家族、代谢和寿命，不是孤立的代码片段
2. **策略流强绑定**：通过 ID 引用实现策略组合，子策略更新后策略流自动生效
3. **禁止嵌套**：策略流只能绑定原子策略，不允许嵌套绑定另一个策略流
4. **删除保护**：被策略流引用的子策略不允许删除
5. **不侵入 akquant 内部状态**：模拟盘与真实持仓采用双账本并行
6. **本地优先**：SQLite + 本地文件存储，零外部依赖，开箱即用
7. **Apple Silicon 原生**：MLX 框架本地 LLM 推理，无需 Docker/CUDA

---

## 相关资源

- **LLM 模型**: [Hugging Face Qwen 模型库](https://huggingface.co/Qwen)
- **量化数据源**: [AKShare 文档](https://www.akshare.xyz/)
- **回测引擎**: [akquant GitHub](https://github.com/akfamily/akquant)
- **MLX 框架**: [MLX GitHub](https://github.com/ml-explore/mlx)

---

## 许可证

MIT

# QuantEvo — 量化策略生态系统

QuantEvo（Quantitative Strategy Ecosystem）是一个面向个人量化投资者的全栈量化交易平台。它将每个交易策略视为一个「有机体」，通过 DNA 测序提取策略的基因特征，分析亲缘关系与生态健康度，帮助构建多样化、抗风险的交易策略群落。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Vue 3 + Vite + TypeScript + Pinia + Vue Router + ECharts + Vue I18n + CodeMirror |
| **后端** | FastAPI + SQLAlchemy + SQLite + Pydantic |
| **量化引擎** | [akquant](https://github.com/akfamily/akquant)（回测/模拟盘）+ [akshare](https://www.akshare.xyz/)（数据获取）|
| **测试** | pytest + httpx |

---

## 项目结构

```
quant-trading-app/
├── frontend/                  # Vue 3 前端
│   ├── src/
│   │   ├── api/               # 后端 API 封装
│   │   ├── components/        # 公共组件（SparklineChart、LoadingOverlay 等）
│   │   ├── i18n/              # 国际化（中/英/日）
│   │   ├── router/            # 路由配置
│   │   ├── stores/            # Pinia 状态管理
│   │   ├── views/             # 页面视图
│   │   │   ├── strategies/    # 策略工坊子页面（picker/trade/risk/flow）
│   │   │   ├── BacktestCenter.vue    # 回测中心
│   │   │   ├── PaperTradingMonitor.vue # 模拟盘监控
│   │   │   ├── HomeView.vue           # 生态仪表盘（首页）
│   │   │   ├── StrategyMapView.vue    # 策略地图
│   │   │   ├── DNAReport.vue          # 基因报告
│   │   │   ├── UserManual.vue         # 使用手册
│   │   │   └── StockPicker.vue        # 选股池管理
│   │   ├── App.vue
│   │   └── main.ts
│   └── package.json
├── backend/                   # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/endpoints/  # API 路由
│   │   │   ├── dna.py         # DNA 测序/生态/系统发育
│   │   │   ├── strategies.py  # 策略管理
│   │   │   ├── backtests.py   # 回测管理
│   │   │   ├── paper_trading.py
│   │   │   ├── stock_picker.py
│   │   │   ├── strategy_flows.py
│   │   │   ├── risk_strategies.py
│   │   │   ├── sync.py
│   │   │   └── account_settings.py
│   │   ├── core/              # 配置项
│   │   ├── db/                # 数据库模型与会话
│   │   ├── models/            # SQLAlchemy ORM 模型
│   │   │   ├── strategy.py
│   │   │   ├── strategy_dna.py       # DNA / 代谢 / 寿命模型
│   │   │   ├── backtest.py           # 回测结果（含 benchmark 对照）
│   │   │   ├── paper_trading.py
│   │   │   ├── stock_picker.py
│   │   │   ├── risk_strategy.py
│   │   │   ├── strategy_flow.py
│   │   │   ├── sync_models.py
│   │   │   └── account_settings.py
│   │   ├── schemas/           # Pydantic 数据校验
│   │   ├── services/          # 业务逻辑层
│   │   │   ├── dna_sequencer.py      # DNA 测序引擎
│   │   │   ├── phylogeny_service.py  # 系统发育引擎
│   │   │   ├── ecosystem_service.py  # 生态仪表盘聚合
│   │   │   ├── lifespan_service.py   # 寿命预测
│   │   │   ├── metabolic_service.py  # 代谢分析
│   │   │   ├── backtest_service.py   # 回测执行（含 Buy & Hold 对照）
│   │   │   └── ...
│   │   └── main.py            # 应用入口
│   ├── tests/                 # 测试用例
│   └── requirements.txt
├── docs/                      # 设计文档
│   └── sync-scheme.md         # 真实持仓同步方案
├── start.py                   # 一键启动前后端开发环境
└── package.json               # 根目录依赖
```

---

## 核心功能

### 1. 策略工坊（Strategy Workshop）

策略中枢，统一包含四个子页面：

- **选股策略（Picker）**：基于 akshare 获取 A 股市场数据，编写自定义选股逻辑；内置每周五自动运行的量价活跃选股策略
- **交易策略（Trade）**：在线编写 Python 量化策略，内置 CodeMirror 编辑器，基于 akquant 框架
- **风控策略（Risk）**：A+B 混合模式——既支持 Python 代码扩展（`risk_check(context)`），也内置表单化规则配置（仓位上限、日最大回撤、黑名单）
- **策略流（Flow）**：将选股、风控、交易策略强绑定为流水线。策略流保存对子策略的 ID 引用，回测/模拟盘运行时自动完成选股 → 风控 → 交易的执行链路

### 2. QuantEvo 策略生态系统

#### 2.1 策略 DNA 测序
每次保存策略时，系统自动对代码进行 DNA 测序：
- **特征层基因**：检测技术指标（MA、MACD、RSI、BOLL、ATR 等）
- **信号层基因**：识别交易逻辑（金叉死叉、突破、均值回归、ML 模型等）
- **风控层基因**：发现止损、仓位管理、回撤控制等机制
- **执行层基因**：识别订单类型（市价单、限价单、TWAP 等）

测序结果生成 32 维基因向量，用于相似度计算和家族聚类。

#### 2.2 系统发育与亲属关系
基于基因向量余弦相似度计算策略间亲缘关系：
- 每个策略展示 Top 5 最相似的策略（相似度进度条直观展示）
- **同质化风险**：与最近亲属的平均相似度，>75% 触发「近亲警告」
- **家族归属**：基于策略基因自动聚类（趋势跟踪、动量、均值回归、多因子、风控增强等家族）

#### 2.3 代谢分析与寿命预测
- **代谢率**：反映策略信息更新频率和逻辑复杂度（高代谢 = 频繁调仓、多层嵌套）
- **生态位宽度**：覆盖的市场状态越多，寿命越长
- **寿命预测**：基于代谢率、生态位、同质化压力、代谢综合征四维度计算预计剩余寿命（月）
- **寿命阶段**：年轻（36+ 月）/ 成熟（12-36 月）/ 衰老（3-12 月）/ 濒危（<3 月）

#### 2.4 生态仪表盘（首页）
提供策略群落的整体健康状况：
- **KPI 卡片**：策略总数、家族数量、平均健康度、近亲风险计数
- **图表区**：家族分布条形图、寿命分布环形图、代谢排名、家族雷达图、家族网络力导向图
- **需关注策略**：健康度 <60 的策略列表
- **寿命预警**：短寿命/濒危策略高亮
- **策略墓地**：已停止或濒危策略归档

#### 2.5 策略地图
按基因家族分组展示 22 个预设策略：
- 每个策略卡片显示健康度分数、多样性百分比、特征/信号基因数量
- 点击「导入策略」将预设策略复制到你的生态中
- 家族分类：趋势跟踪、动量、均值回归、多因子、风控增强

### 3. 回测中心（Backtest Center）

- 为指定策略或策略流配置回测参数（标的、时间范围、初始资金）
- 调用 akquant 引擎执行回测，**每次回测自动运行买入并持有（Buy & Hold）对照组**，便于评估策略超额收益
- 记录回测状态与结果，支持删除和历史对比
- **策略流回测**：若选择策略流，系统自动先执行选股节点得到标的，再运行交易节点；若选股结果为空则自动终止并提示
- **生态预审**：创建回测时自动检测策略同质化风险（>50% 时弹出警告）
- **回测周期推荐**：根据策略代谢率智能推荐回测时长（高代谢 1-3 月 / 中等 3-6 月 / 低代谢 6-12 月）

### 4. 模拟盘监控（Paper Trading Monitor）

- 基于 akquant Paper Trading 模式运行策略或策略流
- 实时展示模拟持仓、盈亏与交易信号
- **寿命倒计时**：每个运行中的会话显示当前寿命阶段（年轻/成熟/衰老/濒危），濒危状态红色脉冲警示
- **停盘死因归档**：停止模拟盘时选择停止原因（策略失效/达到目标/止损退出/手动停止/其他），便于复盘
- **策略墓地**：页面底部归档所有已停止的会话

### 5. 生态集成（五大集成方案）

QuantEvo 生态系统与业务模块深度联动：

| 方案 | 模块 | 功能 |
|------|------|------|
| 方案一 | 回测中心 | 生态预审（近亲警告 + 周期推荐）+ 策略选择器下方生态迷你卡片 |
| 方案二 | 模拟盘监控 | 寿命状态列 + 停盘死因归档 + 策略墓地 |
| 方案三 | 策略工坊 | 代码输入 3 秒后自动生成基因预览（健康度/多样性/代谢率 + 相似度预警） |
| 方案四 | 全局导航 | 导航栏徽章（濒危策略计数）+ 基因报告快捷操作（跳转编辑/回测/模拟盘） |
| 方案五 | 模块级浮层 | 回测中心/模拟盘/策略工坊内嵌生态迷你卡片（健康度色点 + 分数 + 家族） |

### 6. 真实持仓同步（Real Position Sync）

- **双账本并行**：模拟账本（akquant）+ 真实账本（本系统独立维护）
- 一键同步：在券商 APP 完成真实交易后，回填实际成交数据
- 收盘自动对账：对比模拟持仓与真实持仓，生成差异清单
- 未来可平滑扩展至 MiniQMT 自动交易接入

> 详细设计见 [docs/sync-scheme.md](./docs/sync-scheme.md)

---

## 快速开始

### 环境要求

- **Node.js**: `^20.19.0 || >=22.12.0`
- **Python**: `>=3.10`
- **Conda**（推荐用于管理 Python 环境）

### 1. 安装依赖

**前端**

```bash
cd frontend
npm install
```

**后端**

```bash
# 创建并激活 conda 环境（示例）
conda create -n quant python=3.12
conda activate quant

# 安装依赖
cd backend
pip install -r requirements.txt
```

### 2. 启动开发环境

在项目根目录执行一键启动脚本：

```bash
python start.py
```

该脚本会同时启动：
- **后端服务**：`http://127.0.0.1:8000`（uvicorn 热重载）
- **前端服务**：`http://localhost:5173`（vite dev server）

按 `Ctrl+C` 即可优雅关闭所有子进程。

### 3. 手动启动（可选）

```bash
# 后端
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 前端（新终端）
cd frontend
npm run dev
```

---

## API 文档

启动后端后，可访问自动生成的 OpenAPI 文档：

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

### 主要接口

| 模块 | 前缀 | 说明 |
|------|------|------|
| 策略管理 | `/api/v1/strategies` | CRUD + DNA 测序触发 |
| 策略 DNA | `/api/v1/dna/*` | 测序、预览、生态系统、家族列表 |
| 系统发育 | `/api/v1/strategies/{id}/phylogeny` | 亲属关系、同质化风险 |
| 寿命预测 | `/api/v1/strategies/{id}/lifespan` | 寿命阶段、老化速度、建议 |
| 风控策略配置 | `/api/v1/risk-strategies` | 表单化风控规则 |
| 策略流 | `/api/v1/strategy-flows` | 流水线编排 |
| 回测管理 | `/api/v1/backtests` | 创建/运行/删除（含 Buy & Hold 对照） |
| 模拟盘 | `/api/v1/paper-trading` | 会话管理、持仓监控 |
| 持仓同步 | `/api/v1/sync` | 真实持仓回填与对账 |
| 健康检查 | `/health` | 服务状态 |

---

## 运行测试

```bash
cd backend
pytest
```

---

## 配置文件

后端配置通过 `backend/app/core/config.py` 管理，支持 `.env` 文件覆盖：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PROJECT_NAME` | `quant-trading-app` | 项目名称 |
| `VERSION` | `0.1.0` | 版本号 |
| `API_V1_STR` | `/api/v1` | API 前缀 |
| `BACKEND_CORS_ORIGINS` | `http://localhost:5173` | 允许的跨域来源 |
| `SQLITE_DB_PATH` | `./quant_trading.db` | SQLite 数据库路径 |

---

## 设计原则

1. **策略流强绑定**：通过 ID 引用实现策略组合，子策略更新后策略流自动生效
2. **禁止嵌套**：策略流只能绑定原子策略，不允许嵌套绑定另一个策略流
3. **删除保护**：被策略流引用的子策略不允许删除
4. **不侵入 akquant 内部状态**：模拟盘与真实持仓采用双账本并行
5. **预留自动交易扩展**：真实持仓表结构兼容未来 MiniQMT Gateway 接入
6. **生态优先**：每次策略操作自动触发 DNA 测序，生态健康度作为决策依据
7. **对照组基准**：回测自动运行 Buy & Hold 对照，避免单一策略结果误导
8. **本地优先**：SQLite + 本地文件存储，零外部数据库依赖，开箱即用

---

## 相关依赖

- [akquant](https://github.com/akfamily/akquant) — 量化回测与模拟交易引擎
- [akshare](https://www.akshare.xyz/) — 中国金融数据接口库
- [FastAPI](https://fastapi.tiangolo.com/) — 现代高性能 Python Web 框架
- [Vue 3](https://vuejs.org/) — 渐进式前端框架
- [ECharts](https://echarts.apache.org/) — 数据可视化图表库

---

## 许可证

MIT

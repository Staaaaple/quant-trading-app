---
name: key-decisions
description: 用户确认的设计决策和实现约束
type: feedback
originSessionId: cf5072ae-84a5-4ae9-bbc9-b693627ef29b
---
- **首页仪表盘双状态逻辑**：用户明确要求 — 当用户没有导入自己的策略时，首页展示内置策略地图 + 理想生态数据（预览模式）；导入策略后才显示真实仪表盘数据。实现为 `hasUserStrategies` 判断。

- **保留原有功能**：回测中心和模拟盘监控必须保留，QuantEvo 是增量功能而非替换。

- **语言**：全部 QuantEvo 内容使用中文，不依赖 i18n 键（因为概念全新）。

- **数据库注意**：SQLite 表结构变更时（如添加 metabolic 字段），需删除数据库文件重新创建，`Base.metadata.create_all` 不会 ALTER TABLE 添加新列。

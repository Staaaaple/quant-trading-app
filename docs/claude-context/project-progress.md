---
name: project-progress
description: QuantEvo项目实时进度追踪（自动更新）
metadata: 
  node_type: memory
  type: project
  originSessionId: f982107d-b5f4-4809-950c-0f64af9b2b9b
---

# QuantEvo 项目进度

## 当前阶段
**Phase B Week 2-3: 知识库基础 + Hybrid引擎实现中**

## 已完成

### Phase A (4周) ✅
- [x] 数据库重建
- [x] User/Profile模型
- [x] API端点
- [x] 首页双状态
- [x] 15题问卷Wizard
- [x] 画像15维向量计算
- [x] 全局样式系统

### Phase B Week 1 ✅
- [x] 市场信号五层模型
- [x] akshare宏观数据采集
- [x] 爬虫新闻采集
- [x] NLP情绪提取
- [x] 市场信号API
- [x] 前端市场信号页
- [x] 定时任务（每日9:00）

## 进行中

### Phase B Week 2-3
- [ ] 35策略模板入库
- [ ] 20论文知识库结构化
- [ ] Hybrid引擎6步实现
  - [ ] SAA引擎
  - [ ] TAA引擎
  - [ ] 策略-标的绑定
  - [ ] 风控配置
  - [ ] 可靠性评估
  - [ ] 组合寿命计算

## 待办

### Phase B Week 4-5
- [ ] 回测适配器（个股/ETF/基金/债券）
- [ ] Walk-Forward验证
- [ ] 蒙特卡洛模拟
- [ ] 压力测试

### Phase B Week 5-7
- [ ] 组合构建器前端
- [ ] 回测中心前端
- [ ] 组合详情页

### Phase C (4周)
- [ ] 策略池扩展（35→150）
- [ ] Agent Crawler
- [ ] 动态寿命监控
- [ ] DNA测序/同质化

### Phase D (3周)
- [ ] 教学引导系统
- [ ] 建仓助手
- [ ] 推送系统
- [ ] 周报月报

## 关键决策记录
- 2026-06-01: 从专业量化工具转向投资小白快速上手工具
- 2026-06-02: 策略验证标准调整（牛市≥70%持有收益，熊市≥110%持有收益）
- 2026-06-02: 确认Hybrid引擎架构（3输入向量→6步组合设计）

## 当前阻塞
- 策略验证通过率0%，需要调整验证框架或策略设计

# RAG-Hybrid 部署检查清单

## 预部署检查

### 代码检查
- [x] `portfolio_quality_gate.py` 已创建
- [x] `adjustment_engine.py` 已创建
- [x] `hybrid_portfolio_designer_v2.py` 已创建
- [x] `__init__.py` 已更新导出
- [x] `index_builder_v2.py` 已更新支持新目录
- [x] `portfolios.py` 已新增API端点
- [x] `saa_engine.py` 已修复time_horizon处理

### 数据检查
- [x] 16种资产配置案例已创建
- [x] 8种风控案例已创建
- [x] 8种策略绑定案例已创建
- [x] 所有索引已重建（131条）

### 测试检查
- [x] 单元测试通过（13/13）
- [x] 集成测试通过（11/12，1个跳过）
- [x] 无阻塞性错误

## 部署步骤

### 1. 备份现有索引
```bash
cp -r backend/data/vector_stores backend/data/vector_stores.backup.$(date +%Y%m%d)
```

### 2. 重建索引
```bash
cd backend
python -c "from app.services.rag.index_builder_v2 import IndexBuilderV2; \
           from app.services.rag.embedding_service import get_embedding_service; \
           b = IndexBuilderV2(get_embedding_service()); \
           b.build_all(force_rebuild=True)"
```

### 3. 验证索引
```bash
python -c "from app.services.rag.index_builder_v2 import IndexBuilderV2; \
           from app.services.rag.embedding_service import get_embedding_service; \
           b = IndexBuilderV2(get_embedding_service()); \
           print(b.get_stats())"
```

### 4. 重启服务
```bash
# 如果使用uvicorn
uvicorn app.main:app --reload

# 如果使用docker
docker-compose restart backend
```

### 5. 验证API
```bash
# 测试原接口（不带RAG）
curl -X POST http://localhost:8000/api/v1/portfolios/design \
  -H "Content-Type: application/json" \
  -d '{"profile_vector": {"risk_tolerance": 0.5}, "market_signal": {"macro_score": 0.5}}'

# 测试新接口（带RAG）
curl -X POST http://localhost:8000/api/v1/portfolios/design-with-rag \
  -H "Content-Type: application/json" \
  -d '{"profile_vector": {"risk_tolerance": 0.5}, "market_signal": {"macro_score": 0.5}, "use_rag_gate": true}'
```

## 回滚方案

如果出现问题：

```bash
# 1. 恢复索引
cp -r backend/data/vector_stores.backup.* backend/data/vector_stores

# 2. 回滚代码
git checkout -- backend/app/services/rag/__init__.py
git checkout -- backend/app/services/rag/index_builder_v2.py
git checkout -- backend/app/api/v1/endpoints/portfolios.py
git checkout -- backend/app/services/saa_engine.py

# 3. 删除新增文件（如需完全回滚）
rm backend/app/services/rag/portfolio_quality_gate.py
rm backend/app/services/rag/adjustment_engine.py
rm backend/app/services/hybrid_portfolio_designer_v2.py

# 4. 重启服务
```

## 监控指标

部署后监控：

| 指标 | 正常范围 | 告警阈值 |
|------|---------|---------|
| 组合生成时间 | <3s | >5s |
| RAG质检耗时 | <500ms/点 | >1s/点 |
| 索引加载时间 | <1s | >3s |
| API错误率 | <1% | >5% |

## 已知问题

1. **Mock LLM限制**：当前RAG质检使用mock LLM，生产环境需配置真实模型
2. **回测模拟**：绑定审核的回测为模拟数据，需接入真实回测服务
3. **transformers加载**：启用RAG时加载transformers可能崩溃（已跳过相关测试）

## 后续优化

- [ ] 接入真实LLM（Qwen3-14B-MLX）
- [ ] 接入真实回测服务
- [ ] 前端展示RAG质检记录
- [ ] 调节阈值基于实盘数据校准
- [ ] 性能优化（异步并行质检）

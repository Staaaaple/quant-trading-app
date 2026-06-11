# RAG-Hybrid 全链路性能分析

## 实测结果（Mock 模式）

| 模式 | 耗时 | 说明 |
|------|------|------|
| **不带 RAG** | **0.3ms** | 纯规则计算，极快 |
| **带 RAG (Mock)** | **49.6ms** | 含6次索引加载 + Mock LLM 响应 |

### Mock 模式 RAG 质检详情

```
[Retriever] 加载6个索引: ~40ms
  - stock_case_index (16条)
  - allocation_theory_index (8条)
  - finance_basic_index (20条)
  - valuation_case_index (20条)
  - behavioral_case_index (15条)
  - paper_chunk_index (20条)

RAG 质检记录 (9条):
  - saa: passed=False (触发调节)
  - taa: passed=False (触发调节)
  - risk_config: passed=False (触发调节)
  - reliability: passed=False ×5 (5次重试全部失败)
  - final: passed=False
```

**注意**：Mock LLM 总是返回 "不通过"，所以触发大量重试。生产环境真实 LLM 会根据实际情况判断。

---

## 生产环境预估耗时

### 基础流程（无 RAG）

| 步骤 | 操作 | 预估耗时 |
|------|------|---------|
| Step 1 | SAA 计算 | 10-50ms |
| Step 2 | TAA 计算 | 10-30ms |
| Step 3 | 策略绑定 | 5-20ms |
| Step 4 | 风控配置 | 1-5ms |
| Step 5 | 可靠性评估 | 50-200ms |
| Step 6 | 寿命计算 | 1-5ms |
| **总计** | | **80-310ms** |

### RAG 质检（每步）

| 子步骤 | 操作 | 预估耗时 | 瓶颈分析 |
|--------|------|---------|---------|
| 检索 | FAISS 向量检索 | 50-200ms | 取决于索引大小和 top_k |
| LLM 生成 | Qwen3-14B-MLX 生成 | **500-3000ms** | **主要瓶颈** |
| 解析 | JSON 解析 + 提取 | 10-50ms | 可忽略 |
| 调节 | 应用调节建议 | 10-50ms | 可忽略 |
| **每步总计** | | **570-3300ms** | |

### 全链路预估（6步全质检）

| 场景 | 计算方式 | 预估耗时 |
|------|---------|---------|
| 最理想（全部一次通过） | 6步 × 570ms | **~3.4s** |
| 正常（2步需要重试1次） | 8步 × 1500ms | **~12s** |
| 较差（可靠性5次重试） | 11步 × 2000ms | **~22s** |
| 最差（每步都重试满） | 15步 × 3000ms | **~45s** |

---

## LLM 调用记录

### 每次质检的 LLM 调用

```python
# 6个质检点，每个点调用 1 次 LLM
# 如果失败重试，再调用 1 次

SAA 审核:
  - 输入: ~2000 tokens (SAA结果 + 市场信号 + 检索上下文)
  - 输出: ~500 tokens (JSON格式审核结果)
  - 模型: Qwen3-14B-MLX-4bit
  - 预估: 800-1500ms

TAA 审核:
  - 输入: ~1500 tokens
  - 输出: ~400 tokens
  - 预估: 600-1200ms

绑定审核:
  - 输入: ~2500 tokens (绑定信息 + 回测数据 + 检索上下文)
  - 输出: ~600 tokens
  - 预估: 1000-2000ms

风控审核:
  - 输入: ~1000 tokens
  - 输出: ~300 tokens
  - 预估: 400-800ms

可靠性审核:
  - 输入: ~3000 tokens (回测汇总 + 压力测试 + 检索上下文)
  - 输出: ~800 tokens
  - 预估: 1200-2500ms

最终审核:
  - 输入: ~2000 tokens
  - 输出: ~400 tokens
  - 预估: 600-1200ms
```

### 单次组合生成的 LLM 调用统计

| 场景 | 调用次数 | 总输入 Tokens | 总输出 Tokens | 预估耗时 |
|------|---------|--------------|--------------|---------|
| 全部一次通过 | 6次 | ~12,000 | ~3,000 | **~4.7s** |
| 2步各重试1次 | 8次 | ~16,000 | ~4,000 | **~6.3s** |
| 可靠性重试5次 | 10次 | ~22,000 | ~5,500 | **~8.5s** |

---

## 优化建议

### 1. 并行质检（最大优化）

当前是串行质检（Step1 → 质检 → Step2 → 质检...），可改为：

```python
# 串行（当前）
总耗时 = Step1 + 质检1 + Step2 + 质检2 + ... ≈ 6 × 2s = 12s

# 并行（优化后）
总耗时 = max(Step1+质检1, Step2+质检2, ...) ≈ 2s
```

**但注意**：步骤间有依赖关系（SAA结果影响TAA），不能完全并行。

**可行方案**：
- SAA 和风控可并行（风控只依赖画像）
- TAA 和绑定可部分并行
- 最终审核必须等前面全部完成

**优化后预估**：
- 串行 → 并行：12s → **4-6s**

### 2. 缓存质检结果

```python
# 相同画像 + 相同市场周期 → 复用质检结果
缓存键 = hash(profile_vector + market_cycle_phase)
```

**效果**：
- 首次生成：~12s
- 缓存命中：~0.3s（直接返回基础流程结果）

### 3. 异步质检（不阻塞返回）

```python
# 先返回基础组合，RAG质检异步进行
# 质检完成后推送通知

响应（即时）:
  { portfolio: 基础组合, status: "pending_review" }

推送（3-10s后）:
  { portfolio: 优化后组合, rag_reviews: [...] }
```

**用户体验**：
- 首次看到组合：~0.3s
- 看到优化建议：~3-10s

### 4. 降级策略

```python
if LLM_timeout:
    # 超时降级：使用规则审核代替LLM审核
    return rule_based_review()  # ~10ms

if LLM_error:
    # 错误降级：跳过RAG，返回基础组合
    return portfolio_without_rag()  # ~0.3ms
```

---

## 推荐配置

### 开发/测试环境

```python
use_rag_gate = False  # 快速迭代，0.3ms
# 或
use_rag_gate = True   # 但用 mock LLM，~50ms
```

### 生产环境（低延迟优先）

```python
# 方案A：异步RAG
use_rag_gate = True
rag_mode = "async"  # 先返回基础组合，异步优化

# 方案B：缓存优先
use_rag_gate = True
rag_cache_ttl = 3600  # 1小时缓存

# 方案C：降级保障
use_rag_gate = True
rag_timeout = 3000    # 3秒超时降级
```

### 生产环境（质量优先）

```python
# 完整RAG质检
use_rag_gate = True
rag_mode = "sync"     # 等待全部质检完成
rag_max_retries = 3   # 限制重试次数
rag_timeout = 30000   # 30秒超时
```

---

## 监控指标

```python
# 需要记录的指标
metrics = {
    "hybrid_total_time_ms": 0,      # 总耗时
    "hybrid_base_time_ms": 0,       # 基础流程耗时
    "hybrid_rag_time_ms": 0,        # RAG质检耗时
    "rag_step_times": {             # 每步耗时
        "saa_review_ms": 0,
        "taa_review_ms": 0,
        "binding_review_ms": 0,
        "risk_review_ms": 0,
        "reliability_review_ms": 0,
        "final_review_ms": 0,
    },
    "rag_llm_calls": 0,             # LLM调用次数
    "rag_llm_tokens_in": 0,         # 输入tokens
    "rag_llm_tokens_out": 0,        # 输出tokens
    "rag_adjustments": 0,           # 调节次数
    "rag_cache_hits": 0,            # 缓存命中
    "rag_cache_misses": 0,          # 缓存未命中
}
```

---

## 总结

| 指标 | 当前(Mock) | 生产(预估) | 优化后 |
|------|-----------|-----------|--------|
| 基础流程 | 0.3ms | 80-310ms | 80-310ms |
| + RAG质检 | 49.6ms | 4-45s | 2-8s |
| LLM调用/次 | 0ms | 0.5-3s | 0.5-3s |
| 总调用/组合 | 6-15次 | 6-15次 | 6-15次 |

**关键结论**：
1. **Mock模式不能反映真实性能**，真实LLM是主要瓶颈
2. **生产环境必须优化**：并行、缓存、异步
3. **建议默认异步模式**：先返回基础组合，3-10s后推送优化结果
4. **可靠性审核最耗时**：5次重试可能占50%以上时间

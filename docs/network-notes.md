# 网络环境注意事项

## AKShare 数据源稳定性与代理问题

### 问题描述

在部分网络环境下，`akshare` 调用**东方财富**数据源接口（`ak.stock_zh_a_hist` 等）时可能出现以下异常：

```
requests.exceptions.ConnectionError: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
```

**根本原因分析：**
- 东方财富服务端对特定请求特征（IP、请求频率、User-Agent 等）存在反爬/拦截策略，会主动断开连接。
- 在某些网络环境（如存在 HTTP/HTTPS 代理、企业内网、或本地安全软件）下，该现象更为频繁。
- 这**并非**程序缺陷，而是数据源层面的访问限制。

### 已实现的稳定性措施

后端已在 `app/services/backtest_service.py` 中实现**多源自动回退（fallback）**机制：

1. **主数据源**：东方财富（`ak.stock_zh_a_hist`）— 数据最全、支持按日期段精确获取。
2. **备用数据源**：新浪财经（`ak.stock_zh_a_daily`）— 在主源失败时自动切换，支持前复权数据。

**测试结果（2026-04-14）：**
- 东方财富接口：❌ 在当前网络环境下被主动断开
- 新浪财经接口：✅ 可正常返回 A 股历史日线数据
- `fetch_stock_data` 自动 fallback 后，回测数据拉取恢复正常

### 后端错误码设计

回测服务在拉取数据失败时，会将错误分类并写入回测记录的 `metrics.error_code` 字段：

| `error_code` | 含义 | 触发条件 |
|-------------|------|---------|
| `akshare_proxy_error` | 网络/代理问题 | 所有数据源均因 `ConnectionError` 无法连接 |
| `akshare_data_error` | 数据不可用 | 数据源返回空数据或非网络类异常 |

回测结果响应示例（失败时 `status` 为 `failed`）：
```json
{
  "backtest_id": "bt001",
  "status": "failed",
  "metrics": {
    "error_code": "akshare_proxy_error",
    "error": "无法连接到 AKShare 数据源（代理或网络问题）。请检查系统代理设置，或尝试关闭代理后重试。"
  },
  "logs": "AkshareProxyError: ..."
}
```

### 前端实现要求

**当后端返回的回测记录 `metrics.error_code` 为 `akshare_proxy_error` 时，前端应弹出通知提醒用户。**

建议实现：
- 在调用 `POST /api/v1/backtests/{id}/run` 后，检查响应体中的 `status` 和 `metrics.error_code`：
  - 若 `status == "failed"` 且 `metrics.error_code == "akshare_proxy_error"`，弹出 `Notification` / `Message`：
    > "无法连接到 AKShare 数据源，疑似网络代理拦截。请检查代理设置或切换网络后重试。"
  - 若 `status == "failed"` 且 `metrics.error_code == "akshare_data_error"`，弹出提示：
    > "无法获取该标的历史数据，请检查股票代码或日期范围是否正确。"

### 常见解决方案

1. **临时关闭代理**
   在终端中执行：
   ```bash
   unset HTTP_PROXY
   unset HTTPS_PROXY
   unset http_proxy
   unset https_proxy
   ```
   然后重新启动后端服务。

2. **更换网络环境**
   切换到无代理限制或未被目标站屏蔽的 Wi-Fi 网络。

3. **手动补充本地数据（高级）**
   `akquant` 在已有本地数据的情况下可正常执行回测计算。未来可扩展 parquet data catalog 机制，避免完全依赖实时网络。

### 影响范围

- 回测时拉取历史 K 线数据
- 模拟盘实时数据获取
- 收盘自动对账时获取当日收盘价

### 备注

- 新浪财经作为备用源，数据格式与东财略有不同（如成交量单位），后端已通过 `_normalize_akquant_df` 统一标准化。
- 备用源暂无分钟级数据，若未来需要分钟级回测，需额外接入其他可用数据源。

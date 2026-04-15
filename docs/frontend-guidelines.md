# 前端开发规范

本文档规范 `quant-trading-app` 前端开发中的通用实践，确保后续功能迭代的一致性与可维护性。

---

## 1. 异步操作全局 Loading 规范（强制）

### 1.1 原则

**任何会触发后端 API 调用且可能耗时超过 500ms 的按钮/操作，都必须显示全局 Loading 遮罩。**

这包括但不限于：
- **运行/执行类**：运行选股、运行回测、运行模拟盘、停止模拟盘
- **保存/提交类**：保存策略、保存设置、提交同步、批量补录
- **导入/导出类**：CSV 导入
- **创建类**：新建策略、新建回测、新建模拟盘会话

### 1.2 使用方式

项目已内置全局组件 `LoadingOverlay`（`frontend/src/components/LoadingOverlay.vue`），通过 `Teleport` 挂载到 `body`，自带半透明背景、模糊效果与旋转动画。

#### 步骤

1. **导入组件**
   ```ts
   import LoadingOverlay from '@/components/LoadingOverlay.vue'
   ```

2. **声明 loading 状态**
   ```ts
   const loading = ref(false)
   ```
   若页面存在多个并发的耗时操作（如"保存"与"运行"可能同时触发），应为每个操作声明独立状态：
   ```ts
   const saving = ref(false)
   const running = ref(false)
   ```

3. **在异步函数中切换状态**
   ```ts
   async function saveStrategy() {
     loading.value = true
     try {
       await strategyApi.update(...)
       showToast(t('strategy.saveSuccess'))
     } catch (e: any) {
       showToast(t('strategy.saveError') + ': ' + e.message)
     } finally {
       loading.value = false
     }
   }
   ```

4. **在模板中挂载组件**
   ```vue
   <template>
     <div class="page">
       <!-- 页面内容 -->

       <LoadingOverlay :visible="loading" :text="t('common.loading')" />
     </div>
   </template>
   ```

### 1.3 多状态合并示例

当页面有多个独立异步操作时，推荐用 `computed` 合并为单一 `showOverlay`：

```vue
<script setup>
const loading = ref(false)
const running = ref(false)
const runningWeekly = ref(false)

const showOverlay = computed(() => loading.value || running.value || runningWeekly.value)
</script>

<template>
  <div class="page">
    <!-- ... -->
    <LoadingOverlay :visible="showOverlay" :text="t('common.loading')" />
  </div>
</template>
```

### 1.4 禁止行为

- **禁止**仅用按钮 `disabled` 状态表示加载中，而不展示全局遮罩。
- **禁止**在 `finally` 块遗漏 `loading.value = false`，否则遮罩将永远卡死。
- **禁止**对纯本地、不调用 API 的操作（如打开弹窗、切换 Tab）使用 LoadingOverlay。

---

## 2. 页面结构规范

### 2.1 通用布局

每个页面入口统一使用：
```vue
<template>
  <div class="page">
    <!-- 页面内容 -->
  </div>
</template>
```

### 2.2 状态提示

- **成功提示**：使用 `showToast()`，绿色背景，3 秒后自动消失
- **错误提示**：使用 `showToast(msg, 'error')`，红色背景
- **Loading 提示**：统一使用 `LoadingOverlay`，不重复在 Toast 中提示 loading

---

## 3. API 错误处理

所有 `await api.xxx()` 调用必须包裹在 `try/catch` 中，错误信息应拼接具体异常消息：

```ts
try {
  await api.create(...)
} catch (e: any) {
  showToast(t('xxx.createError') + ': ' + e.message, 'error')
} finally {
  loading.value = false
}
```

---

## 4. 组件引用路径

组件统一使用 `@/components/xxx` 别名引入，不使用相对路径 `../components/xxx`。

---

## 5. i18n 新增键值规范

在 `frontend/src/i18n/locales/` 下的 `zh-CN.json`、`en.json`、`ja.json` 中同步添加键值：

- 命名采用小驼峰
- 按模块分组（`strategy`、`backtest`、`paperTrading`、`stockPicker` 等）
- 修改后务必检查三语文件是否同步更新

---

## 6. 样式变量

优先使用 `frontend/src/assets/base.css` 中定义的 CSS 变量，不硬编码色值：

| 用途 | 变量 |
|---|---|
| 主背景 | `--bg-base` |
| 卡片背景 | `--bg-surface` |
| 悬停背景 | `--bg-surface-hover` |
| 主文本 | `--text-primary` |
| 次要文本 | `--text-secondary` |
| 主题色 | `--accent` |
| 成功色 | `--success` |
| 错误色 | `--error` |
| 间距 | `--space-sm` ~ `--space-4xl` |

---

*最后更新：2026-04-15*

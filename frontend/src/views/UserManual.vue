<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'

const activeSection = ref<string | null>(null)

function toggleSection(key: string) {
  activeSection.value = activeSection.value === key ? null : key
}

const sections = [
  {
    key: 'intro',
    icon: '🌿',
    title: '什么是 QuantEvo',
    content: `QuantEvo（Quantitative Strategy Ecosystem）是你的量化策略生态系统。它将每个交易策略视为一个「有机体」，通过 DNA 测序提取策略的基因特征，分析它们之间的亲缘关系，评估生态健康度，帮助你构建一个多样化、抗风险的交易策略群落。

核心隐喻：策略如同生物，有出生（创建）、成长（优化）、衰老（失效）和死亡（淘汰）的生命周期。健康的生态系统需要多样性——单一策略的过度繁殖会导致近亲衰退。`,
  },
  {
    key: 'quickstart',
    icon: '🚀',
    title: '快速开始',
    content: `1. 打开「策略地图」浏览 22 个预设策略，按家族分类展示
2. 点击「导入策略」将感兴趣的策略加入你的生态
3. 在「策略工坊」中编辑或创建自己的策略
4. 保存后系统自动进行 DNA 测序
5. 回到首页查看你的生态仪表盘
6. 点击任意策略的「基因报告」查看详细分析`,
  },
  {
    key: 'dna',
    icon: '🧬',
    title: '策略 DNA 测序',
    content: `每次保存策略时，系统会自动对其代码进行 DNA 测序。测序过程包括：

• 特征层基因：检测技术指标（MA、MACD、RSI、BOLL、ATR 等）
• 信号层基因：识别交易逻辑（金叉死叉、突破、均值回归、ML 模型等）
• 风控层基因：发现止损、仓位管理、回撤控制等风控机制
• 执行层基因：识别订单类型（市价单、限价单、TWAP 等）

测序结果生成 32 维基因向量，用于后续的相似度计算和家族聚类。`,
  },
  {
    key: 'report',
    icon: '📋',
    title: '基因报告解读',
    content: `基因报告展示单个策略的完整基因画像：

健康度评分（0-100）
• 基础分 50 + 多样性加分 + 风控加分 + ML 加分
• ≥80：健康，基因丰富，风控完善
• 60-79：一般，可优化
• <60：需关注，可能缺乏风控或基因过于单一

多样性评分
• 检测到的独特基因数量 / 16，上限 1.0
• 多样性越高，策略的抗脆弱性越强

四层基因标签
• 每层最多展示全部检测到的基因
• 空层会提示风险（如缺少风控基因）`,
  },
  {
    key: 'map',
    icon: '🗺️',
    title: '策略地图',
    content: `策略地图按基因家族分组展示所有策略：

家族分类
• 趋势跟踪家族：均线、MACD、突破类策略
• 动量家族：RSI、KDJ、量价、动量排名
• 均值回归家族：布林带、RSI 超卖反弹、低波动率
• 多因子家族：估值、ROE、小市值、动量+价值
• 风控增强家族：ATR 止损、仓位管理、动态止损
• 系统内置：选股器等系统功能

每个策略卡片显示：
• 健康度分数（颜色编码）
• 多样性百分比
• 特征/信号基因数量
• 前 3 个特征基因 + 前 2 个信号基因标签

点击「导入策略」可将预设策略复制到你的生态中。`,
  },
  {
    key: 'phylogeny',
    icon: '🌳',
    title: '系统发育与亲属关系',
    content: `系统发育基于基因向量的余弦相似度计算策略间的亲缘关系：

最近亲属
• 每个策略展示 Top 5 最相似的策略
• 相似度以进度条直观展示
• 可点击跳转查看亲属的基因报告

同质性风险
• 与最近亲属的平均相似度
• >75% 触发「近亲警告」
• 高同质性意味着策略群落缺乏多样性，市场风格切换时可能集体失效

家族归属
• 基于策略 ID 模式自动分类
• 也可通过相似度聚类自动识别`,
  },
  {
    key: 'dashboard',
    icon: '📊',
    title: '生态仪表盘',
    content: `首页生态仪表盘提供策略群落的整体健康状况：

KPI 卡片
• 策略有机体总数
• 基因家族数量
• 平均健康度（颜色反映状态）
• 近亲风险计数

图表区
• 家族分布：水平条形图展示各家族策略数量
• 寿命分布：环形图展示年轻/成熟/衰老/濒危的比例
• 代谢排名：所有策略按代谢率排序，识别高能耗策略
• 家族雷达：各家族在健康度、多样性、稳定性等维度的对比
• 家族网络：力导向图展示策略间的亲缘关系连线

需关注策略
• 健康度 <60 的策略列表
• 附带健康度进度条和快捷操作

寿命预警
• 短寿命（<12 月）策略列表
• 濒危（<3 月）策略以红色高亮

策略墓地
• 已停止或濒危的策略归档
• 帮助复盘策略的实际生命周期

最新加入
• 最近测序的策略
• 快速导航到策略地图、回测中心、模拟盘`,
  },
  {
    key: 'health',
    icon: '💚',
    title: '健康度指标详解',
    content: `健康度是策略「出生质量」的综合评分：

计算公式
健康度 = 50 + 多样性 × 30 + 有风控基因 × 10 + 有 ML 基因 × 5

分项解读
• 多样性（0-30 分）：策略使用的独特基因越多，得分越高。单一指标依赖的策略得分低。
• 风控（0-10 分）：检测到止损、仓位管理、回撤限制等基因时加分。
• ML（0-5 分）：检测到 sklearn、PyTorch、XGBoost 等机器学习库时加分。

健康度 ≠ 盈利能力
健康度衡量的是策略的「结构性稳健性」，不是回测收益。一个健康度高的策略可能在特定市场环境下收益一般，但它更可能在风格切换时存活下来。`,
  },
  {
    key: 'risk',
    icon: '⚠️',
    title: '近亲风险与多样性',
    content: `近亲风险是 QuantEvo 的核心理念之一：

什么是近亲风险？
当多个策略的基因向量高度相似时，它们会对相同的市场信号做出类似的反应。一旦该信号失效，这些策略会同时亏损。

如何降低近亲风险？
• 确保生态中有多个家族的策略
• 避免导入过多同一家族的策略
• 创建策略时混搭不同指标（如趋势+均值回归）
• 关注「系统发育」中的近亲警告

多样性建议
• 理想生态：至少 3 个家族，每个家族 2-4 个策略
• 动量家族和趋势跟踪家族通常相似度高，不宜同时大量持仓
• 多因子和风控增强家族可提供良好的互补性`,
  },
  {
    key: 'metabolic',
    icon: '🔥',
    title: '代谢分析与寿命预测',
    content: `代谢率反映策略的信息更新频率和逻辑复杂度：

• 高代谢策略：频繁调仓、多层嵌套逻辑、大量指标计算
• 低代谢策略：低频交易、简洁逻辑、长周期持仓

寿命预测基于四个维度：
1. 代谢率：越高寿命越短（过度优化容易失效）
2. 生态位宽度：覆盖越多市场状态，寿命越长
3. 同质化压力：与亲属越相似，竞争压力越大
4. 代谢综合征：高代谢+窄生态位，寿命折半

寿命阶段
• 年轻（36+ 月）：刚创建或低频策略，潜力期
• 成熟（12-36 月）：表现稳定，最佳运行期
• 衰老（3-12 月）：需谨慎监控，准备替代方案
• 濒危（<3 月）：高概率即将失效，建议停止或重构`,
  },
  {
    key: 'integration1',
    icon: '🔍',
    title: '回测中心生态预审（方案一）',
    content: `在创建回测前，系统会自动进行生态预审：

近亲繁殖警告
• 当策略同质化风险 >50% 时，创建回测会弹出警告
• 提醒用户回测结果可能无法反映真实差异化表现
• 可选择继续或更换策略

回测周期推荐
• 根据策略代谢率智能推荐回测时长
• 高代谢策略（>30%）：建议 1-3 个月，避免过拟合
• 中等代谢（15-30%）：建议 3-6 个月
• 低代谢策略（<15%）：可回测 6-12 个月

生态预览
• 策略选择器下方实时显示该策略的健康度、家族归属
• 一键跳转基因报告`,
  },
  {
    key: 'integration2',
    icon: '⏳',
    title: '模拟盘寿命倒计时（方案二）',
    content: `模拟盘监控集成寿命倒计时功能：

寿命状态列
• 每个运行中的会话显示当前寿命阶段（年轻/成熟/衰老/濒危）
• 濒危状态以红色脉冲动画警示
• 未测序的策略显示「未测序」

停盘死因归档
• 停止模拟盘时需要选择停止原因
• 可选：策略失效、达到目标、止损退出、手动停止、其他
• 原因记录便于后续复盘和生态分析

策略墓地
• 页面底部自动归档所有已停止的会话
• 显示会话 ID、策略 ID、停止原因、停止日期
• 帮助追踪策略的实际生命周期`,
  },
  {
    key: 'integration3',
    icon: '👁️',
    title: '策略工坊基因实时预览（方案三）',
    content: `在策略工坊编写代码时，系统每 3 秒自动生成基因预览：

实时基因分析
• 输入代码 3 秒后自动触发预览（无需保存）
• 显示健康度、多样性、代谢率三个核心指标
• 以颜色编码直观展示策略健康状态

基因标签预览
• 特征层：检测到的技术指标基因
• 信号层：识别交易逻辑基因
• 风控层：发现风控机制基因

相似度预警
• 实时比对已有策略的基因重叠度
• 重叠度 >50% 时发出近亲繁殖警告
• 提示与哪个策略最为相似

使用建议
• 编写过程中关注预览变化，及时调整代码结构
• 发现健康度低时，考虑添加风控或多样化指标
• 收到相似度警告时，刻意引入差异化逻辑`,
  },
  {
    key: 'integration4',
    icon: '🔔',
    title: '生态预警与全局导航（方案四）',
    content: `首页导航集成生态预警系统：

导航栏徽章
• 当存在濒危或短寿命策略时，首页导航项显示红色脉冲徽章
• 徽章数字表示需要关注的策略数量
• 每 5 分钟自动刷新

基因报告快捷操作
• 每个策略的基因报告页顶部新增操作按钮
• 快速跳转：编辑策略、创建回测、启动模拟盘
• 减少在不同模块间切换的操作成本

生态联动
• 从基因报告可直接进入回测中心并预填策略 ID
• 从基因报告可直接进入模拟盘监控并选择该策略`,
  },
  {
    key: 'integration5',
    icon: '🏷️',
    title: '模块级生态浮层（方案五）',
    content: `各业务模块内嵌生态信息浮层：

回测中心
• 创建回测时，策略选择器下方显示该策略的生态迷你卡片
• 健康度色点 + 分数 + 家族名 + 基因报告链接

模拟盘监控
• 创建模拟盘会话时，同样显示生态迷你卡片
• 帮助在启动模拟盘前快速评估策略质量

策略工坊
• 左侧策略列表每项前显示健康度色点
• 绿色（≥80）、橙色（60-79）、棕色（<60）
• 空点表示未测序
• 列表项内可直接跳转基因报告`,
  },
  {
    key: 'bestpractice',
    icon: '💡',
    title: '最佳实践',
    content: `构建健康策略生态的建议：

1. 从策略地图导入 5-10 个不同家族的策略作为种子
2. 在策略工坊中基于种子策略进行变异（修改参数、添加风控）
3. 每次创建新策略后查看基因报告，确保引入新的基因
4. 定期查看首页仪表盘，关注健康度下降的策略
5. 当近亲风险过高时，导入或创建来自陌生家族的策略
6. 回测表现好的策略不一定健康——检查其基因多样性
7. 模拟盘运行时观察策略间的相关性，与基因相似度交叉验证
8. 关注寿命倒计时，在策略进入衰老期前准备替代方案
9. 利用实时预览在编写阶段就优化基因结构
10. 回测前查看生态预审警告，避免对近亲策略过度自信

常见误区
• ❌ 只使用趋势跟踪策略（近亲风险极高）
• ❌ 大量复制同一策略只改参数（基因几乎相同）
• ❌ 忽视风控层（健康度上限被锁定）
• ❌ 对濒危策略继续运行模拟盘（高风险）
• ✅ 跨家族组合（趋势+均值回归+多因子）
• ✅ 每个策略有独特的指标组合
• ✅ 回测前查看生态预审和周期推荐`,
  },
]
</script>

<template>
  <div class="manual">
    <section class="manual-hero">
      <h1 class="manual-hero-title">
        <span class="manual-hero-icon">📖</span>
        使用手册
      </h1>
      <p class="manual-hero-desc">
        QuantEvo 生态系统的完整指南。理解策略基因、健康度、亲属关系，构建抗脆弱的交易策略群落。
      </p>
    </section>

    <div class="manual-toc">
      <div class="toc-grid">
        <button
          v-for="section in sections"
          :key="section.key"
          class="toc-item"
          :class="{ active: activeSection === section.key }"
          @click="toggleSection(section.key)"
        >
          <span class="toc-icon">{{ section.icon }}</span>
          <span class="toc-label">{{ section.title }}</span>
        </button>
      </div>
    </div>

    <div class="manual-content">
      <div
        v-for="section in sections"
        :key="section.key"
        class="section-card"
        :class="{ expanded: activeSection === section.key }"
      >
        <button class="section-header" @click="toggleSection(section.key)">
          <span class="section-icon">{{ section.icon }}</span>
          <h3 class="section-title">{{ section.title }}</h3>
          <span class="section-toggle">{{ activeSection === section.key ? '−' : '+' }}</span>
        </button>
        <div v-show="activeSection === section.key" class="section-body">
          <pre class="section-text">{{ section.content }}</pre>
        </div>
      </div>
    </div>

    <div class="manual-footer">
      <RouterLink to="/strategy-map" class="manual-action">
        <span>🗺️</span> 前往策略地图
      </RouterLink>
      <RouterLink to="/" class="manual-action secondary">
        <span>🌿</span> 查看生态仪表盘
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.manual {
  padding: 0;
  max-width: 720px;
  margin: 0 auto;
}

/* Hero */
.manual-hero {
  margin-bottom: var(--space-3xl);
  padding-bottom: var(--space-xl);
  border-bottom: 1px solid var(--border-subtle);
}

.manual-hero-title {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--space-sm) 0;
  letter-spacing: -0.02em;
}

.manual-hero-icon {
  font-size: 1.3rem;
}

.manual-hero-desc {
  font-size: 0.95rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin: 0;
}

/* TOC */
.manual-toc {
  margin-bottom: var(--space-2xl);
}

.toc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--space-sm);
}

.toc-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: left;
}

.toc-item:hover {
  border-color: var(--border-focus);
  color: var(--text-primary);
}

.toc-item.active {
  background: var(--accent-subtle);
  border-color: var(--accent);
  color: var(--accent);
}

.toc-icon {
  font-size: 1.1rem;
}

.toc-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Content */
.manual-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-bottom: var(--space-3xl);
}

.section-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: border-color 0.2s ease;
}

.section-card.expanded {
  border-color: var(--border-focus);
}

.section-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  background: none;
  border: none;
  width: 100%;
  cursor: pointer;
  color: inherit;
  font: inherit;
  text-align: left;
}

.section-icon {
  font-size: 1.2rem;
}

.section-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  flex: 1;
}

.section-toggle {
  font-size: 1.2rem;
  font-weight: 300;
  color: var(--text-muted);
  width: 24px;
  text-align: center;
}

.section-body {
  padding: 0 var(--space-lg) var(--space-lg) var(--space-lg);
}

.section-text {
  font-family: inherit;
  font-size: 0.9rem;
  line-height: 1.7;
  color: var(--text-secondary);
  white-space: pre-wrap;
  margin: 0;
  padding: var(--space-md);
  background: var(--bg-base);
  border-radius: var(--radius-md);
}

/* Footer */
.manual-footer {
  display: flex;
  gap: var(--space-md);
  flex-wrap: wrap;
  padding-top: var(--space-xl);
  border-top: 1px solid var(--border-subtle);
}

.manual-action {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-lg);
  background: var(--accent);
  color: #fff;
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  font-weight: 500;
  text-decoration: none;
  transition: opacity 0.15s ease;
}

.manual-action:hover {
  opacity: 0.9;
}

.manual-action.secondary {
  background: var(--bg-surface);
  color: var(--text-primary);
  border: 1px solid var(--border-subtle);
}

.manual-action.secondary:hover {
  border-color: var(--border-focus);
  background: var(--bg-surface-hover);
}

/* Responsive */
@media (max-width: 600px) {
  .toc-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>

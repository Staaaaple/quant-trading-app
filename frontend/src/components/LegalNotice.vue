<script setup lang="ts">
interface Props {
  /** 是否显示数据来源声明（akshare/公开数据） */
  showDataSource?: boolean
  /** 是否显示投资建议免责声明 */
  showInvestmentDisclaimer?: boolean
  /** 是否显示隐私/数据使用声明 */
  showPrivacy?: boolean
  /** 是否显示开源许可证声明 */
  showLicense?: boolean
  /** 是否显示爬虫/第三方数据声明 */
  showCrawler?: boolean
  /** 是否折叠显示（默认展开） */
  collapsible?: boolean
  /** 标题覆盖 */
  title?: string
}

withDefaults(defineProps<Props>(), {
  showDataSource: true,
  showInvestmentDisclaimer: true,
  showPrivacy: true,
  showLicense: true,
  showCrawler: true,
  collapsible: false,
  title: '重要法律与合规声明',
})
</script>

<template>
  <div class="legal-notice">
    <div class="legal-notice-header">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/>
        <path d="M12 8v4"/>
        <path d="M12 16h.01"/>
      </svg>
      <span class="legal-notice-title">{{ title }}</span>
    </div>
    <ul class="legal-notice-list">
      <li v-if="showInvestmentDisclaimer">
        <strong>不构成投资建议：</strong>本应用展示的所有组合、策略、标的代码、预期收益及买卖信号均为算法生成的示例，仅供学习交流，不构成任何投资建议。过往业绩不代表未来表现，投资有风险，入市需谨慎。本平台非持牌证券投资顾问。
      </li>
      <li v-if="showDataSource">
        <strong>数据来源：</strong>行情及财经数据来源于 akshare 等公开数据源，数据版权归原数据提供方所有。本应用不对数据的实时性、准确性和完整性作出保证，数据仅供学术研究及学习交流使用。
      </li>
      <li v-if="showCrawler">
        <strong>第三方数据与爬虫：</strong>部分资讯通过公开网络抓取获得，仅用于本地研究与展示，不对内容做任何编辑、保证或再分发授权。如有侵权或违规，请立即停止使用并联系我们删除。
      </li>
      <li v-if="showPrivacy">
        <strong>隐私与数据使用：</strong>使用本应用需要收集投资者画像、投资组合及操作日志等信息，用于生成本地推荐结果。默认使用本地大模型，不会将您的数据发送至第三方；如切换到 OpenAI 等在线模型，相关数据将上传至对应服务商，请仔细阅读《隐私政策》与《用户协议》。
      </li>
      <li v-if="showLicense">
        <strong>开源许可：</strong>本项目代码按 MIT 许可证开源（详见项目根目录 LICENSE 文件），第三方依赖及模型享有各自独立许可证。运行本应用即表示您同意遵守相关开源协议。
      </li>
    </ul>
  </div>
</template>

<style scoped>
.legal-notice {
  background: linear-gradient(180deg, #fffbeb 0%, #fff 100%);
  border: 1px solid rgba(217, 119, 6, 0.18);
  border-left: 4px solid #d97706;
  border-radius: 14px;
  padding: 14px 16px;
  margin-bottom: 16px;
  color: #78350f;
}

.legal-notice-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  color: #92400e;
  font-weight: 700;
  font-size: 0.85rem;
}

.legal-notice-header svg {
  flex-shrink: 0;
}

.legal-notice-title {
  letter-spacing: -0.01em;
}

.legal-notice-list {
  margin: 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.legal-notice-list li {
  font-size: 0.75rem;
  line-height: 1.6;
  color: #78350f;
}

.legal-notice-list li strong {
  color: #92400e;
  font-weight: 600;
}

@media (min-width: 768px) {
  .legal-notice {
    padding: 18px 20px;
  }

  .legal-notice-list li {
    font-size: 0.78rem;
  }
}
</style>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useUserStore } from '@/stores/user'

const props = defineProps<{
  portfolioId?: number
  strategyId?: string
  feedbackType?: string
}>()

const emit = defineEmits<['submitted']>()

const userStore = useUserStore()
const showPanel = ref(false)
const submitting = ref(false)
const submitted = ref(false)

const overallRating = ref(0)
const returnRating = ref(0)
const riskRating = ref(0)
const usabilityRating = ref(0)
const pros = ref('')
const cons = ref('')
const suggestion = ref('')
const willingToInterview = ref(false)

const hoverRating = ref(0)

function setOverall(n: number) {
  overallRating.value = n
}

const canSubmit = computed(() => {
  return overallRating.value > 0
})

async function submit() {
  if (!canSubmit.value) return
  submitting.value = true

  try {
    const userId = userStore.currentUserId || 1
    const resp = await fetch('/api/v1/feedbacks', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Id': String(userId),
      },
      body: JSON.stringify({
        portfolio_id: props.portfolioId,
        strategy_id: props.strategyId,
        feedback_type: props.feedbackType || 'general',
        overall_rating: overallRating.value,
        return_rating: returnRating.value || null,
        risk_rating: riskRating.value || null,
        usability_rating: usabilityRating.value || null,
        pros: pros.value || null,
        cons: cons.value || null,
        suggestion: suggestion.value || null,
        willing_to_interview: willingToInterview.value ? 1 : 0,
      }),
    })

    if (resp.ok) {
      submitted.value = true
      emit('submitted')
      setTimeout(() => {
        showPanel.value = false
        reset()
      }, 2000)
    }
  } catch (e) {
    console.error('反馈提交失败:', e)
  } finally {
    submitting.value = false
  }
}

function reset() {
  overallRating.value = 0
  returnRating.value = 0
  riskRating.value = 0
  usabilityRating.value = 0
  pros.value = ''
  cons.value = ''
  suggestion.value = ''
  willingToInterview.value = false
  submitted.value = false
}

function open() {
  showPanel.value = true
}

function close() {
  showPanel.value = false
  reset()
}

// 导出 open 方法供父组件调用
defineExpose({ open })
</script>

<template>
  <!-- Trigger Button -->
  <button class="feedback-trigger" @click="open">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    </svg>
    反馈
  </button>

  <!-- Modal -->
  <div v-if="showPanel" class="feedback-modal">
    <div class="modal-overlay" @click="close"></div>
    <div class="modal-content">
      <div v-if="submitted" class="submitted-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
          <polyline points="22 4 12 14.01 9 11.01"/>
        </svg>
        <h3>感谢你的反馈</h3>
        <p>你的意见将帮助我们优化推荐策略</p>
      </div>

      <template v-else>
        <div class="modal-header">
          <h3>使用反馈</h3>
          <button class="close-btn" @click="close">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 6 6 18"/>
              <path d="m6 6 12 12"/>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <!-- 总体评分 -->
          <div class="rating-group">
            <label>总体满意度 <span class="required">*</span></label>
            <div class="stars">
              <button
                v-for="n in 5"
                :key="n"
                class="star-btn"
                :class="{ active: n <= (hoverRating || overallRating) }"
                @mouseenter="hoverRating = n"
                @mouseleave="hoverRating = 0"
                @click="setOverall(n)"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"
                  :class="{ filled: n <= (hoverRating || overallRating) }"
                >
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- 细分评分 -->
          <div class="rating-row">
            <div class="rating-group small">
              <label>收益表现</label>
              <div class="stars small">
                <button v-for="n in 5" :key="n" class="star-btn" :class="{ active: n <= returnRating }" @click="returnRating = n"
                  @mouseenter="hoverRating = n" @mouseleave="hoverRating = 0"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" :class="{ filled: n <= returnRating }"
                    @click="returnRating = n"
                  >
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                  </svg>
                </button>
              </div>
            </div>
            <div class="rating-group small">
              <label>风险控制</label>
              <div class="stars small">
                <button v-for="n in 5" :key="n" class="star-btn" :class="{ active: n <= riskRating }" @click="riskRating = n"
                  @mouseenter="hoverRating = n" @mouseleave="hoverRating = 0"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" :class="{ filled: n <= riskRating }"
                    @click="riskRating = n"
                  >
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                  </svg>
                </button>
              </div>
            </div>
            <div class="rating-group small">
              <label>易用性</label>
              <div class="stars small">
                <button v-for="n in 5" :key="n" class="star-btn" :class="{ active: n <= usabilityRating }" @click="usabilityRating = n"
                  @mouseenter="hoverRating = n" @mouseleave="hoverRating = 0"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" :class="{ filled: n <= usabilityRating }"
                    @click="usabilityRating = n"
                  >
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- 文字反馈 -->
          <div class="text-group">
            <label>优点</label>
            <textarea v-model="pros" rows="2" placeholder="哪些方面做得好？"></textarea>
          </div>

          <div class="text-group">
            <label>不足</label>
            <textarea v-model="cons" rows="2" placeholder="哪些方面需要改进？"></textarea>
          </div>

          <div class="text-group">
            <label>建议</label>
            <textarea v-model="suggestion" rows="2" placeholder="有什么具体建议？"></textarea>
          </div>

          <label class="checkbox-label">
            <span class="check-box" :class="{ checked: willingToInterview }" @click="willingToInterview = !willingToInterview"
              @click="willingToInterview = !willingToInterview"
            >
              <svg v-if="willingToInterview" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"
                @click="willingToInterview = !willingToInterview"
              >
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </span>
            <span>愿意参与后续优化访谈</span>
          </label>
        </div>

        <div class="modal-footer">
          <button class="btn-secondary" @click="close">取消</button>
          <button class="btn-primary" :disabled="!canSubmit || submitting" @click="submit"
            @click="submit"
          >
            <span v-if="submitting">提交中...</span>
            <span v-else>提交反馈</span>
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.feedback-trigger {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 16px;
  border: 1px solid rgba(0,0,0,0.08); border-radius: 10px;
  background: #fff; color: #525252;
  font-family: inherit; font-size: 0.8rem; font-weight: 500;
  cursor: pointer; transition: all 0.2s;
}
.feedback-trigger:hover {
  border-color: rgba(0,0,0,0.12); color: #171717;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

/* Modal */
.feedback-modal {
  position: fixed; inset: 0; z-index: 300;
  display: flex; align-items: center; justify-content: center;
}
.modal-overlay {
  position: absolute; inset: 0;
  background: rgba(0,0,0,0.3);
}
.modal-content {
  position: relative;
  background: #fff; border-radius: 20px;
  width: 440px; max-width: 90vw;
  max-height: 85vh; overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
}

.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 24px 0;
}
.modal-header h3 {
  font-size: 1.1rem; font-weight: 700; color: #171717; margin: 0;
}
.close-btn {
  width: 32px; height: 32px; border-radius: 8px;
  border: none; background: transparent;
  color: #a3a3a3; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.close-btn:hover { background: #f5f5f5; color: #171717; }

.modal-body {
  padding: 20px 24px;
  display: flex; flex-direction: column; gap: 16px;
}

.modal-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 0 24px 20px;
}

/* Rating */
.rating-group label {
  display: block; font-size: 0.82rem; font-weight: 600;
  color: #171717; margin-bottom: 8px;
}
.rating-group.small label {
  font-size: 0.75rem; color: #737373; font-weight: 500;
}
.required { color: #ef4444; }

.rating-row {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;
}

.stars {
  display: flex; gap: 4px;
}
.star-btn {
  background: none; border: none; padding: 2px;
  cursor: pointer; color: #e5e5e5;
  transition: color 0.15s; line-height: 0;
}
.star-btn:hover { transform: scale(1.1); }
.star-btn.active, .star-btn .filled {
  color: #f59e0b;
}

/* Text inputs */
.text-group label {
  display: block; font-size: 0.82rem; font-weight: 600;
  color: #171717; margin-bottom: 6px;
}
.text-group textarea {
  width: 100%; padding: 10px 14px;
  border: 1px solid rgba(0,0,0,0.1); border-radius: 12px;
  font-family: inherit; font-size: 0.85rem;
  resize: vertical; outline: none;
  transition: border-color 0.2s;
}
.text-group textarea:focus {
  border-color: #171717;
}

/* Checkbox */
.checkbox-label {
  display: flex; align-items: center; gap: 10px;
  font-size: 0.82rem; color: #525252; cursor: pointer;
}
.check-box {
  width: 18px; height: 18px; border-radius: 5px;
  border: 2px solid #d4d4d4;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; color: #fff;
  transition: all 0.2s;
}
.check-box.checked {
  background: #22c55e; border-color: #22c55e;
}

/* Buttons */
.btn-primary {
  padding: 12px 24px;
  border: none; border-radius: 12px;
  background: #171717; color: #fff;
  font-family: inherit; font-size: 0.85rem; font-weight: 600;
  cursor: pointer; transition: all 0.2s;
}
.btn-primary:hover:not(:disabled) { background: #262626; }
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-secondary {
  padding: 12px 20px;
  border: 1px solid rgba(0,0,0,0.08); border-radius: 12px;
  background: #fff; color: #525252;
  font-family: inherit; font-size: 0.85rem; font-weight: 500;
  cursor: pointer; transition: all 0.2s;
}
.btn-secondary:hover { border-color: rgba(0,0,0,0.12); color: #171717; }

/* Submitted state */
.submitted-state {
  text-align: center; padding: 48px 24px;
}
.submitted-state h3 {
  font-size: 1.1rem; font-weight: 700; color: #171717;
  margin: 16px 0 8px;
}
.submitted-state p {
  font-size: 0.85rem; color: #737373; margin: 0;
}
</style>

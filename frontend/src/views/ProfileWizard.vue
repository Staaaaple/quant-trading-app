<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { profileApi, type Question } from '@/api/profile'
import { userApi } from '@/api/user'

const router = useRouter()

const questions = ref<Question[]>([])
const loading = ref(true)
const currentStep = ref(0)
const answers = ref<Record<string, string>>({})
const submitting = ref(false)

const STEPS = [
  { title: '基本信息', desc: '了解你的投资背景' },
  { title: '风险偏好', desc: '评估你的风险承受能力' },
  { title: '行为特征', desc: '分析你的投资行为模式' },
]

const stepQuestions = computed(() => {
  const start = currentStep.value * 5
  return questions.value.slice(start, start + 5)
})

const progress = computed(() => {
  const total = questions.value.length
  const answered = Object.keys(answers.value).length
  return total > 0 ? Math.round((answered / total) * 100) : 0
})

const canNext = computed(() => {
  return stepQuestions.value.every(q => answers.value[q.id] !== undefined)
})

const canSubmit = computed(() => {
  return questions.value.every(q => answers.value[q.id] !== undefined)
})

async function loadQuestions() {
  loading.value = true
  try {
    questions.value = await profileApi.getQuestions()
  } catch (e) {
    console.error('Failed to load questions:', e)
  } finally {
    loading.value = false
  }
}

function selectOption(qid: string, label: string) {
  answers.value[qid] = label
}

function nextStep() {
  if (currentStep.value < STEPS.length - 1) {
    currentStep.value++
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

async function submit() {
  if (!canSubmit.value) return
  submitting.value = true
  try {
    // Ensure a user exists (create default if none)
    let users = await userApi.list()
    let user = users[0]
    if (!user) {
      user = await userApi.create({ name: 'User_01' })
    }
    await profileApi.create(user.id, answers.value)
    router.push('/')
  } catch (e) {
    console.error('Failed to submit profile:', e)
    alert('提交失败，请重试')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadQuestions()
})
</script>

<template>
  <div class="wizard-page">
    <!-- Textures -->
    <div class="texture-noise"></div>
    <div class="texture-grid"></div>

    <!-- Header -->
    <header class="wizard-header">
      <div class="wizard-header-inner">
        <button class="back-btn" @click="$router.back()">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
        </button>
        <div class="step-info">
          <span class="step-label">Step {{ currentStep + 1 }}/{{ STEPS.length }}</span>
          <span class="step-title">{{ STEPS[currentStep]?.title }}</span>
        </div>
        <div class="step-placeholder"></div>
      </div>

      <!-- Progress bar -->
      <div class="progress-wrap">
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: `${progress}%` }"></div>
        </div>
        <span class="progress-text">{{ progress }}%</span>
      </div>
    </header>

    <!-- Content -->
    <div class="wizard-content">
      <div v-if="loading" class="loading-state">加载中...</div>

      <template v-else>
        <div
          v-for="q in stepQuestions"
          :key="q.id"
          class="question-card"
        >
          <div class="question-num">{{ q?.id?.split('_')?.[0]?.replace('q', '') }}</div>
          <h3 class="question-text">{{ q?.question }}</h3>
          <div class="options-list">
            <button
              v-for="opt in (q?.options || [])"
              :key="opt.label"
              :class="['option-btn', { selected: answers[q?.id] === opt.label }]"
              @click="selectOption(q?.id, opt.label)"
            >
              <span class="option-dot" v-if="q && answers[q.id] === opt.label">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              </span>
              <span class="option-dot empty" v-else-if="q"></span>
              <span class="option-label" v-if="q">{{ opt.label }}</span>
            </button>
          </div>
        </div>
      </template>
    </div>

    <!-- Footer -->
    <div class="wizard-footer">
      <button
        v-if="currentStep > 0"
        class="btn-secondary"
        @click="prevStep"
      >
        上一步
      </button>
      <div v-else></div>

      <button
        v-if="currentStep < STEPS.length - 1"
        class="btn-primary"
        :disabled="!canNext"
        @click="nextStep"
      >
        下一步
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
      </button>
      <button
        v-else
        class="btn-primary"
        :disabled="!canSubmit || submitting"
        @click="submit"
      >
        <span v-if="submitting">计算中...</span>
        <span v-else>完成画像</span>
        <svg v-if="!submitting" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.wizard-page {
  min-height: 100vh;
  background: #fafafa;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* Textures */
.texture-noise {
  position: fixed; inset: 0; z-index: 0;
  opacity: 0.035; pointer-events: none;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  background-repeat: repeat; background-size: 128px 128px;
}
.texture-grid {
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background-image: linear-gradient(rgba(0,0,0,0.028) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,0.028) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: linear-gradient(to bottom, transparent 0%, black 10%, black 90%, transparent 100%);
}

/* Header */
.wizard-header {
  position: sticky; top: 0; z-index: 50;
  background: rgba(250,250,250,0.85);
  backdrop-filter: blur(20px) saturate(1.3);
  border-bottom: 1px solid rgba(0,0,0,0.06);
  padding: 12px 0;
}

.wizard-header-inner {
  max-width: 720px; margin: 0 auto; padding: 0 24px;
  display: flex; align-items: center; justify-content: space-between;
}

.back-btn {
  width: 36px; height: 36px;
  border-radius: 10px; border: 1px solid rgba(0,0,0,0.06);
  background: rgba(255,255,255,0.7);
  display: flex; align-items: center; justify-content: center;
  color: #525252; cursor: pointer; transition: all 0.2s;
}
.back-btn:hover { background: #fff; border-color: rgba(0,0,0,0.1); color: #171717; }

.step-info { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.step-label { font-size: 0.65rem; font-weight: 700; color: #d4d4d4; letter-spacing: 0.08em; text-transform: uppercase; }
.step-title { font-size: 0.9rem; font-weight: 600; color: #171717; letter-spacing: -0.01em; }
.step-placeholder { width: 36px; }

.progress-wrap {
  max-width: 720px; margin: 10px auto 0; padding: 0 24px;
  display: flex; align-items: center; gap: 10px;
}
.progress-track {
  flex: 1; height: 3px; background: #e5e5e5; border-radius: 999px; overflow: hidden;
}
.progress-fill {
  height: 100%; background: #171717; border-radius: 999px;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.progress-text { font-size: 0.65rem; font-weight: 600; color: #a3a3a3; min-width: 32px; text-align: right; }

/* Content */
.wizard-content {
  flex: 1;
  max-width: 720px; margin: 0 auto; padding: 20px 24px 32px;
  width: 100%; display: flex; flex-direction: column; gap: 14px;
  position: relative; z-index: 1;
}

.loading-state { text-align: center; padding: 60px 0; color: #a3a3a3; font-size: 0.9rem; }

/* Question Card */
.question-card {
  background: #fff;
  border-radius: 20px;
  padding: 24px 22px;
  border: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 1px 3px rgba(0,0,0,0.02);
  transition: all 0.2s ease;
}

.question-num {
  font-size: 0.65rem; font-weight: 700; color: #d4d4d4;
  letter-spacing: 0.08em; margin-bottom: 8px;
}

.question-text {
  font-size: 1.05rem; font-weight: 600; color: #171717;
  letter-spacing: -0.01em; line-height: 1.4; margin-bottom: 18px;
}

.options-list { display: flex; flex-direction: column; gap: 8px; }

.option-btn {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px;
  border-radius: 14px;
  border: 1.5px solid rgba(0,0,0,0.06);
  background: #fafafa;
  cursor: pointer; transition: all 0.2s ease;
  font-family: inherit; text-align: left;
}

.option-btn:hover {
  border-color: rgba(0,0,0,0.1);
  background: #f5f5f5;
}

.option-btn.selected {
  border-color: #171717;
  background: #171717;
  color: #fff;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
}

.option-dot {
  width: 20px; height: 20px;
  border-radius: 50%;
  border: 2px solid #d4d4d4;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; transition: all 0.2s ease;
}

.option-btn.selected .option-dot {
  border-color: #fff; background: #fff; color: #171717;
}

.option-dot.empty { background: transparent; }

.option-label {
  font-size: 0.88rem; font-weight: 500;
  letter-spacing: -0.01em;
}

/* Footer */
.wizard-footer {
  position: fixed; bottom: 0; left: 0; right: 0; z-index: 50;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(20px) saturate(1.3);
  border-top: 1px solid rgba(0,0,0,0.05);
  max-width: 720px; margin: 0 auto;
  padding: 12px 24px calc(12px + env(safe-area-inset-bottom, 0px));
  display: flex; align-items: center; justify-content: space-between;
}

.btn-primary {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  padding: 14px 24px;
  border: none; border-radius: 14px;
  background: #171717; color: #fff;
  font-family: inherit; font-size: 0.88rem; font-weight: 600;
  letter-spacing: -0.01em; cursor: pointer;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.btn-primary:hover { background: #262626; transform: translateY(-1px); box-shadow: 0 8px 24px rgba(0,0,0,0.15); }
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; transform: none; box-shadow: none; }

.btn-secondary {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  padding: 14px 24px;
  border: 1px solid rgba(0,0,0,0.08); border-radius: 14px;
  background: #fff; color: #525252;
  font-family: inherit; font-size: 0.88rem; font-weight: 500;
  cursor: pointer; transition: all 0.2s ease;
}
.btn-secondary:hover { border-color: rgba(0,0,0,0.12); color: #171717; }
</style>

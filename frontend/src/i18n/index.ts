import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN.json'
import ja from './locales/ja.json'
import en from './locales/en.json'

const messages = {
  'zh-CN': zhCN,
  ja,
  en,
}

const savedLocale = localStorage.getItem('locale') || 'zh-CN'

export const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'zh-CN',
  messages,
})

export const supportedLocales = [
  { code: 'zh-CN', name: '中文' },
  { code: 'ja', name: '日本語' },
  { code: 'en', name: 'English' },
] as const

export type SupportedLocale = (typeof supportedLocales)[number]['code']

import { reactive } from 'vue'
import en from './en'
import zh from './zh'

const messages = { en, zh }

export const i18n = reactive({
  locale: localStorage.getItem('locale') || 'zh',
  messages,
  t(key) {
    const keys = key.split('.')
    let value = this.messages[this.locale]
    for (const k of keys) {
      value = value[k]
      if (!value) return key
    }
    return value
  },
  setLocale(locale) {
    this.locale = locale
    localStorage.setItem('locale', locale)
  }
})

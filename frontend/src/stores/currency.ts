import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getSettings } from '@/api/admin/settings'
import type { PublicSettings } from '@/types'

export type DisplayCurrency = 'USD' | 'CNY'

const STORAGE_KEY = 'sub2_display_currency'
const EXCHANGE_RATE_KEY = 'sub2_exchange_rate'

function loadCurrency(): DisplayCurrency {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'USD' || saved === 'CNY') {
      return saved
    }
  } catch (e) {
    // ignore
  }
  return 'USD'
}

function loadExchangeRate(): number {
  try {
    const saved = localStorage.getItem(EXCHANGE_RATE_KEY)
    if (saved) {
      const rate = parseFloat(saved)
      if (!isNaN(rate) && rate > 0) {
        return rate
      }
    }
  } catch (e) {
    // ignore
  }
  return 0
}

export const useCurrencyStore = defineStore('currency', () => {
  const displayCurrency = ref<DisplayCurrency>(loadCurrency())
  const exchangeRate = ref<number>(loadExchangeRate())
  const initialized = ref(false)

  const currencySymbol = computed(() => {
    return displayCurrency.value === 'USD' ? '$' : '¥'
  })

  const currencyCode = computed(() => displayCurrency.value)

  function setCurrency(currency: DisplayCurrency) {
    displayCurrency.value = currency
    try {
      localStorage.setItem(STORAGE_KEY, currency)
    } catch (e) {
      // ignore
    }
  }

  function toggleCurrency() {
    setCurrency(displayCurrency.value === 'USD' ? 'CNY' : 'USD')
  }

  function setExchangeRate(rate: number) {
    if (rate > 0) {
      exchangeRate.value = rate
      try {
        localStorage.setItem(EXCHANGE_RATE_KEY, rate.toString())
      } catch (e) {
        // ignore
      }
    }
  }

  async function initFromSettings() {
    if (initialized.value) return
    try {
      const settings = await getSettings()
      if (settings.default_display_currency) {
        displayCurrency.value = settings.default_display_currency
      }
      if (settings.default_exchange_rate) {
        exchangeRate.value = settings.default_exchange_rate
      }
      initialized.value = true
    } catch (e) {
      // ignore - use localStorage fallback
    }
  }

  function initFromInjectedConfig(config: PublicSettings) {
    if (config.default_display_currency) {
      displayCurrency.value = config.default_display_currency as DisplayCurrency
      try {
        localStorage.setItem(STORAGE_KEY, config.default_display_currency)
      } catch (e) {
        // ignore
      }
    }
    if (config.default_exchange_rate && config.default_exchange_rate > 0) {
      exchangeRate.value = config.default_exchange_rate
      try {
        localStorage.setItem(EXCHANGE_RATE_KEY, config.default_exchange_rate.toString())
      } catch (e) {
        // ignore
      }
    }
    initialized.value = true
  }

  function convertAmount(amount: number | null | undefined): number {
    if (amount === null || amount === undefined) return 0
    if (displayCurrency.value === 'USD') return amount
    return amount * exchangeRate.value
  }

  function formatAmount(amount: number | null | undefined): string {
    if (amount === null || amount === undefined) {
      return displayCurrency.value === 'USD' ? '$0.00' : '¥0.00'
    }

    const converted = displayCurrency.value === 'USD' 
      ? amount 
      : amount * exchangeRate.value

    const fractionDigits = converted > 0 && converted < 0.01 ? 6 : 2
    const symbol = displayCurrency.value === 'USD' ? '$' : '¥'

    return symbol + converted.toLocaleString('zh-CN', {
      minimumFractionDigits: fractionDigits,
      maximumFractionDigits: fractionDigits,
    })
  }

  return {
    displayCurrency,
    exchangeRate,
    currencySymbol,
    currencyCode,
    setCurrency,
    toggleCurrency,
    setExchangeRate,
    initFromSettings,
    initFromInjectedConfig,
    convertAmount,
    formatAmount,
  }
})

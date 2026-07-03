import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getSettings } from '@/api/admin/settings'
import type { PublicSettings } from '@/types'

export type DisplayCurrency = 'USD' | 'CNY'

const STORAGE_KEY = 'sub2_display_currency'

function loadCurrency(): DisplayCurrency | null {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'USD' || saved === 'CNY') {
      return saved
    }
  } catch (e) {
    // ignore
  }
  return null
}



function formatNumberWith6Decimals(num: number): string {
  const rounded = Math.round(num * 1000000) / 1000000
  
  if (Number.isInteger(rounded)) {
    return rounded.toLocaleString('zh-CN')
  }
  
  const str = rounded.toString()
  const parts = str.split('.')
  const integerPart = parseInt(parts[0], 10).toLocaleString('zh-CN')
  let decimalPart = parts[1] || ''
  
  while (decimalPart.length < 6) {
    decimalPart += '0'
  }
  
  return `${integerPart}.${decimalPart}`
}

export const useCurrencyStore = defineStore('currency', () => {
  const displayCurrency = ref<DisplayCurrency | null>(loadCurrency())
  const exchangeRate = ref<number>(1.0)
  const initialized = ref(false)

  const effectiveCurrency = computed(() => {
    return displayCurrency.value || 'USD'
  })

  const currencySymbol = computed(() => {
    return effectiveCurrency.value === 'USD' ? '$' : '¥'
  })

  const currencyCode = computed(() => effectiveCurrency.value)

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
    }
  }

  async function initFromSettings() {
    try {
      const settings = await getSettings()
      if (settings.default_display_currency) {
        displayCurrency.value = settings.default_display_currency
        try {
          localStorage.setItem(STORAGE_KEY, settings.default_display_currency)
        } catch (e) {
          // ignore
        }
      }
      if (settings.default_exchange_rate && settings.default_exchange_rate > 0) {
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
    }
    initialized.value = true
  }

  function convertAmount(amount: number | null | undefined): number {
    if (amount === null || amount === undefined) return 0
    if (effectiveCurrency.value === 'USD') return amount
    return amount * exchangeRate.value
  }

  function formatAmount(amount: number | null | undefined): string {
    if (amount === null || amount === undefined) {
      return effectiveCurrency.value === 'USD' ? '$0.000000' : '¥0.000000'
    }

    const converted = effectiveCurrency.value === 'USD' 
      ? amount 
      : amount * exchangeRate.value

    const symbol = effectiveCurrency.value === 'USD' ? '$' : '¥'
    return symbol + formatNumberWith6Decimals(converted)
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

import { ref, computed } from 'vue';

export type DisplayCurrency = 'USD' | 'CNY';

const STORAGE_KEY = 'sub2_display_currency';
const EXCHANGE_RATE_KEY = 'sub2_exchange_rate';

const defaultExchangeRate = 7.25;

const displayCurrency = ref<DisplayCurrency>(loadCurrency());
const exchangeRate = ref<number>(loadExchangeRate());

function loadCurrency(): DisplayCurrency {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'USD' || saved === 'CNY') {
      return saved;
    }
  } catch (e) {
    // ignore
  }
  return 'USD';
}

function loadExchangeRate(): number {
  try {
    const saved = localStorage.getItem(EXCHANGE_RATE_KEY);
    if (saved) {
      const rate = parseFloat(saved);
      if (!isNaN(rate) && rate > 0) {
        return rate;
      }
    }
  } catch (e) {
    // ignore
  }
  return defaultExchangeRate;
}

export function useCurrency() {
  const setCurrency = (currency: DisplayCurrency) => {
    displayCurrency.value = currency;
    try {
      localStorage.setItem(STORAGE_KEY, currency);
    } catch (e) {
      // ignore
    }
  };

  const toggleCurrency = () => {
    setCurrency(displayCurrency.value === 'USD' ? 'CNY' : 'USD');
  };

  const setExchangeRate = (rate: number) => {
    if (rate > 0) {
      exchangeRate.value = rate;
      try {
        localStorage.setItem(EXCHANGE_RATE_KEY, rate.toString());
      } catch (e) {
        // ignore
      }
    }
  };

  const convertAmount = (amount: number | null | undefined): number => {
    if (amount === null || amount === undefined) return 0;
    if (displayCurrency.value === 'USD') return amount;
    return amount * exchangeRate.value;
  };

  const currencySymbol = computed(() => {
    return displayCurrency.value === 'USD' ? '$' : '¥';
  });

  const currencyCode = computed(() => displayCurrency.value);

  return {
    displayCurrency,
    exchangeRate,
    currencySymbol,
    currencyCode,
    setCurrency,
    toggleCurrency,
    setExchangeRate,
    convertAmount,
  };
}

export function formatDisplayCurrency(amount: number | null | undefined): string {
  const { displayCurrency, exchangeRate } = useCurrency();
  
  if (amount === null || amount === undefined) {
    return displayCurrency.value === 'USD' ? '$0.00' : '¥0.00';
  }

  const converted = displayCurrency.value === 'USD' 
    ? amount 
    : amount * exchangeRate.value;

  const fractionDigits = converted > 0 && converted < 0.01 ? 6 : 2;
  const symbol = displayCurrency.value === 'USD' ? '$' : '¥';

  return symbol + converted.toLocaleString('zh-CN', {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
}

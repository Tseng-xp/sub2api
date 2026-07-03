import { computed } from 'vue';
import { useCurrencyStore } from '@/stores/currency';

export type DisplayCurrency = 'USD' | 'CNY';

export function useCurrency() {
  const currencyStore = useCurrencyStore();

  const displayCurrency = computed(() => currencyStore.displayCurrency || 'USD');
  const exchangeRate = computed(() => currencyStore.exchangeRate);
  const currencySymbol = computed(() => currencyStore.currencySymbol);
  const currencyCode = computed(() => currencyStore.currencyCode);

  const setCurrency = (currency: DisplayCurrency) => {
    currencyStore.setCurrency(currency);
  };

  const toggleCurrency = () => {
    currencyStore.toggleCurrency();
  };

  const setExchangeRate = (rate: number) => {
    currencyStore.setExchangeRate(rate);
  };

  const convertAmount = (amount: number | null | undefined): number => {
    return currencyStore.convertAmount(amount);
  };

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
  const currencyStore = useCurrencyStore();
  return currencyStore.formatAmount(amount);
}
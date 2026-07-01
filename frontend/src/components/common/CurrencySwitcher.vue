<template>
  <div class="relative" ref="dropdownRef">
    <button
      @click="toggleDropdown"
      class="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-dark-700"
      :title="currentCurrencyName"
    >
      <span class="text-base font-bold">{{ currencySymbol }}</span>
      <span class="hidden sm:inline">{{ displayCurrency }}</span>
      <Icon
        name="chevronDown"
        size="xs"
        class="text-gray-400 transition-transform duration-200"
        :class="{ 'rotate-180': isOpen }"
      />
    </button>

    <transition name="dropdown">
      <div
        v-if="isOpen"
        class="absolute right-0 z-50 mt-1 w-48 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-lg dark:border-dark-700 dark:bg-dark-800"
      >
        <div class="border-b border-gray-100 px-3 py-2 dark:border-dark-700">
          <p class="text-xs font-medium text-gray-500 dark:text-gray-400">显示货币</p>
        </div>
        
        <button
          v-for="currency in currencies"
          :key="currency.code"
          @click="selectCurrency(currency.code)"
          class="flex w-full items-center gap-2 px-3 py-2 text-sm text-gray-700 transition-colors hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-dark-700"
          :class="{
            'bg-primary-50 text-primary-600 dark:bg-primary-900/20 dark:text-primary-400':
              currency.code === displayCurrency
          }"
        >
          <span class="text-base font-bold w-6">{{ currency.symbol }}</span>
          <span>{{ currency.name }}</span>
          <Icon v-if="currency.code === displayCurrency" name="check" size="sm" class="ml-auto text-primary-500" />
        </button>

        <div v-if="displayCurrency === 'CNY'" class="border-t border-gray-100 px-3 py-3 dark:border-dark-700">
          <label class="text-xs font-medium text-gray-500 dark:text-gray-400 block mb-1">汇率 (1 USD = ? CNY)</label>
          <input
            type="number"
            step="0.01"
            min="0.01"
            :value="exchangeRate"
            @input="handleRateChange"
            class="w-full rounded-md border border-gray-300 px-2 py-1 text-sm dark:border-dark-600 dark:bg-dark-700 dark:text-white"
          />
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import Icon from '@/components/icons/Icon.vue'
import { useCurrencyStore, type DisplayCurrency } from '@/stores'

const { displayCurrency, exchangeRate, currencySymbol, setCurrency, setExchangeRate } = useCurrencyStore()

const isOpen = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)

const currencies = [
  { code: 'USD' as DisplayCurrency, symbol: '$', name: '美元 (USD)' },
  { code: 'CNY' as DisplayCurrency, symbol: '¥', name: '人民币 (CNY)' },
]

const currentCurrencyName = computed(() => {
  const c = currencies.find(c => c.code === displayCurrency)
  return c?.name || 'USD'
})

function toggleDropdown() {
  isOpen.value = !isOpen.value
}

function selectCurrency(code: DisplayCurrency) {
  if (code === displayCurrency) {
    return
  }
  setCurrency(code)
}

function handleRateChange(event: Event) {
  const target = event.target as HTMLInputElement
  const rate = parseFloat(target.value)
  if (!isNaN(rate) && rate > 0) {
    setExchangeRate(rate)
  }
}

function handleClickOutside(event: MouseEvent) {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(-4px);
}
</style>

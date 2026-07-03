<template>
  <div class="flex justify-between gap-2">
    <span class="text-gray-500 dark:text-gray-400">{{ label }}</span>
    <span class="font-mono">{{ display }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { formatScaled } from '@/utils/pricing'
import { useCurrencyStore } from '@/stores'

const currencyStore = useCurrencyStore()

const props = withDefaults(
  defineProps<{
    label: string
    value: number | null
    unit: string
    scale: number
    currency?: string
  }>(),
  { value: null, currency: 'USD' }
)

const display = computed(() => {
  if (props.value == null) return '-'
  return `${formatScaled(
    props.value, 
    props.scale, 
    currencyStore.currencySymbol, 
    props.currency,
    currencyStore.exchangeRate,
    currencyStore.displayCurrency || 'USD'
  )} ${props.unit}`
})
</script>

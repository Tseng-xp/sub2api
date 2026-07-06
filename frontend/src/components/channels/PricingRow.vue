<template>
  <div class="flex justify-between gap-2">
    <span class="text-gray-500 dark:text-gray-400">{{ label }}</span>
    <span class="font-mono">{{ display }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { formatScaled } from '@/utils/pricing'
import { useCurrencyStore } from '@/stores/currency'

const props = withDefaults(
  defineProps<{
    label: string
    value: number | null
    unit: string
    scale: number
  }>(),
  { value: null }
)

const currencyStore = useCurrencyStore()

const display = computed(() =>
  props.value == null
    ? '-'
    : `${formatScaled(props.value, props.scale, {
        convert: currencyStore.convertAmount,
        currencySymbol: currencyStore.currencySymbol,
      })} ${props.unit}`
)
</script>

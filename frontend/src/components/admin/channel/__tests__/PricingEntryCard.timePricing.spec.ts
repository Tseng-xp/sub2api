import { shallowMount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import PricingEntryCard from '../PricingEntryCard.vue'
import type { PricingFormEntry } from '../types'

vi.mock('vue-i18n', async importOriginal => ({
  ...await importOriginal<typeof import('vue-i18n')>(),
  useI18n: () => ({ t: (key: string) => key }),
}))

function createEntry(billingMode: PricingFormEntry['billing_mode'] = 'token'): PricingFormEntry {
  return {
    models: [],
    billing_mode: billingMode,
    input_price: null,
    output_price: null,
    cache_write_price: null,
    cache_read_price: null,
    fast_multiplier: null,
    flex_multiplier: null,
    max_reasoning_effort_multiplier: null,
    image_input_price: null,
    image_output_price: null,
    per_request_price: null,
    intervals: [],
    time_pricing: {
      timezone: 'Asia/Shanghai',
      periods: [{ start_time: '09:00', end_time: '12:00', multiplier: '2.00' }],
    },
  }
}

describe('PricingEntryCard time pricing visibility', () => {
  it('is hidden by default', () => {
    const wrapper = shallowMount(PricingEntryCard, {
      props: { entry: createEntry() },
    })

    expect(wrapper.findComponent({ name: 'TimePricingSection' }).exists()).toBe(false)
  })

  it('is shown for token pricing when explicitly enabled', () => {
    const wrapper = shallowMount(PricingEntryCard, {
      props: { entry: createEntry(), enableTimePricing: true },
    })

    expect(wrapper.findComponent({ name: 'TimePricingSection' }).exists()).toBe(true)
  })

  it('is hidden for non-token pricing even when explicitly enabled', () => {
    const wrapper = shallowMount(PricingEntryCard, {
      props: { entry: createEntry('per_request'), enableTimePricing: true },
    })

    expect(wrapper.findComponent({ name: 'TimePricingSection' }).exists()).toBe(false)
  })

  it('clears time periods when changing billing mode', () => {
    const entry = createEntry()
    const wrapper = shallowMount(PricingEntryCard, {
      props: { entry, enableTimePricing: true },
    })

    wrapper.findComponent({ name: 'Select' }).vm.$emit('update:modelValue', 'image')

    expect(wrapper.emitted('update')?.[0]?.[0]).toEqual({
      ...entry,
      billing_mode: 'image',
      intervals: [],
      time_pricing: { timezone: 'Asia/Shanghai', periods: [] },
    })
    expect(entry.time_pricing.periods).toHaveLength(1)
  })
})

describe('PricingEntryCard request multipliers', () => {
  it('shows Fast, Flex, and Max effort controls only when explicitly enabled', () => {
    const hidden = shallowMount(PricingEntryCard, { props: { entry: createEntry() } })
    expect(hidden.text()).not.toContain('admin.channels.form.fastMultiplier')

    const shown = shallowMount(PricingEntryCard, {
      props: { entry: createEntry(), enableTierMultipliers: true },
    })
    expect(shown.text()).toContain('admin.channels.form.fastMultiplier')
    expect(shown.text()).toContain('admin.channels.form.flexMultiplier')
    expect(shown.text()).toContain('admin.channels.form.maxReasoningEffortMultiplier')
  })
})

describe('PricingEntryCard tiered video-token pricing', () => {
  it('adds editable input-mode tiers without hardcoding a model or price', async () => {
    const entry = createEntry('video_token_tiered')
    entry.models = ['custom-video-model']
    const wrapper = shallowMount(PricingEntryCard, { props: { entry } })

    expect(wrapper.text()).toContain('admin.channels.form.videoTokenTierHint')
    const addTier = wrapper.findAll('button').find(button =>
      button.text().includes('admin.channels.form.addTier')
    )
    expect(addTier).toBeDefined()
    await addTier!.trigger('click')

    const firstUpdate = wrapper.emitted('update')?.[0]?.[0] as PricingFormEntry
    expect(firstUpdate.intervals[0].tier_label).toBe('480p_with_ref')
    expect(firstUpdate.intervals[0].per_request_price).toBeNull()
    await wrapper.setProps({ entry: firstUpdate })
    await addTier!.trigger('click')

    const secondUpdate = wrapper.emitted('update')?.[1]?.[0] as PricingFormEntry
    expect(secondUpdate.intervals.map(interval => interval.tier_label)).toEqual([
      '480p_with_ref',
      '480p_no_ref',
    ])
  })

  it('offers Tencent H3 768p and 2k tiers without hardcoded prices', async () => {
	const entry = createEntry('video_token_tiered')
	entry.intervals = [
	  '480p_with_ref', '480p_no_ref', '720p_with_ref', '720p_no_ref',
	].map((tier_label, sort_order) => ({
	  min_tokens: 0, max_tokens: null, tier_label,
	  input_price: null, output_price: null, cache_write_price: null,
	  cache_write_1h_price: null, cache_read_price: null, per_request_price: null,
	  input_multiplier: null, output_multiplier: null,
	  cache_write_multiplier: null, cache_read_multiplier: null, sort_order,
	}))
	const wrapper = shallowMount(PricingEntryCard, { props: { entry } })
	const addTier = wrapper.findAll('button').find(button =>
	  button.text().includes('admin.channels.form.addTier')
	)
	await addTier!.trigger('click')
	const update = wrapper.emitted('update')?.[0]?.[0] as PricingFormEntry
	expect(update.intervals.at(-1)?.tier_label).toBe('768p_with_ref')
  })
})

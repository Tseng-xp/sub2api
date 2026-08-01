interface FormatScaledOptions {
  /** 货币换算函数（通常传 currencyStore.convertAmount）：USD 不变、CNY 乘汇率。不传则不换算。 */
  convert?: (value: number) => number
  /** 货币符号（通常传 currencyStore.currencySymbol）。默认 '$'。 */
  currencySymbol?: string
  /** Minimum number of decimal places to display. */
  minFractionDigits?: number
}

/**
 * formatScaled formats a per-token (or per-request) price scaled by `scale`.
 *
 *   formatScaled(0.000003, 1_000_000)    → "$3"      // per 1M tokens
 *   formatScaled(0.5,        1)          → "$0.5"    // per request
 *   formatScaled(null,       1_000_000)  → "-"
 *   formatScaled(0.000003, 1_000_000, 2) → "$3.00"   // pad to ≥2 decimals
 *   formatScaled(1.25e-8,  1_000_000, 2) → "$0.0125" // longer decimals kept as-is
 *
 * 后端返回的价格是 USD/每 token。传入 options.convert / options.currencySymbol
 * 即可按管理员设置的展示币种换算并显示对应符号（否则默认显示美元）。
 * Uses toPrecision(10) then strips trailing zeros to avoid IEEE 754 display noise.
 * `minFractionDigits` pads the result back up to a minimum number of decimals.
 */
export function formatScaled(
  value: number | null,
  scale: number,
  options: FormatScaledOptions | number = {}
): string {
  if (value == null) return '-'
  const normalizedOptions = typeof options === 'number'
    ? { minFractionDigits: options }
    : options
  let amount = value * scale
  if (normalizedOptions.convert) {
    amount = normalizedOptions.convert(amount)
  }
  let s = amount.toPrecision(10).replace(/\.?0+$/, '')
  const minFractionDigits = normalizedOptions.minFractionDigits ?? 0
  if (minFractionDigits > 0 && !s.includes('e')) {
    const dot = s.indexOf('.')
    const digits = dot === -1 ? 0 : s.length - dot - 1
    if (digits < minFractionDigits) {
      s = (dot === -1 ? `${s}.` : s) + '0'.repeat(minFractionDigits - digits)
    }
  }
  return `${normalizedOptions.currencySymbol ?? '$'}${s}`
}

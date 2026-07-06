interface FormatScaledOptions {
  /** 货币换算函数（通常传 currencyStore.convertAmount）：USD 不变、CNY 乘汇率。不传则不换算。 */
  convert?: (value: number) => number
  /** 货币符号（通常传 currencyStore.currencySymbol）。默认 '$'。 */
  currencySymbol?: string
}

/**
 * formatScaled formats a per-token (or per-request) price scaled by `scale`.
 *
 *   formatScaled(0.000003, 1_000_000) → "$3"        // per 1M tokens
 *   formatScaled(0.5,        1)        → "$0.5"      // per request
 *   formatScaled(null,       1_000_000) → "-"
 *
 * 后端返回的价格是 USD/每 token。传入 options.convert / options.currencySymbol
 * 即可按管理员设置的展示币种换算并显示对应符号（否则默认显示美元）。
 * Uses toPrecision(10) then strips trailing zeros to avoid IEEE 754 display noise.
 */
export function formatScaled(
  value: number | null,
  scale: number,
  options: FormatScaledOptions = {}
): string {
  if (value == null) return '-'
  let amount = value * scale
  if (options.convert) {
    amount = options.convert(amount)
  }
  const symbol = options.currencySymbol ?? '$'
  return `${symbol}${amount.toPrecision(10).replace(/\.?0+$/, '')}`
}

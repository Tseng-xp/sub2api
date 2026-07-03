export function formatScaled(value: number | null, scale: number, symbol: string = '$', currency: string = 'USD', exchangeRate: number = 1.0, displayCurrency: string = 'USD'): string {
  if (value == null) return '-'
  let raw = value * scale
  
  if (exchangeRate <= 0) {
    exchangeRate = 1.0
  }
  
  if (currency === 'USD' && displayCurrency === 'CNY') {
    raw = raw * exchangeRate
  } else if (currency === 'CNY' && displayCurrency === 'USD') {
    raw = raw / exchangeRate
  }
  
  const rounded = Math.round(raw * 1000000) / 1000000
  return `${symbol}${rounded.toPrecision(10).replace(/\.?0+$/, '')}`
}

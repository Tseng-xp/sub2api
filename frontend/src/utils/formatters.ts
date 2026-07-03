/**
 * 格式化缓存 token 数量（1K/1M 缩写）
 */
export function formatCacheTokens(tokens: number): string {
  if (tokens >= 1000000) return `${(tokens / 1000000).toFixed(1)}M`
  if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}K`
  return tokens.toLocaleString()
}

/**
 * 自适应精度格式化倍率（确保小数值如 0.001 不被截断）
 */
export function formatMultiplier(val: number): string {
  const rounded = Math.round(val * 1000000) / 1000000
  
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

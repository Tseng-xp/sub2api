import os
import shutil

project_dir = os.path.dirname(os.path.abspath(__file__))

print("=" * 60)
print("应用自定义修改")
print("=" * 60)

ICP_CODE = "粤ICP备2025408634号-4"

# ============================================================
# 1. 删除 GitHub 链接
# ============================================================
def remove_github_links(filepath):
    full_path = os.path.join(project_dir, filepath)
    if not os.path.exists(full_path):
        return False
    
    with open(full_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    i = 0
    modified = False
    while i < len(lines):
        line = lines[i]
        skip = False
        
        if 'github.com/Wei-Shaw/sub2api' in line or 'href="https://github.com/Wei-Shaw/sub2api"' in line:
            if '</a>' in line:
                skip = True
                modified = True
            else:
                j = i
                while j < len(lines):
                    if '</a>' in lines[j]:
                        i = j
                        skip = True
                        modified = True
                        break
                    j += 1
        
        if 'const githubUrl = ' in line:
            skip = True
            modified = True
        
        if not skip:
            new_lines.append(line)
        i += 1
    
    if modified:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    return False

# ============================================================
# 2. 添加备案号
# ============================================================
def add_icp_footer(filepath):
    full_path = os.path.join(project_dir, filepath)
    if not os.path.exists(full_path):
        return False
    
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if ICP_CODE in content:
        return False
    
    ICP_HTML = f'''
        <div class="mt-4 text-center text-xs text-gray-400 dark:text-dark-500">
          <a href="https://beian.miit.gov.cn" target="_blank" rel="noopener noreferrer" class="hover:text-gray-600 dark:hover:text-dark-300 transition-colors">
            {ICP_CODE}
          </a>
        </div>'''
    
    if '</footer>' in content:
        content = content.replace('</footer>', ICP_HTML + '\n    </footer>')
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False

def add_icp_fixed(filepath):
    full_path = os.path.join(project_dir, filepath)
    if not os.path.exists(full_path):
        return False
    
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if ICP_CODE in content:
        return False
    
    ICP_HTML = f'''
  <footer class="fixed bottom-0 left-64 right-0 py-2 text-center text-xs text-gray-400 dark:text-dark-500 border-t border-gray-200/50 dark:border-dark-800/50 bg-gray-50/80 dark:bg-dark-950/80 backdrop-blur-sm z-50">
    <a href="https://beian.miit.gov.cn" target="_blank" rel="noopener noreferrer" class="hover:text-gray-600 dark:hover:text-dark-300 transition-colors">
      {ICP_CODE}
    </a>
  </footer>'''
    
    if '</template>' in content:
        content = content.replace('</template>', ICP_HTML + '\n</template>')
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False

# ============================================================
# 3. 添加货币切换功能
# ============================================================
def setup_currency_switcher():
    """设置货币切换功能（添加composable和组件）"""
    composable_path = os.path.join(project_dir, "frontend/src/composables/useCurrency.ts")
    component_path = os.path.join(project_dir, "frontend/src/components/common/CurrencySwitcher.vue")
    
    need_setup = not os.path.exists(composable_path) or not os.path.exists(component_path)
    
    if not need_setup:
        return False
    
    # 创建 useCurrency.ts
    composable_content = '''import { ref, computed } from 'vue';

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
'''
    
    os.makedirs(os.path.dirname(composable_path), exist_ok=True)
    with open(composable_path, 'w', encoding='utf-8') as f:
        f.write(composable_content)
    
    # 创建 CurrencySwitcher.vue
    component_content = '''<template>
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
import { useCurrency, type DisplayCurrency } from '@/composables/useCurrency'

const { displayCurrency, exchangeRate, currencySymbol, setCurrency, setExchangeRate } = useCurrency()

const isOpen = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)

const currencies = [
  { code: 'USD' as DisplayCurrency, symbol: '$', name: '美元 (USD)' },
  { code: 'CNY' as DisplayCurrency, symbol: '¥', name: '人民币 (CNY)' },
]

const currentCurrencyName = computed(() => {
  const c = currencies.find(c => c.code === displayCurrency.value)
  return c?.name || 'USD'
})

function toggleDropdown() {
  isOpen.value = !isOpen.value
}

function selectCurrency(code: DisplayCurrency) {
  if (code === displayCurrency.value) {
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
'''
    
    with open(component_path, 'w', encoding='utf-8') as f:
        f.write(component_content)
    
    return True

def add_currency_switcher_to_header():
    """在AppHeader中添加货币切换器"""
    filepath = "frontend/src/components/layout/AppHeader.vue"
    full_path = os.path.join(project_dir, filepath)
    if not os.path.exists(full_path):
        return False
    
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    # 1. 添加导入
    if "import CurrencySwitcher from" not in content:
        content = content.replace(
            "import LocaleSwitcher from '@/components/common/LocaleSwitcher.vue'",
            "import LocaleSwitcher from '@/components/common/LocaleSwitcher.vue'\nimport CurrencySwitcher from '@/components/common/CurrencySwitcher.vue'\nimport { formatDisplayCurrency } from '@/composables/useCurrency'"
        )
        modified = True
    
    # 2. 添加货币切换器组件（在语言切换器之前）
    if "<CurrencySwitcher />" not in content:
        content = content.replace(
            "<!-- Language Switcher -->\n        <LocaleSwitcher />",
            "<!-- Currency Switcher -->\n        <CurrencySwitcher />\n\n        <!-- Language Switcher -->\n        <LocaleSwitcher />"
        )
        modified = True
    
    # 3. 修改余额显示（顶部导航栏）
    if "${{ user.balance" in content:
        content = content.replace(
            "${{ user.balance?.toFixed(2) || '0.00' }}",
            "{{ formatDisplayCurrency(user.balance) }}"
        )
        modified = True
    
    # 4. 修改下拉菜单中的余额显示
    if "text-sm font-semibold text-primary-600" in content and "${{ user.balance" in content:
        # 找到第二个余额显示（下拉菜单中）
        parts = content.split("${{ user.balance?.toFixed(2) || '0.00' }}")
        if len(parts) >= 2:
            content = parts[0] + "{{ formatDisplayCurrency(user.balance) }}" + parts[1]
            # 还有更多的话继续替换
            for i in range(2, len(parts)):
                # 后续的不替换了，只替换前两个
                content += "{{ formatDisplayCurrency(user.balance) }}" + parts[i]
            modified = True
    
    if modified:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def update_key_usage_view():
    """更新KeyUsageView的货币显示"""
    filepath = "frontend/src/views/KeyUsageView.vue"
    full_path = os.path.join(project_dir, filepath)
    if not os.path.exists(full_path):
        return False
    
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    # 添加导入
    if "formatDisplayCurrency" not in content:
        if "import Icon from '@/components/icons/Icon.vue'" in content:
            content = content.replace(
                "import Icon from '@/components/icons/Icon.vue'",
                "import Icon from '@/components/icons/Icon.vue'\nimport { formatDisplayCurrency } from '@/composables/useCurrency'"
            )
            modified = True
    
    # 修改 usd 函数
    if "return '$' + Number(value).toFixed(2)" in content:
        content = content.replace(
            "return '$' + Number(value).toFixed(2)",
            "return formatDisplayCurrency(value)"
        )
        modified = True
    
    if modified:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def update_keys_view():
    """更新KeysView的货币显示"""
    filepath = "frontend/src/views/user/KeysView.vue"
    full_path = os.path.join(project_dir, filepath)
    if not os.path.exists(full_path):
        return False
    
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    # 添加导入
    if "formatDisplayCurrency" not in content:
        if "import { formatDateTime } from '@/utils/format'" in content:
            content = content.replace(
                "import { formatDateTime } from '@/utils/format'",
                "import { formatDateTime } from '@/utils/format'\nimport { formatDisplayCurrency } from '@/composables/useCurrency'"
            )
            modified = True
    
    # 替换 quota 显示
    if "${{ row.quota_used?.toFixed(2) || '0.00' }} / ${{ row.quota?.toFixed(2) }}" in content:
        content = content.replace(
            "${{ row.quota_used?.toFixed(2) || '0.00' }} / ${{ row.quota?.toFixed(2) }}",
            "{{ formatDisplayCurrency(row.quota_used) }} / {{ formatDisplayCurrency(row.quota) }}"
        )
        modified = True
    
    # 替换 rate_limit 显示
    patterns = [
        ("${{ row.usage_5h?.toFixed(2) || '0.00' }}/${{ row.rate_limit_5h?.toFixed(2) }}",
         "{{ formatDisplayCurrency(row.usage_5h) }}/{{ formatDisplayCurrency(row.rate_limit_5h) }}"),
        ("${{ row.usage_1d?.toFixed(2) || '0.00' }}/${{ row.rate_limit_1d?.toFixed(2) }}",
         "{{ formatDisplayCurrency(row.usage_1d) }}/{{ formatDisplayCurrency(row.rate_limit_1d) }}"),
        ("${{ row.usage_7d?.toFixed(2) || '0.00' }}/${{ row.rate_limit_7d?.toFixed(2) }}",
         "{{ formatDisplayCurrency(row.usage_7d) }}/{{ formatDisplayCurrency(row.rate_limit_7d) }}"),
    ]
    
    for old, new in patterns:
        if old in content:
            content = content.replace(old, new)
            modified = True
    
    if modified:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def update_account_stats_cell():
    """更新AccountTodayStatsCell的货币显示"""
    filepath = "frontend/src/components/account/AccountTodayStatsCell.vue"
    full_path = os.path.join(project_dir, filepath)
    if not os.path.exists(full_path):
        return False
    
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    # 修改导入
    if "formatCurrency" in content and "formatDisplayCurrency" not in content:
        content = content.replace(
            "import { formatNumber, formatCurrency } from '@/utils/format'",
            "import { formatNumber } from '@/utils/format'\nimport { formatDisplayCurrency } from '@/composables/useCurrency'"
        )
        modified = True
    
    # 替换 formatCurrency 调用
    if "formatCurrency(props.stats.cost)" in content:
        content = content.replace(
            "formatCurrency(props.stats.cost)",
            "formatDisplayCurrency(props.stats.cost)"
        )
        modified = True
    
    if "formatCurrency(props.stats.user_cost)" in content:
        content = content.replace(
            "formatCurrency(props.stats.user_cost)",
            "formatDisplayCurrency(props.stats.user_cost)"
        )
        modified = True
    
    if modified:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

# ============================================================
# 执行所有自定义修改
# ============================================================

print("\n--- 1. 删除 GitHub 链接 ---")
github_files = [
    "frontend/src/views/HomeView.vue",
    "frontend/src/views/KeyUsageView.vue",
    "frontend/src/components/layout/AppHeader.vue",
]
for f in github_files:
    if remove_github_links(f):
        print(f"  ✓ {f}")
    else:
        print(f"  - {f}")

print("\n--- 2. 添加备案号 ---")
icp_files = [
    ("frontend/src/views/HomeView.vue", "footer"),
    ("frontend/src/views/KeyUsageView.vue", "footer"),
    ("frontend/src/components/layout/AuthLayout.vue", "footer"),
    ("frontend/src/components/layout/AppLayout.vue", "fixed"),
]
for f, mode in icp_files:
    if mode == "footer":
        result = add_icp_footer(f)
    else:
        result = add_icp_fixed(f)
    if result:
        print(f"  ✓ {f}")
    else:
        print(f"  - {f}")

print("\n--- 3. 设置货币切换功能 ---")
if setup_currency_switcher():
    print("  ✓ 创建 useCurrency.ts 和 CurrencySwitcher.vue")
else:
    print("  - 货币切换组件已存在")

if add_currency_switcher_to_header():
    print("  ✓ 更新 AppHeader.vue")
else:
    print("  - AppHeader.vue 无需更新")

if update_key_usage_view():
    print("  ✓ 更新 KeyUsageView.vue")
else:
    print("  - KeyUsageView.vue 无需更新")

if update_keys_view():
    print("  ✓ 更新 KeysView.vue")
else:
    print("  - KeysView.vue 无需更新")

if update_account_stats_cell():
    print("  ✓ 更新 AccountTodayStatsCell.vue")
else:
    print("  - AccountTodayStatsCell.vue 无需更新")

print("\n" + "=" * 60)
print("自定义修改应用完成！")
print("=" * 60)
print("\n已应用的修改：")
print("  1. 删除 GitHub 链接")
print("  2. 添加备案号（粤ICP备2025408634号-4）")
print("  3. 添加货币切换功能（美元/人民币）")
print("\n提示：每次从 GitHub 拉取新版本后，运行此脚本即可恢复所有自定义修改。")

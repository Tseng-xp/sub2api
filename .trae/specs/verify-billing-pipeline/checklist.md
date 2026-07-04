# Checklist

## 断言工具
- [ ] `BillingFourWaySnapshot` 结构体包含四个字段：`PublicPricingCost`、`CalculateCostUnifiedCost`、`DBDeductedCost`、`UsageLogCost`
- [ ] `AssertFourWayConsistency` 默认容差 ≤ 1e-9 USD，失败时输出四路具体值便于排查
- [ ] `ComputePublicPricingCost` 支持文本 token、image token、cache_creation（5m/1h）、cache_read、perRequest、image perRequest 六种计费模式
- [ ] `CaptureDBDeductedCost` 正确捕获余额变化量（含 overdraft 场景）
- [ ] `CaptureSubscriptionAccumulation` 正确捕获 daily/weekly/monthly_usage_usd 累加量

## 黄金样本
- [ ] `TestBillingPipelineE2E_PlainText`：1000 input + 500 output，分组倍率 0.8，预期 0.002 USD
- [ ] `TestBillingPipelineE2E_CacheCreation5m`：200 cache_creation(5m) + 500 input + 400 output，cache_creation 按 1.25× input 价
- [ ] `TestBillingPipelineE2E_CacheRead`：300 cache_read + 500 input + 400 output，cache_read 按 0.1× input 价
- [ ] `TestBillingPipelineE2E_ImageInput`：1000 文本 + 2×500 image tokens + 500 output
- [ ] `TestBillingPipelineE2E_PerRequest`：perRequest $0.01 × 倍率 0.8 = 0.008
- [ ] `TestBillingPipelineE2E_SubscriptionBilling`：订阅制扣费，验证 daily/weekly/monthly_usage_usd 累加
- [ ] `TestBillingPipelineE2E_RateMultiplierStack`：分组倍率 × 长上下文 × service tier 叠加
- [ ] 每个黄金样本在注释中记录预期金额的手动计算过程

## 边界场景
- [ ] 订阅→余额切换瞬间的在途请求扣费路径正确
- [ ] 多候选 billingModel 回退时，最终命中定价档的一致性
- [ ] RunModeSimple 下 usage_log cost 与正常模式口径差异已文档化或断言一致

## 单元测试补充
- [ ] `billing_service_test.go` 包含 `rate_multiplier × imageMultiplier` 叠加场景
- [ ] `model_pricing_resolver_test.go` 包含渠道覆盖 LiteLLM 默认价的边界场景

## CI 集成
- [ ] `make test-unit` 运行结果包含 `TestBillingPipelineE2E*` 系列测试
- [ ] 若新增独立 `billing-consistency` job，其在 backend-ci.yml 中配置正确
- [ ] CI 在 PR 上运行计费一致性测试并作为合并门槛

## 不变式
- [ ] 所有测试不修改任何生产代码（仅新增测试文件和断言工具）
- [ ] 所有测试在 `go test -tags=unit ./internal/service/...` 下通过
- [ ] 所有测试在 `go test -tags=integration ./internal/service/...` 下通过（若涉及 DB 集成）
- [ ] 测试覆盖率不降低（相对当前 baseline）

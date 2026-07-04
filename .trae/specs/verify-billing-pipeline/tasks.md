# Tasks

- [ ] Task 1: 创建计费一致性断言工具 `billing_consistency_assertions.go`
  - [ ] SubTask 1.1: 定义 `BillingFourWaySnapshot` 结构体，包含 `PublicPricingCost`、`CalculateCostUnifiedCost`、`DBDeductedCost`、`UsageLogCost` 四个字段
  - [ ] SubTask 1.2: 实现 `AssertFourWayConsistency(t, snapshot, tolerance)` 断言函数，容差默认 1e-9
  - [ ] SubTask 1.3: 实现 `ComputePublicPricingCost(pricing, tokens, rateMultiplier)` 手动计算公示定价
  - [ ] SubTask 1.4: 实现 `CaptureDBDeductedCost(repo, userID, beforeBalance)` 捕获余额变化量
  - [ ] SubTask 1.5: 实现 `CaptureSubscriptionAccumulation(repo, subscriptionID, before)` 捕获订阅累计变化量

- [ ] Task 2: 创建端到端计费测试 `billing_pipeline_e2e_test.go`
  - [ ] SubTask 2.1: 搭建测试 harness（mock 上游 + 内存 DB + 预置渠道/分组/定价），复用 `billing_service_unified_test.go` 的 setup 模式
  - [ ] SubTask 2.2: 实现黄金样本 `TestBillingPipelineE2E_PlainText`：1000 input + 500 output，分组倍率 0.8
  - [ ] SubTask 2.3: 实现黄金样本 `TestBillingPipelineE2E_CacheCreation5m`：200 cache_creation + 500 input + 400 output
  - [ ] SubTask 2.4: 实现黄金样本 `TestBillingPipelineE2E_CacheRead`：300 cache_read + 500 input + 400 output
  - [ ] SubTask 2.5: 实现黄金样本 `TestBillingPipelineE2E_ImageInput`：1000 文本 + 2×500 image tokens + 500 output
  - [ ] SubTask 2.6: 实现黄金样本 `TestBillingPipelineE2E_PerRequest`：perRequest 模式 $0.01/次
  - [ ] SubTask 2.7: 实现黄金样本 `TestBillingPipelineE2E_SubscriptionBilling`：订阅制扣费路径
  - [ ] SubTask 2.8: 实现黄金样本 `TestBillingPipelineE2E_RateMultiplierStack`：分组倍率 × 长上下文 × service tier

- [ ] Task 3: 补充边界场景测试
  - [ ] SubTask 3.1: `TestBillingPipelineE2E_SubscriptionToBalanceSwitch`：订阅→余额切换瞬间的在途请求
  - [ ] SubTask 3.2: `TestBillingPipelineE2E_BillingModelFallback`：多个候选 billingModel 回退的一致性
  - [ ] SubTask 3.3: `TestBillingPipelineE2E_RunModeSimple`：Simple 模式下 usage_log cost 与正常模式口径对比（允许文档化差异）

- [ ] Task 4: 补充单元测试覆盖
  - [ ] SubTask 4.1: 在 `billing_service_test.go` 补充 `rate_multiplier × imageMultiplier` 叠加场景
  - [ ] SubTask 4.2: 在 `model_pricing_resolver_test.go` 补充渠道覆盖 LiteLLM 默认价的边界场景

- [ ] Task 5: CI 集成
  - [ ] SubTask 5.1: 在 `backend-ci.yml` 的 `test` job 中确认 `make test-unit` 已覆盖 `TestBillingPipelineE2E`（若已覆盖则无需新增 job）
  - [ ] SubTask 5.2: 若需独立门禁，新增 `billing-consistency` job 运行 `go test -tags=unit -run "TestBillingPipelineE2E" ./internal/service/...`

# Task Dependencies
- [Task 2] depends on [Task 1]（端到端测试依赖断言工具）
- [Task 3] depends on [Task 1] 和 [Task 2]（边界测试复用 harness）
- [Task 4] 独立，可与 [Task 1] 并行
- [Task 5] depends on [Task 2]（CI 集成依赖测试存在）

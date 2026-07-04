# 计费全流程一致性验证 Spec

## Why
当前 sub2api 的计费链路从 token 用量提取 → 定价解析 → 费用计算 → 余额/订阅扣减 → 使用日志写入涉及 7+ 个文件、多次倍率叠加与候选模型回退。任一环节不一致都会导致用户实际扣费与产品公示定价偏离，且现有测试以单元测试为主，缺少端到端的一致性校验。需要一个全流程检测机制，能在本地和 CI 中验证「产品定价 → 计费计算 → 实际结算」三者一致。

## What Changes
- 新增 `billing_pipeline_e2e_test.go`：端到端计费一致性测试，覆盖 token 计费、perRequest、图片计费三种模式
- 新增 `billing_consistency_assertions.go`：可复用的对账断言工具，对比「公示定价×用量」「CalculateCostUnified 输出」「DB 实际扣费」「UsageLog 记录」四路结果
- 在现有 `RecordUsage` 路径上增加一组「黄金样本」回归测试，覆盖普通文本/缓存读写/图片输入/长上下文/service tier 等场景
- 在 `billing_service_test.go` 中补充 `rate_multiplier` 与 `imageMultiplier` 叠加场景
- 补充订阅制与余额制在「分组切换瞬间」「订阅过期瞬间」的边界一致性测试
- 新增 CI job `billing-consistency` 在 unit test tag 下运行，作为 PR 合并门槛之一

## Impact
- Affected specs: 计费服务、定价解析、使用日志
- Affected code:
  - `backend/internal/service/billing_service.go`（仅测试调用，不改实现）
  - `backend/internal/service/model_pricing_resolver.go`（仅测试调用）
  - `backend/internal/service/openai_gateway_service.go`（仅测试 `RecordUsage`）
  - `backend/internal/service/gateway_service.go`（仅测试 `applyUsageBilling`）
  - `backend/internal/repository/usage_billing_repo.go`（仅集成测试）
  - 新增 `backend/internal/service/billing_pipeline_e2e_test.go`
  - 新增 `backend/internal/service/billing_consistency_assertions.go`
- 不修改任何生产代码逻辑，仅新增测试与对账工具

## ADDED Requirements

### Requirement: 计费四路一致性断言
系统 SHALL 提供一组对账断言工具，对任意一次 `RecordUsage` 调用，能同时验证以下四路结果一致（容差 ≤ 1e-9 USD）：
1. **公示定价路径**：根据渠道配置/LiteLLM 默认价 × 用量 × 倍率手动计算
2. **CalculateCostUnified 输出**：BillingService 返回的 `ActualCost`
3. **DB 实际扣费**：用户余额变化量 或 订阅 daily/weekly/monthly_usage_usd 累加量
4. **UsageLog 记录**：`usage_logs.cost` 字段

#### Scenario: 普通文本请求四路一致
- **WHEN** 用户通过 OpenAI 网关发送一条普通 chat 请求（1000 input + 500 output tokens）
- **AND** 渠道定价配置为 input $1/M、output $3/M
- **AND** 分组倍率为 0.8
- **THEN** 公示定价 = (1000×1 + 500×3) / 1e6 × 0.8 = 0.002 USD
- **AND** `CalculateCostUnified` 返回 `ActualCost = 0.002`
- **AND** 用户余额减少 0.002 USD
- **AND** `usage_logs.cost = 0.002`

#### Scenario: 缓存读写请求四路一致
- **WHEN** 请求包含 200 cache_creation（5m）+ 300 cache_read + 500 新输入 + 400 输出
- **THEN** cache_creation 按 1.25× input 价计费
- **AND** cache_read 按 0.1× input 价计费
- **AND** 四路结果一致

#### Scenario: 图片输入请求四路一致
- **WHEN** 请求包含 1000 文本输入 + 2 张图片（各 500 image tokens）+ 500 输出
- **THEN** image token 按 image_input 单价计费
- **AND** 四路结果一致

#### Scenario: perRequest 模式四路一致
- **WHEN** 渠道配置为 perRequest 模式，每次 $0.01
- **AND** 分组倍率 0.8
- **THEN** 实际扣费 = 0.01 × 0.8 = 0.008
- **AND** 四路结果一致

### Requirement: 黄金样本回归测试
系统 SHALL 维护一组黄金样本（golden cases），覆盖以下场景的完整计费链路：
- 普通文本（input/output）
- 缓存创建 5m / 1h
- 缓存读取
- 图片输入 token
- 长上下文倍率
- service tier（priority/default）
- perRequest 模式
- 图片 perRequest 模式
- 订阅制扣费
- 余额制扣费
- 倍率叠加（分组倍率 × 长上下文 × service tier）

每个黄金样本 SHALL 断言四路一致性，并以注释形式记录预期金额的计算过程。

### Requirement: 边界场景一致性
系统 SHALL 验证以下边界场景的计费一致性：
- 分组从订阅制切换到余额制瞬间，在途请求的扣费路径
- 订阅过期瞬间，新请求是否正确回退到余额扣费
- 候选 billingModel 多重回退时，不同候选命中不同定价档的一致性
- RunModeSimple 下 usage_log 记录的 cost 与正常模式口径一致性（或明确文档化的差异）

## MODIFIED Requirements

### Requirement: CI 计费一致性门禁
CI pipeline SHALL 新增 `billing-consistency` job，运行 `go test -tags=unit -run "TestBillingPipelineE2E" ./internal/service/...`，作为 PR 合并的必要门槛。该 job 失败 SHALL 阻止合并。

## REMOVED Requirements
无

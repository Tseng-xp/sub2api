.PHONY: build build-backend build-frontend build-datamanagementd test test-backend test-frontend test-frontend-critical test-datamanagementd secret-scan release release-build release-push

FRONTEND_CRITICAL_VITEST := \
	src/views/auth/__tests__/LinuxDoCallbackView.spec.ts \
	src/views/auth/__tests__/WechatCallbackView.spec.ts \
	src/views/user/__tests__/PaymentView.spec.ts \
	src/views/user/__tests__/PaymentResultView.spec.ts \
	src/components/user/profile/__tests__/ProfileInfoCard.spec.ts \
	src/views/admin/__tests__/SettingsView.spec.ts

# 一键编译前后端
build: build-backend build-frontend

# 编译后端（复用 backend/Makefile）
build-backend:
	@$(MAKE) -C backend build

# 编译前端（需要已安装依赖）
build-frontend:
	@pnpm --dir frontend run build

# 编译 datamanagementd（宿主机数据管理进程）
build-datamanagementd:
	@cd datamanagement && go build -o datamanagementd ./cmd/datamanagementd

# 运行测试（后端 + 前端）
test: test-backend test-frontend

test-backend:
	@$(MAKE) -C backend test

test-frontend:
	@pnpm --dir frontend run lint:check
	@pnpm --dir frontend run typecheck
	@$(MAKE) test-frontend-critical

test-frontend-critical:
	@pnpm --dir frontend exec vitest run $(FRONTEND_CRITICAL_VITEST)

test-datamanagementd:
	@cd datamanagement && go test ./...

secret-scan:
	@python3 tools/secret_scan.py

# 一键构建发布：编译 + 提交 + 推送
# 用法: make release
# 自定义提交信息: make release MSG="fix: 修复登录问题"
release: release-build release-push

# 构建发布版本
release-build: build-backend build-frontend
	@echo "=== Build completed ==="

# 提交并推送到 GitHub（使用 SSH 或已配置的凭据）
release-push:
	@echo "=== Checking git status ==="
	@git status --short
	@echo ""
	@echo "=== Staging tracked changes (excluding ignored files) ==="
	@git add -u
	@echo ""
	@echo "=== Committing changes ==="
	@if [ -z "$(MSG)" ]; then \
		git commit -m "chore: release build $$(date +%Y-%m-%d)" || echo "No changes to commit"; \
	else \
		git commit -m "$(MSG)"; \
	fi
	@echo ""
	@echo "=== Pushing to GitHub ==="
	@git push origin main
	@echo ""
	@echo "=== Release pushed successfully ==="

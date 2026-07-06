# 部署指南（sub2api / tongyuan-ai.cn）

> 本文档描述**本 fork 的真实部署架构**与日常"改完代码怎么上线"的操作。
> 敏感信息（服务器 IP、root 密码）**只存在本地 `deploy/deploy.local.env`（已 gitignore），绝不入库**。

---

## 一、架构总览

```
用户 → Nginx(宝塔, :80/:443, TLS+域名+备案)
          └─反代→ app 容器 :8080  (ghcr.io/tseng-xp/sub2api:latest)
                        ├─ postgres 容器 (sub2api-postgres)  ← 用户数据在 docker 卷 postgres_data
                        └─ redis 容器    (sub2api-redis)
```

- **app**：Docker 容器，镜像由 **GitHub Actions 自动构建**（`.github/workflows/build-and-deploy.yml`，push 到 main 时触发）并推到 `ghcr.io/tseng-xp/sub2api:latest`。镜像里**已内嵌前端**（vite 产物 embed 进 Go 二进制）。
- **postgres / redis**：docker 容器，数据在命名卷里。**换 app 版本不碰这两个卷 → 用户数据安全**。
- **备案**：挂在 Nginx / 宝塔的域名配置里。**换 app 不碰 Nginx → 备案安全**。
- **前端 CDN（可选）**：Vercel 部署前端静态站（见第四节），API 反代回本服务器。

---

## 二、下次改完代码，怎么上线（日常流程）

分两步：**① 推代码让 CI 构建镜像 → ② 让服务器拉新镜像重启**。

### 第 1 步：构建 + 发布（本地一键）
```bash
make release                       # 一键：编译前后端 → 提交 → 推送到 GitHub
# 或带自定义提交信息：
make release MSG="fix: 修复xxx"
```
> 建议推送前先 `make test`（跑 lint + typecheck + 关键测试），避免 CI 变红。
推送后，GitHub Actions 会自动：
- **Build and Deploy** workflow → 构建镜像推到 `ghcr.io/tseng-xp/sub2api:latest`
- （若已连 Vercel）自动部署前端

> 去 GitHub → Actions 确认 **"Build and Deploy"** 变绿（镜像构建完成）再做第 2 步。

### 第 2 步：服务器拉新镜像并重启（一键）
```bash
cp deploy/deploy.local.env.example deploy/deploy.local.env   # 首次：填入服务器IP等
bash deploy/redeploy.sh
```
脚本会：SSH 到服务器 → `docker pull` 新镜像 → 重启 app 容器 → `curl /health` 验证 → **失败自动回滚**到上一个镜像。全程不碰数据库卷、不碰 Nginx。

---

## 三、安全约定（重要）

- 服务器 IP / root 密码**只写在** `deploy/deploy.local.env`（gitignore，永不入库）。
- 任何脚本都从**环境变量**读凭据，**禁止**在代码/文档里写明文。
- 若曾泄露过密码（如历史提交里出现过），**必须在服务器 `passwd root` 轮换**，历史提交清不掉。
- `.trae/` 等 IDE/agent 生成文档已 gitignore，避免把服务器信息带进库。

---

## 四、Vercel（前端 CDN，可选）

`vercel.json` 已配好：把前端构建成静态站，`/api`、`/v1`、`/setup`、`/docs` 反代到 `https://tongyuan-ai.cn`。

**一次性连接（在 Vercel 后台，需你的账号）**：
1. vercel.com → Add New Project → Import 你的 GitHub 仓库 `Tseng-xp/sub2api`
2. Framework 选 Other（`vercel.json` 会接管构建），Root 保持仓库根目录
3. Deploy。之后每次 push main，Vercel 自动重新部署前端。

> Vercel 只托管前端；后端 API 仍在你自己的服务器。二者互不影响。

---

## 五、绝对不能做的操作（会毁数据/备案）

- ❌ `docker compose down -v` / `docker volume rm` —— 会删数据库卷（用户数据）
- ❌ `docker system prune --volumes` —— 同上
- ❌ 改动 Nginx / 宝塔域名配置 —— 可能影响备案
- ❌ 把 IP / 密码 提交进 git

---

## 六、回滚

- app 容器换版本后有问题：`docker tag` 保留了上一个镜像，`redeploy.sh` 失败会自动回滚；手动回滚见脚本内 `rollback` 段。
- 数据库/redis 从不随 app 更新，无需回滚。

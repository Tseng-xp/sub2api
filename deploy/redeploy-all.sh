#!/usr/bin/env bash
# ============================================================================
# 一键部署到「所有」服务器（新版本同时推送多台）
#
# 用法：
#   cp deploy/servers.local.env.example deploy/servers.local.env   # 首次，填服务器
#   bash deploy/redeploy-all.sh
#
# 每台：拉新镜像 → 智能重建 app 容器(自动识别 compose / docker run) →
#       健康检查 → 失败自动回滚。全程不碰数据库卷 / Nginx。
# 服务器 IP、密钥路径只在本地 servers.local.env 里，不入库。
# ============================================================================
set -uo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
CONF="$DIR/servers.local.env"
[ -f "$CONF" ] || { echo "缺少 $CONF —— 先 cp servers.local.env.example servers.local.env 并填写"; exit 1; }
# shellcheck disable=SC1090
source "$CONF"
IMAGE="${IMAGE:-ghcr.io/tseng-xp/sub2api:latest}"

# 服务器端执行的重建逻辑（自动适配 compose / 独立容器 + 回滚）
read -r -d '' REMOTE_SCRIPT <<'REMOTE'
set -e
IMAGE="${IMAGE:?}"
COMPOSE="/root/sub2api/deploy/docker-compose.yml"
OLD="$(docker inspect -f '{{.Image}}' sub2api 2>/dev/null || echo '')"
[ -n "$OLD" ] && docker tag "$OLD" sub2api:rollback 2>/dev/null || true

echo "拉取镜像..."
docker pull "$IMAGE" >/dev/null

recreate() {  # $1=镜像
  if [ -f "$COMPOSE" ] && grep -q 'container_name: sub2api$\|^\s*sub2api:' "$COMPOSE" 2>/dev/null && docker compose -f "$COMPOSE" config --services 2>/dev/null | grep -qx sub2api; then
    cd /root/sub2api/deploy && IMAGE="$1" docker compose up -d sub2api >/dev/null 2>&1 && return 0
  fi
  # 独立容器方式（阿里云）
  docker rm -f sub2api >/dev/null 2>&1 || true
  docker run -d --name sub2api --network deploy_sub2api-network -p 8080:8080 \
    -v /root/sub2api_data:/app/data --restart unless-stopped "$1" >/dev/null
}

echo "重建容器..."
recreate "$IMAGE"

ok=''
for i in $(seq 1 25); do curl -sf http://localhost:8080/health >/dev/null 2>&1 && { ok=1; break; }; sleep 2; done
if [ -n "$ok" ]; then
  echo "OK $(docker inspect -f '{{.Config.Image}} {{.State.Health.Status}}' sub2api 2>/dev/null)"
else
  echo "不健康，回滚..."
  if docker image inspect sub2api:rollback >/dev/null 2>&1; then recreate sub2api:rollback; sleep 6; fi
  curl -sf http://localhost:8080/health >/dev/null 2>&1 && echo "已回滚，服务恢复" || echo "回滚后仍异常，需人工"
  exit 1
fi
REMOTE

fail=0
for entry in "${DEPLOY_SERVERS[@]}"; do
  host="${entry%%|*}"; key="${entry#*|}"
  keyopt=(); [ -n "$key" ] && keyopt=(-i "$key")
  echo "======================================================"
  echo "→ 部署到 $host"
  if ssh "${keyopt[@]}" -o ConnectTimeout=20 -o StrictHostKeyChecking=accept-new "$host" "IMAGE='$IMAGE' bash -s" <<< "$REMOTE_SCRIPT"; then
    echo "✅ $host 完成"
  else
    echo "❌ $host 失败"; fail=1
  fi
done
echo "======================================================"
[ "$fail" = 0 ] && echo "全部服务器部署完成 ✅" || { echo "有服务器失败，请检查上面输出 ⚠️"; exit 1; }

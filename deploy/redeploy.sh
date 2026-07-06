#!/usr/bin/env bash
# ============================================================================
# 一键重部署 app（拉新镜像 → 重建容器 → 健康检查 → 失败自动回滚）
#
# 用法：
#   cp deploy/deploy.local.env.example deploy/deploy.local.env   # 首次，填服务器IP
#   bash deploy/redeploy.sh
#
# 只更新 app 容器；postgres/redis/数据库卷/Nginx/备案 全程不碰。
# 凭据只从本地 deploy/deploy.local.env 读取，不入库。
# ============================================================================
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
[ -f "$DIR/deploy.local.env" ] && source "$DIR/deploy.local.env"
: "${SERVER_HOST:?请先在 deploy/deploy.local.env 里设置 SERVER_HOST}"
IMAGE="${IMAGE:-ghcr.io/tseng-xp/sub2api:latest}"

# 优先用 SSH 密钥；仅当设置了密码且装了 sshpass 时才用密码
SSH_CMD=(ssh -o ConnectTimeout=15)
if [ -n "${SERVER_PASSWORD:-}" ] && command -v sshpass >/dev/null 2>&1; then
  SSH_CMD=(sshpass -p "$SERVER_PASSWORD" ssh -o ConnectTimeout=15)
fi

echo "→ 部署 $IMAGE 到 $SERVER_HOST ..."
"${SSH_CMD[@]}" root@"$SERVER_HOST" "IMAGE='$IMAGE' bash -s" <<'REMOTE'
set -e
IMAGE="${IMAGE:?}"
NET="deploy_sub2api-network"
DATA="/root/sub2api_data"

run_app() {  # $1 = 镜像
  docker rm -f sub2api >/dev/null 2>&1 || true
  docker run -d --name sub2api \
    --network "$NET" \
    -p 8080:8080 \
    -v "$DATA":/app/data \
    --restart unless-stopped \
    "$1" >/dev/null
}

echo "== 备份当前镜像用于回滚 =="
OLD_IMG="$(docker inspect --format '{{.Config.Image}}' sub2api 2>/dev/null || true)"
[ -n "$OLD_IMG" ] && docker tag "$OLD_IMG" sub2api:rollback && echo "已备份: $OLD_IMG" || echo "(当前无 app 容器，首次部署)"

echo "== 拉取新镜像 =="
docker pull "$IMAGE"

echo "== 用新镜像重建 app 容器 =="
run_app "$IMAGE"

echo "== 健康检查（最多等 40s）=="
ok=""
for i in $(seq 1 20); do
  if curl -sf http://localhost:8080/health >/dev/null 2>&1; then ok=1; break; fi
  sleep 2
done

if [ -n "$ok" ]; then
  echo "✅ 部署成功"
  docker ps --filter name=sub2api --format '{{.Names}} {{.Image}} {{.Status}}'
else
  echo "❌ 健康检查失败"
  if docker image inspect sub2api:rollback >/dev/null 2>&1; then
    echo "== 回滚到上一个镜像 =="
    run_app sub2api:rollback
    sleep 6
    curl -sf http://localhost:8080/health >/dev/null 2>&1 && echo "已回滚，服务恢复" || echo "回滚后仍异常，请人工检查 docker logs sub2api"
  fi
  exit 1
fi
REMOTE

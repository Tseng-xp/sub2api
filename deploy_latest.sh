#!/bin/bash
set -e

HOST="${SERVER_HOST}"
PASSWORD="${SERVER_PASSWORD}"

# 环境变量校验
if [ -z "$HOST" ]; then
  echo "ERROR: SERVER_HOST is not set"
  exit 1
fi
if [ -z "$PASSWORD" ]; then
  echo "ERROR: SERVER_PASSWORD is not set"
  exit 1
fi

SSH_OPTS="-o ConnectTimeout=10"

echo "=== Step 1: Check current containers ==="
sshpass -p "$PASSWORD" ssh $SSH_OPTS root@$HOST "docker ps -a"

echo ""
echo "=== Step 2: Pull latest image ==="
sshpass -p "$PASSWORD" ssh $SSH_OPTS root@$HOST "docker pull ghcr.io/tseng-xp/sub2api:latest"

echo ""
echo "=== Step 3: Restart docker-compose ==="
sshpass -p "$PASSWORD" ssh $SSH_OPTS root@$HOST "cd /root/sub2api/deploy && docker-compose up -d"

echo ""
echo "=== Step 4: Wait for container to start ==="
sleep 10
sshpass -p "$PASSWORD" ssh $SSH_OPTS root@$HOST "docker ps | grep sub2api"

echo ""
echo "=== Step 5: Clean up old images ==="
sshpass -p "$PASSWORD" ssh $SSH_OPTS root@$HOST "docker images --filter=reference='ghcr.io/tseng-xp/sub2api:*' --format='{{.ID}} {{.Tag}}' | grep -v 'latest' | awk '{print \$1}' | xargs -r docker rmi -f 2>/dev/null || true"

echo ""
echo "=== Step 6: Clean up unused Docker resources ==="
sshpass -p "$PASSWORD" ssh $SSH_OPTS root@$HOST "docker system prune -f"

echo ""
echo "=== Step 7: Show remaining images ==="
sshpass -p "$PASSWORD" ssh $SSH_OPTS root@$HOST "docker images"

echo ""
echo "=== Step 8: Verify service ==="
sshpass -p "$PASSWORD" ssh $SSH_OPTS root@$HOST "curl -s http://localhost:8080/health || echo 'Health check failed'"

echo ""
echo "=== Deployment completed ==="
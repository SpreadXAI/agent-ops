#!/usr/bin/env bash
# Deploy agent-ops to imjson ECS (same pattern as tactile).
# Usage: DATABASE_PASSWORD=xxx bash scripts/deploy-imjson.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEPLOY_HOST="${DEPLOY_HOST:-118.31.57.25}"
DEPLOY_INSTANCE="${DEPLOY_INSTANCE:-i-bp18kchcnvcke6ltimn2}"
REMOTE_DIR="/opt/agent-ops"
WEB_DIR="/var/www/agent-ops"
API_PORT=9092
SERVICE_NAME="agent-ops-api"

echo "==> Build frontend"
cd "$ROOT/frontend"
npm ci
npm run build

echo "==> Package release"
RELEASE="/tmp/agent-ops-release.tar.gz"
tar -czf "$RELEASE" \
  -C "$ROOT" \
  backend \
  --exclude='backend/.venv' \
  --exclude='backend/__pycache__' \
  --exclude='**/__pycache__'

echo "==> Upload & deploy via git on server (cloud assistant)"
# Deployment executed on ECS — see scripts/remote-deploy.sh embedded in release

cat > /tmp/remote-deploy.sh << 'REMOTE'
#!/usr/bin/env bash
set -euo pipefail
REMOTE_DIR="/opt/agent-ops"
WEB_DIR="/var/www/agent-ops"
API_PORT=9092
SERVICE_NAME="agent-ops-api"

mkdir -p "$REMOTE_DIR" "$WEB_DIR"
cd "$REMOTE_DIR"

if [ ! -d .git ]; then
  git clone https://github.com/SpreadXAI/agent-ops.git .
fi
git fetch origin main && git reset --hard origin/main

python3 -m venv .venv
. .venv/bin/activate
pip install -q -r backend/requirements.txt

cat > backend/.env << EOF
ENVIRONMENT=test
DATABASE_PASSWORD=${DATABASE_PASSWORD}
JWT_SECRET=${JWT_SECRET:-agent-ops-test-jwt-secret-4918}
EOF

cd backend
python -c "from app.database import ensure_schema; from app.models import Base; from app.database import engine; ensure_schema(); Base.metadata.create_all(bind=engine)"
python scripts/migrate_schema.py
python scripts/seed_data.py 200
cd "$REMOTE_DIR"

deactivate 2>/dev/null || true

# systemd
cat > /etc/systemd/system/${SERVICE_NAME}.service << UNIT
[Unit]
Description=Agent Ops API (test)
After=network.target

[Service]
Type=simple
WorkingDirectory=${REMOTE_DIR}/backend
EnvironmentFile=${REMOTE_DIR}/backend/.env
ExecStart=${REMOTE_DIR}/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port ${API_PORT}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl restart ${SERVICE_NAME}

echo "API started on port ${API_PORT}"
REMOTE

echo "Release built at $RELEASE"
echo "Run remote deploy with cloud assistant — see scripts/ecs-deploy.py"

# Agent Ops

Social account task orchestration platform (**test environment**).

- Frontend: Vue 3 + Vite + Tailwind (static + Nginx)
- Backend: FastAPI + PostgreSQL (`agent_ops_test` schema on tactile RDS)
- Deploy: imjson ECS, path `/agent-ops/` (same pattern as tactile)

## Live (test)

- http://118.31.57.25/agent-ops/
- http://imjson.cn/agent-ops/ (if DNS routes to imjson)

## Local dev

```bash
# backend
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # set DATABASE_PASSWORD
export PYTHONPATH=.
uvicorn app.main:app --reload --port 9092

# frontend
cd frontend && npm ci && npm run dev
```

## Deploy

```bash
export DATABASE_PASSWORD=...
python3 scripts/ecs-deploy.py
```

## E2E

```bash
cd frontend && npm ci
cd .. && npx playwright install chromium
E2E_BASE_URL=http://118.31.57.25/agent-ops npx playwright test
```

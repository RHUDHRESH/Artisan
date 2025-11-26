# Artisan Hub – All-In-One Guide

AI-powered, privacy-first assistant that helps Indian artisans find suppliers, growth opportunities, and events. This single README replaces the previous markdown docs (`QUICK_START`, `HOW_TO_USE`, `TROUBLESHOOTING`, `DEVELOPER_GUIDE`, `DEPLOYMENT`, `ORCHESTRATION`, `MONITORING`, `CICD_SETUP`, `plan`, `todo`).

## Table of Contents
- [Run It Locally (5 Minutes)](#run-it-locally-5-minutes)
- [Environment Variables](#environment-variables)
- [How to Use the App](#how-to-use-the-app)
- [Troubleshooting Cheatsheet](#troubleshooting-cheatsheet)
- [Architecture and Layout](#architecture-and-layout)
- [Developer Workflow](#developer-workflow)
- [Deployment](#deployment)
- [Monitoring and Observability](#monitoring-and-observability)
- [Multi-Agent Orchestration](#multi-agent-orchestration)
- [CI/CD Overview](#cicd-overview)
- [Open Tasks](#open-tasks)
- [Support](#support)

## Run It Locally (5 Minutes)

### Prerequisites
```powershell
python --version    # 3.9+ recommended 3.11+
node --version      # 18+
ollama --version    # from https://ollama.com
```

### Step 1: Download AI Models (Terminal 1)
```powershell
ollama pull gemma3:4b
ollama pull gemma3:1b
ollama pull nomic-embed-text
ollama serve   # keep running
```

### Step 2: Backend (Terminal 2)
```powershell
cd "C:\Users\hp\OneDrive\Desktop\Artisan"
.venv\Scripts\activate
pip install -r requirements.txt      # first time
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3: Frontend (Terminal 3)
```powershell
cd "C:\Users\hp\OneDrive\Desktop\Artisan\frontend"
npm install    # first time
npm run dev
```

### Step 4: Open the app
```
http://localhost:3000
```

Expected running stack:
```
Terminal 1: ollama serve        (11434)
Terminal 2: uvicorn backend     (8000)
Terminal 3: npm run dev         (3000)
Browser:   http://localhost:3000
```

To stop, press `Ctrl+C` in each terminal.

## Environment Variables
Copy `.env.example` to `.env` and set what you need:
```env
# LLM provider (Groq default, Ollama fallback)
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key
OLLAMA_BASE_URL=http://localhost:11434

# Web search (required for suppliers, growth, events)
TAVILY_API_KEY=your-tavily-key
SERPAPI_KEY=optional-fallback

# Optional persistence
SUPABASE_URL=https://your.supabase.co
SUPABASE_KEY=service-role-key

# Frontend URLs
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# CORS for production
CORS_ORIGINS=https://your-frontend.vercel.app
```

If `TAVILY_API_KEY`/`SERPAPI_KEY` are missing, the Supply Hunter, Growth Marketer, and Event Scout agents will stop early and surface a blocking message telling you to add a key.

## How to Use the App

1. Open `http://localhost:3000`.
2. Fill the 8-question questionnaire (craft type, experience, region, products, tools, materials, challenges, traditions).
3. Click **Analyze My Craft** and wait ~30–60 seconds.
4. Results include:
   - **Profile Analyst**: craft profile, positioning.
   - **Supply Hunter**: verified suppliers (with confidence %).
   - **Growth Marketer**: market trends, pricing, scaling ideas.
   - **Event Scout**: exhibitions and networking events with suitability %.
5. Use specific answers for better results and include your city/state.

Tips:
- Provide detailed materials and tools (e.g., “stoneware clay, electric kiln, cobalt glaze”).
- Contact top 2–3 suppliers first and request samples.
- Re-run monthly to refresh market/event data.

## Troubleshooting Cheatsheet

- **Python/Node missing**: reinstall and ensure they’re on PATH (`python --version`, `node --version`).
- **Port in use (8000/3000)**: `netstat -ano | findstr :8000` then `taskkill /PID <PID> /F`, or run on another port (`uvicorn ... --port 8001`, `npm run dev -- -p 3001`).
- **Ollama not running/model missing**: keep `ollama serve` open; check `ollama list`, re-run pulls.
- **Missing web search key**: add `TAVILY_API_KEY` or `SERPAPI_KEY` to `.env`, restart backend, refresh UI.
- **npm install errors**: `npm cache clean --force`, delete `frontend/node_modules` + `package-lock.json`, reinstall.
- **pip install errors**: upgrade pip (`python -m pip install --upgrade pip`), ensure build tools installed, retry `pip install -r requirements.txt`.
- **Frontend stuck loading**: check backend terminal for errors, refresh page, ensure web search key present for supplier/event data.
- **Reset everything**: delete `.venv`, `frontend/node_modules`, `data/cache`, re-create venv, reinstall, rerun commands above.

## Architecture and Layout

```
Artisan/
├── backend/            # FastAPI, agents, scraping, vector store, services
├── frontend/           # Next.js app and components
├── data/               # Local data (ChromaDB, cache, logs)
├── docker-compose*.yml # Docker definitions
└── start.bat           # Windows helper
```

Core flow:
Frontend (Next.js) → Backend API/WebSocket (FastAPI) → Agents (Profile, Supply, Growth, Events) → LLM (Groq/Ollama) → Vector store (ChromaDB) → Optional Supabase sync.

Stack highlights: FastAPI, Next.js 14, Tailwind, Framer Motion, Playwright/BeautifulSoup, Groq + Ollama, ChromaDB, Supabase optional, Tavily/SerpAPI for live search.

## Developer Workflow

Setup for contributing:
```powershell
cd "C:\Users\hp\OneDrive\Desktop\Artisan"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
cd frontend && npm install && cd ..
```

Code quality:
```powershell
black backend/
flake8 backend/ --max-line-length=100
mypy backend/
cd frontend && npm run lint && cd ..
```

Tests:
```powershell
pytest backend/tests/ -v            # or add --cov=backend
cd frontend && npm test && cd ..
```

Useful patterns:
- Add APIs under `backend/api/routes/`, include validation via Pydantic models.
- Agents live in `backend/agents/`; reuse `backend/core/ollama_client.py` and `vector_store.py`.
- Frontend fetches use `NEXT_PUBLIC_API_URL`; WebSocket at `NEXT_PUBLIC_WS_URL`.

## Deployment

> ⚠️ Cloud Run is the canonical choice for the backend today. The Render manifest (`render.yaml`) remains in the repo for historical context only; updates and CI/CD pipelines target Google Cloud Run instead.

### Docker (local/prod)
```bash
./docker-start.sh prod    # or: docker-compose up -d --build
./docker-start.sh dev     # hot reload
```
Ports: backend 8000, frontend 3000, Ollama 11434.

### Vercel (frontend)
- Framework: Next.js; build `npm run build`; output `.next`.
- Env vars: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_WS_URL`.
- Connect repo in Vercel dashboard or run `vercel --prod` inside `frontend/`.

### Google Cloud Run (backend)
Cloud Run is the recommended backend host, and the included `cloudbuild.yaml` automates building, pushing, and deploying the service while loading secrets from Secret Manager entries such as `groq-api-key` and `tavily-api-key`.

Cloud Run exposes a `PORT` environment variable (default 8080). The backend container now respects `${PORT}` with a fallback to `8000`, so the same image works locally and on Cloud Run.

```bash
gcloud builds submit --tag gcr.io/<PROJECT_ID>/artisan-backend
gcloud run deploy artisan-backend \
  --image gcr.io/<PROJECT_ID>/artisan-backend \
  --allow-unauthenticated \
  --region us-central1 \
  --set-env-vars "LLM_PROVIDER=groq,GROQ_API_KEY=your-key,TAVILY_API_KEY=your-key" \
  --memory 4Gi --cpu 2 --timeout 300
```
Use Secret Manager for keys where possible. Update Vercel envs to point to the Cloud Run URL.

Supabase schema (optional persistence):
```sql
create table if not exists user_profiles (
  user_id text primary key,
  context jsonb default '{}'::jsonb,
  updated_at timestamptz default now()
);

create table if not exists search_results (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references user_profiles(user_id) on delete cascade,
  search_type text not null,
  results jsonb not null,
  timestamp timestamptz default now()
);

create table if not exists suppliers (
  id uuid primary key default gen_random_uuid(),
  name text,
  location jsonb,
  contact jsonb,
  metadata jsonb,
  updated_at timestamptz default now()
);
```

## Monitoring and Observability

- Prometheus metrics: `http://localhost:8000/monitoring/metrics`
- Health: `/monitoring/health`, `/monitoring/health/live`, `/monitoring/health/ready`
- System info: `/monitoring/info`
- Grafana (via docker-compose): http://localhost:3001 (admin/admin)
- Key metrics: request rate/latency, agent executions, LLM requests/tokens, cache hits, memory usage.
- Alerts (Prometheus Alertmanager examples): high error rate, slow responses, high LLM latency, Redis/LLM/provider issues.

## Multi-Agent Orchestration

Advanced stack (optional) includes 100+ specialized agents, LangGraph workflows, Redis-backed memory, and tool database.

Quick start:
```bash
# start full stack incl. Redis (via docker-compose)
./docker-start.sh prod
```
Example workflow call:
```python
import requests
requests.post("http://localhost:8000/orchestration/workflow/execute", json={
  "task": "Find top pottery clay suppliers in India",
  "agents": ["web_researcher", "data_analyst", "quality_checker"],
  "use_supervisor": True,
  "max_iterations": 10
})
```
Env notes: `REDIS_URL=redis://localhost:6379`, `LLM_PROVIDER`/keys as above, optional tool DB at `sqlite:///./data/tools.db`.

## CI/CD Overview

GitHub Actions workflows:
- **ci.yml**: backend + frontend tests, lint/type checks, coverage.
- **deploy.yml**: deploy frontend (Vercel) and backend (Cloud Run) on main.
- **docker.yml**: multi-arch Docker builds + publish.
- **security.yml**: CodeQL, pip-audit/Bandit, npm audit, Trivy, secret scanning.
- **Dependabot**: weekly dependency PRs.

Required secrets (repo → Settings → Secrets → Actions): `GROQ_API_KEY`, `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, `GCP_PROJECT_ID`, `GCP_SA_KEY`, optional `DOCKERHUB_USERNAME`/`DOCKERHUB_TOKEN`, `CODECOV_TOKEN`.

Pre-commit (optional):
```bash
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```

## Open Tasks
- Add API error-handling tests for missing web search keys and agent propagation.
- Document blocking behavior with sample error JSON (UI already shows guidance).

## Support
- App: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- Need help? Check the troubleshooting cheatsheet above, then inspect backend/frontend terminal logs. If search is blocked, add `TAVILY_API_KEY` or `SERPAPI_KEY` and restart the backend.

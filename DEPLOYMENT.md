# Artisan Hub - Deployment Guide

Complete guide for deploying Artisan Hub to production environments.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Docker Deployment](#docker-deployment)
4. [Vercel Deployment (Frontend)](#vercel-deployment-frontend)
5. [Google Cloud Deployment (Backend)](#google-cloud-deployment-backend)
6. [Post-Deployment](#post-deployment)

---

> ⚠️ Backend deployments now use Google Cloud Run and the accompanying `cloudbuild.yaml`. The legacy `render.yaml` manifest is retained only for historical reference; CI/CD pipelines and docs focus on Cloud Run and Secret Manager.

## Prerequisites

### Required Accounts & API Keys
- **Groq** – https://console.groq.com (create a key with `chat.completions` scope)
- **Supabase** – https://supabase.com (project + service role key)
- **Vercel** – https://vercel.com (connect your Git repo)
- **Google Cloud** – https://cloud.google.com (enable Cloud Run + Cloud Build)
- **Tavily** (optional) – https://tavily.com for richer supplier search

> ✅ Tip: sign into all four dashboards once before running the CLIs so auth tokens are cached locally.

### Login Checklist

| Service | CLI Command | Purpose |
|---------|-------------|---------|
| Groq | _n/A_ | Copy the key into `.env` + Secret Manager |
| Supabase | `npx supabase login` (optional) | Seed tables or run SQL migrations |
| Vercel | `vercel login` | Authorize repo + import project |
| Google Cloud | `gcloud auth login` | Also run `gcloud auth configure-docker` |

### Required Tools
- Docker & Docker Compose (for local/Docker deployment)
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)
- Google Cloud SDK (for GCP deployment)
- Vercel CLI (optional, for CLI deployment)

---

## Environment Configuration

### 1. Copy Environment Template
```bash
cp .env.example .env
```

### 2. Configure Required Variables

```env
# LLM PROVIDER (Primary - GROQ recommended)
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key-here

# OLLAMA (Fallback - optional for local development)
OLLAMA_BASE_URL=http://localhost:11434

# SEARCH API (Optional but recommended)
TAVILY_API_KEY=your-tavily-api-key-here

# DATABASE (Optional - Supabase for cloud storage)
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key

# CORS CONFIGURATION (Important for production)
CORS_ORIGINS=https://your-frontend-domain.vercel.app

# FRONTEND CONFIGURATION
NEXT_PUBLIC_API_URL=https://your-backend-url.com
NEXT_PUBLIC_WS_URL=wss://your-backend-url.com
```

---

## Docker Deployment

### Quick Start

**Option 1: Production Mode**
```bash
# Make startup script executable
chmod +x docker-start.sh

# Start all services
./docker-start.sh prod
```

**Option 2: Development Mode (with hot reload)**
```bash
./docker-start.sh dev
```

### Manual Docker Commands

**Production:**
```bash
docker-compose up -d --build
```

**Development:**
```bash
docker-compose -f docker-compose.dev.yml up --build
```

### Access Services
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Ollama** (if running): http://localhost:11434

### Docker Management
```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart a service
docker-compose restart backend

# Rebuild after code changes
docker-compose up -d --build backend
```

---

## Vercel Deployment (Frontend)

### Method 1: Vercel Dashboard (Recommended)

1. **Connect Repository**
   - Go to https://vercel.com
   - Click "New Project"
   - Import your Git repository
   - Select the `frontend` directory as the root

2. **Configure Build Settings**
   - Framework Preset: Next.js
   - Build Command: `npm run build`
   - Output Directory: `.next`
   - Install Command: `npm install`

3. **Set Environment Variables**
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.com
   NEXT_PUBLIC_WS_URL=wss://your-backend-url.com
   ```
   Frontend does **not** need Supabase credentials—the backend proxies every data call—so only the backend environments need `SUPABASE_URL`/`SUPABASE_KEY`.

4. **Deploy**
   - Click "Deploy"
   - Wait for build to complete
   - Your app will be live at `https://your-project.vercel.app`

### Method 2: Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Navigate to frontend directory
cd frontend

# Login to Vercel
vercel login

# Deploy
vercel --prod
```

### Configure Custom Domain (Optional)
1. Go to Project Settings → Domains
2. Add your custom domain
3. Follow DNS configuration instructions

---

## Google Cloud Deployment (Backend)

### Prerequisites
```bash
# Install Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

# Login
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID
```

### Option 1: Cloud Run (Recommended)

Cloud Run exposes a `PORT` environment variable (default 8080), and the backend container now respects `${PORT}` with a fallback to `8000` so it works both locally and in Cloud Run. The provided `cloudbuild.yaml` automates building, pushing, and deploying while loading secrets from Secret Manager entries such as `groq-api-key`, `tavily-api-key`, and `supabase-key`. You can trigger that config manually via `gcloud builds submit --config cloudbuild.yaml` or wire it up to a Cloud Build trigger tied to your repo.

**1. Build and Push Image**
```bash
# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/artisan-backend

# Deploy to Cloud Run
gcloud run deploy artisan-backend \
  --image gcr.io/YOUR_PROJECT_ID/artisan-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "LLM_PROVIDER=groq,GROQ_API_KEY=your-key" \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 1
```

**2. Configure Secrets (Recommended)**
```bash
# Store secrets in Secret Manager
echo "your-groq-api-key" | gcloud secrets create groq-api-key --data-file=-
echo "your-tavily-api-key" | gcloud secrets create tavily-api-key --data-file=-
echo "https://your-project.supabase.co" | gcloud secrets create supabase-url --data-file=-
echo "your-supabase-service-role-key" | gcloud secrets create supabase-key --data-file=-

# Deploy with secrets
gcloud run deploy artisan-backend \
  --image gcr.io/YOUR_PROJECT_ID/artisan-backend \
  --update-secrets=GROQ_API_KEY=groq-api-key:latest \
  --update-secrets=TAVILY_API_KEY=tavily-api-key:latest \
  --update-secrets=SUPABASE_URL=supabase-url:latest \
  --update-secrets=SUPABASE_KEY=supabase-key:latest \
  ... (other flags)
```

**3. Get Service URL**
```bash
gcloud run services describe artisan-backend --region us-central1 --format 'value(status.url)'
```

### Option 2: App Engine

**1. Configure `app.yaml`**
```bash
cd backend
# Edit app.yaml with your configuration
```

**2. Deploy**
```bash
gcloud app deploy
```

### Option 3: Automated Cloud Build

**1. Setup Cloud Build Trigger**
```bash
# Enable Cloud Build API
gcloud services enable cloudbuild.googleapis.com

# Create build trigger (or use console)
gcloud builds triggers create github \
  --repo-name=your-repo \
  --repo-owner=your-username \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml
```

**2. Push to trigger build**
```bash
git push origin main
```

---

## Post-Deployment

### Supabase Schema Setup

Create the tables below (can be done via Supabase SQL editor):

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

Optional heartbeat table for the Flight Check probe:

```sql
create table if not exists _health (id int primary key default 1);
insert into _health(id) values (1) on conflict do nothing;
```

### 1. Update Frontend Environment
After deploying backend, update frontend environment variables in Vercel:
```
NEXT_PUBLIC_API_URL=https://your-backend-url.run.app
NEXT_PUBLIC_WS_URL=wss://your-backend-url.run.app
```

### 2. Update Backend CORS
Update backend environment variable:
```
CORS_ORIGINS=https://your-frontend.vercel.app
```

### 3. Test Deployment
```bash
# Test backend health
curl https://your-backend-url/health/flight-check

# Test frontend
open https://your-frontend.vercel.app
```

### 4. Monitor Logs

**Vercel (Frontend):**
- View in Vercel Dashboard → Project → Logs
- Or use CLI: `vercel logs`

**Google Cloud (Backend):**
```bash
# Cloud Run
gcloud run services logs tail artisan-backend --region us-central1

# App Engine
gcloud app logs tail
```

---

## Troubleshooting

### Frontend Issues

**Build fails:**
```bash
# Clear Next.js cache
rm -rf .next
npm run build
```

**API connection fails:**
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check CORS configuration in backend
- Verify backend is deployed and healthy

### Backend Issues

**Import errors:**
```bash
# Ensure all dependencies are in requirements.txt
pip freeze > requirements.txt
```

**Memory errors in Cloud Run:**
- Increase memory allocation: `--memory 4Gi` or `8Gi`
- Increase CPU: `--cpu 2` or `4`

**Timeout errors:**
- Increase timeout: `--timeout 300` (max 900s)
- Enable Cloud Run always-on: `--min-instances 1`

### Docker Issues

**Build fails:**
```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

**Port conflicts:**
```bash
# Change ports in docker-compose.yml or .env
BACKEND_PORT=8001
FRONTEND_PORT=3001
```

---

## Security Best Practices

1. **Never commit API keys** - Use environment variables or Secret Manager
2. **Configure CORS properly** - Don't use `*` in production
3. **Enable HTTPS** - Vercel and Cloud Run provide this automatically
4. **Use secrets management** - Google Secret Manager for GCP, Vercel Environment Variables
5. **Regular updates** - Keep dependencies updated
6. **Monitor logs** - Set up alerts for errors

---

## Cost Optimization

### Vercel
- Free tier: Sufficient for small projects
- Pro tier: $20/month for production apps

### Google Cloud Run
- Free tier: 2 million requests/month
- Optimization tips:
  - Use `--min-instances 0` for dev environments
  - Set appropriate `--max-instances` based on traffic
  - Use Cloud Scheduler to warm up instances

### Groq API
- Free tier available
- Very cost-effective compared to OpenAI
- Monitor usage in Groq dashboard

---

## Support & Resources

- **Documentation**: See other .md files in repository
- **Issues**: Open an issue on GitHub
- **Groq Docs**: https://console.groq.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **Google Cloud Run Docs**: https://cloud.google.com/run/docs

---

## Quick Reference Commands

```bash
# Docker
./docker-start.sh prod          # Start production
./docker-start.sh dev            # Start development
./docker-start.sh stop           # Stop all services
./docker-start.sh logs           # View logs

# Vercel
vercel                           # Deploy preview
vercel --prod                    # Deploy production
vercel logs                      # View logs

# Google Cloud
gcloud builds submit --tag gcr.io/$PROJECT_ID/artisan-backend
gcloud run deploy artisan-backend --image gcr.io/$PROJECT_ID/artisan-backend
gcloud run services logs tail artisan-backend

# Git
git add .
git commit -m "Deploy to production"
git push origin main
```

---

**Happy Deploying! 🚀**

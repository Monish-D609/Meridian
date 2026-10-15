# Meridian — Deployment Guide

## Architecture Overview

```
Railway (Backend FastAPI)  ←→  Neon Postgres (Free Postgres DB)
         ↓
External LLM Providers (Groq, Gemini AI Studio, OpenRouter, Cloudflare)
         ↓
React Frontend (served separately — Railway static or Vercel)
```

---

## Step 1: Set Up Neon Postgres (Free Database)

1. Go to https://console.neon.tech and create a free account
2. Create a new project → new database named `meridian`
3. Copy the **Connection String** from the dashboard:
   - Async (for app): `postgresql+asyncpg://user:pass@ep-xxx.region.aws.neon.tech/meridian?sslmode=require`
   - Sync (for Alembic): `postgresql+psycopg2://user:pass@ep-xxx.region.aws.neon.tech/meridian?sslmode=require`

---

## Step 2: Get Free LLM API Keys

| Provider | URL | Notes |
|---|---|---|
| **xAI** (Grok — Elon Musk) | https://console.x.ai | API key for grok-2-latest & grok-2-mini |
| **Groq** (fast LPU inference) | https://console.groq.com | Sign up → API Keys |
| **Google AI Studio** (Gemini, LLM-judge) | https://aistudio.google.com/app/apikey | Free, no credit card |
| **OpenRouter** (many free models) | https://openrouter.ai/keys | Create key, no payment needed for :free models |
| **Cloudflare Workers AI** | https://dash.cloudflare.com | Get Account ID + API Token |

---

## Step 3: Deploy to Railway

### Option A: From GitHub (Recommended)
1. Push the Meridian repo to GitHub
2. Go to https://railway.app → New Project → Deploy from GitHub
3. Select your repo → Set root directory: `backend/`
4. Railway auto-detects the Dockerfile

### Option B: Railway CLI
```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

### Required Environment Variables
Set these in Railway → Project → Variables:

```
# Database
DATABASE_URL=postgresql+asyncpg://...neon.tech/meridian?sslmode=require
DATABASE_URL_SYNC=postgresql+psycopg2://...neon.tech/meridian?sslmode=require

# LLM Providers
XAI_API_KEY=xai-...
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AIza...
OPENROUTER_API_KEY=sk-or-...
CLOUDFLARE_ACCOUNT_ID=...
CLOUDFLARE_API_TOKEN=...

# Judge configuration (reproducibility — stored in every run)
JUDGE_PROVIDER=gemini
JUDGE_MODEL=gemini-1.5-flash-latest
JUDGE_MODEL_VERSION=gemini-1.5-flash-001

# Security
ENCRYPTION_KEY=<generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
SECRET_KEY=<random 32-char string>

# CORS — set to your frontend URL
CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000

# App
APP_ENV=production
LOG_LEVEL=INFO
```

---

## Step 4: Run Database Migrations

After deployment, run migrations via Railway CLI or the Railway console:

```bash
# Local (point to Neon DATABASE_URL_SYNC):
cd backend
DATABASE_URL_SYNC="postgresql+psycopg2://...neon.tech/meridian?sslmode=require" alembic upgrade head

# Seed the database:
DATABASE_URL="postgresql+asyncpg://...neon.tech/meridian?sslmode=require" python -m app.db.seed
```

---

## Step 5: Verify Deployment

```bash
# Health check
curl https://your-railway-app.up.railway.app/health

# Expected response:
# {"status":"ok","service":"meridian-backend","version":"1.0.0"}

# List seeded datasets
curl https://your-railway-app.up.railway.app/api/v1/datasets

# Check configured providers
curl https://your-railway-app.up.railway.app/api/v1/providers/configured/list
```

---

## Railway Free Tier Notes

- **Sleep mode**: Railway's serverless/sleep feature is enabled in `railway.json` 
  (`"sleepApplication": true`). Services sleep after ~5–10 min inactivity, 
  wake on first request (~5–10s cold start).
- **$1/month credit**: Sufficient for academic-scale usage with sleep enabled.
- **Trial**: First 30 days get $5 in credits — more than enough for initial testing.

---

## Running Locally (Development)

```bash
cd backend

# 1. Create .env from template
cp .env.example .env
# Fill in your API keys in .env

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start a local Postgres (optional — can use Neon for local dev too)
# Or set DATABASE_URL in .env to point to Neon

# 4. Run migrations
alembic upgrade head

# 5. Seed database
python -m app.db.seed

# 6. Start server
uvicorn app.main:app --reload --port 8000

# API docs: http://localhost:8000/docs
```

### 6b. Start React + TypeScript Frontend

```bash
cd frontend
pnpm install     # or npm install
pnpm run dev     # Starts Vite dev server at http://localhost:5173
```

- Live Application: `http://localhost:5173/`
- API Proxy: Automatically forwards `/api` and `/health` requests to `http://127.0.0.1:8000`.
- Production Build: `pnpm run build`


---

## Running Tests

```bash
cd backend
pytest tests/ -v --tb=short
```

---

## Redeployment

Push to main branch → Railway auto-redeploys (if GitHub integration is set up).

Or manually:
```bash
railway up
```

---

## Troubleshooting

| Issue | Fix |
|---|---|
| DB connection error | Check DATABASE_URL in Railway variables; ensure Neon project is active |
| Rate limit errors | Normal for free tiers; the system auto-retries and marks cells as failed without aborting |
| Cold start slow | Railway sleep mode — first request after idle takes 5–10s |
| Judge not scoring | Ensure GEMINI_API_KEY or GROQ_API_KEY is set |

---

*Prepared by Meridian team (Monish D 24BDS1033, Soaham S 24BDS1021). September 2026.*

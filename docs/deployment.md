---
# Deploying UnitForge to Production

## Free deployment stack

| Service | Provider | Cost | What it runs |
|---|---|---|---|
| PostgreSQL | Supabase | Free (500MB) | Jobs and results database |
| Redis | Upstash | Free (10k cmds/day) | Task queue between orchestrator and agent |
| Orchestrator API | Render.com | Free web service | Spring Boot REST API |
| Test Agent | Render.com | Free web service | Python Redis worker + health endpoint |
| Analysis Engine | Render.com | Free web service | FastAPI code analysis service |
| Dashboard | Vercel | Free | React frontend |

**Total cost: $0**

---

## Prerequisites

1. GitHub account with UnitForge repo forked or cloned
2. Supabase account — https://supabase.com (no credit card)
3. Upstash account — https://upstash.com (no credit card)
4. Render.com account — https://render.com (no credit card)
5. Vercel account — https://vercel.com (no credit card)

---

## Step 1 — Supabase (PostgreSQL)

1. Go to https://supabase.com → New project
2. Name: `unitforge` · Region: Singapore · Set a password
3. Wait ~2 minutes for setup
4. Go to **Settings → Database → Connection parameters**
5. Copy: Host, Port (5432), Database (postgres), User (postgres), Password

**Use Direct Connection only — NOT the pooler (port 6543)**

---

## Step 2 — Upstash (Redis)

1. Go to https://upstash.com → Create database
2. Name: `unitforge-redis` · Type: Regional · Region: AP-Southeast-1
3. Copy: Endpoint, Port (6379), Password
4. Enable TLS — use `REDIS_SSL=true`

---

## Step 3 — Render (Orchestrator API)

1. Go to https://render.com → New → Web Service
2. Connect GitHub repo → select UnitForge
3. Configure:
   - **Name:** `unitforge-api`
   - **Dockerfile Path:** `./orchestrator/Dockerfile`
   - **Docker Build Context:** `./orchestrator`
   - **Plan:** Free
   - **Health Check Path:** `/health`
4. Add environment variables:

| Key | Value |
|---|---|
| DB_HOST | your Supabase host |
| DB_PORT | 5432 |
| DB_NAME | postgres |
| DB_USERNAME | postgres |
| DB_PASSWORD | your Supabase password |
| REDIS_HOST | your Upstash endpoint |
| REDIS_PORT | 6379 |
| REDIS_PASSWORD | your Upstash password |
| REDIS_SSL | true |
| JWT_SECRET | generate 48 random chars |
| ENCRYPTION_KEY | generate 32 random chars |
| UNITFORGE_DEV_MODE | false |
| CORS_ALLOWED_ORIGINS | * (update after Vercel deploy) |
| SERVER_PORT | 8080 |

5. Click **Create Web Service**
6. Copy your URL: `https://unitforge-api.onrender.com`

---

## Step 4 — Render (Test Agent)

1. New → Web Service (NOT Background Worker — that costs money)
2. Configure:
   - **Name:** `unitforge-agent`
   - **Dockerfile Path:** `./test-agents/Dockerfile`
   - **Docker Build Context:** `./test-agents`
   - **Plan:** Free
   - **Health Check Path:** `/health`
3. Add environment variables:

| Key | Value |
|---|---|
| REDIS_HOST | your Upstash endpoint |
| REDIS_PORT | 6379 |
| REDIS_PASSWORD | your Upstash password |
| REDIS_SSL | true |
| ORCHESTRATOR_URL | https://unitforge-api.onrender.com |
| LLM_PROVIDER | gemini |
| GEMINI_MODEL | gemini-1.5-flash |
| MAX_RETRY_ATTEMPTS | 2 |
| GOOGLE_API_KEY | leave empty (users bring their own) |
| PORT | 8002 |

4. Click **Create Web Service**

**Keep agent awake:** Set up a free UptimeRobot monitor (https://uptimerobot.com) pinging `https://unitforge-agent.onrender.com/health` every 5 minutes to prevent Render free tier sleep.

---

## Step 5 — Render (Analysis Engine)

1. New → Web Service
2. Configure:
   - **Name:** `unitforge-analysis`
   - **Dockerfile Path:** `./analysis-engine/Dockerfile`
   - **Docker Build Context:** `./analysis-engine`
   - **Plan:** Free
   - **Health Check Path:** `/health`
3. Add environment variables:

| Key | Value |
|---|---|
| PORT | 8001 |

4. Click **Create Web Service**

---

## Step 6 — Vercel (Dashboard)

1. Go to https://vercel.com → Add New Project
2. Import UnitForge repo
3. Configure:
   - **Root Directory:** `dashboard`
   - **Framework:** Vite (auto-detected)
4. Add environment variables:

| Key | Value |
|---|---|
| VITE_API_URL | https://unitforge-api.onrender.com/api |
| VITE_WS_URL | https://unitforge-api.onrender.com |
| VITE_ANALYSIS_ENGINE_URL | https://unitforge-analysis.onrender.com |

5. Click **Deploy**
6. Copy your URL: `https://unit-forge.vercel.app`

---

## Step 7 — Update CORS

Go back to **Render → unitforge-api → Environment**
Update `CORS_ALLOWED_ORIGINS` from `*` to your Vercel URL:
[https://your-app.vercel.app](https://your-app.vercel.app)

Render redeploys automatically.

---

## Step 8 — Verify everything

```bash
# Orchestrator health
curl https://unitforge-api.onrender.com/health

# Agent health
curl https://unitforge-agent.onrender.com/health

# Analysis engine health
curl https://unitforge-analysis.onrender.com/health
```

All three should return `{"status":"UP",...}`.
Then open your Vercel dashboard URL, register, add your Gemini key, and submit a test job.

---

## Keeping free tier services awake

Render free web services sleep after 15 minutes of no traffic.
Use UptimeRobot (free) to ping all three services every 5 minutes:
- `https://unitforge-api.onrender.com/health`
- `https://unitforge-agent.onrender.com/health`
- `https://unitforge-analysis.onrender.com/health`

This keeps all services awake 24/7 at zero cost.

---

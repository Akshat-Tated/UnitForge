# Deploying UnitForge to Production

## Free deployment stack

| Service | Provider | Cost |
|---|---|---|
| PostgreSQL | Supabase | Free (500MB) |
| Redis | Upstash | Free (10k commands/day) |
| Orchestrator API | Render.com | Free (sleeps after 15min) |
| Dashboard | Vercel | Free (always on) |
| Test Agent | Self-hosted | Runs locally or on any server |

## Prerequisites

1. GitHub account
2. Supabase account (supabase.com) — no credit card
3. Upstash account (upstash.com) — no credit card
4. Render.com account (render.com) — no credit card
5. Vercel account (vercel.com) — no credit card

## Step 1 — Supabase (PostgreSQL)

1. Go to https://supabase.com → New project
2. Save your database password
3. Go to Settings → Database → copy connection details
4. Note: use port 5432, NOT the pooler port

## Step 2 — Upstash (Redis)

1. Go to https://upstash.com → Create database
2. Select Regional, Singapore region
3. Copy: Endpoint, Port, Password
4. Enable TLS/SSL — set REDIS_SSL=true

## Step 3 — Render.com (Orchestrator)

1. Go to https://render.com → New Web Service
2. Connect your GitHub repo (Akshat-Tated/UnitForge)
3. Select: Docker runtime
4. Dockerfile path: ./orchestrator/Dockerfile
5. Set all environment variables from .env.example
6. Click Deploy
7. Copy your service URL: https://unitforge-api.onrender.com

## Step 4 — Vercel (Dashboard)

1. Go to https://vercel.com → Import project
2. Select UnitForge repo
3. Root directory: dashboard
4. Framework: Vite
5. Add environment variables:
   VITE_API_URL=https://your-render-url.onrender.com/api
   VITE_WS_URL=https://your-render-url.onrender.com
6. Click Deploy
7. Your dashboard is live at https://unitforge-xxx.vercel.app

## Step 5 — Test Agent (local, connects to cloud)

Update test-agents/.env:
  REDIS_HOST=xxx.upstash.io
  REDIS_PORT=6379
  REDIS_PASSWORD=your-upstash-password
  REDIS_SSL=true
  ORCHESTRATOR_URL=https://your-render-url.onrender.com
  LLM_PROVIDER=gemini
  GOOGLE_API_KEY=your-gemini-key

Then run:
  cd test-agents
  python agent.py

The agent runs locally but connects to all cloud services.

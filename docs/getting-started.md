---
# Getting Started with UnitForge

## Option A — Use the hosted version (recommended)

No installation needed.

1. Go to **https://unit-forge.vercel.app**
2. Click **Register** — create a free account
3. Go to **Settings** → paste your Gemini API key
   - Get a free key at https://aistudio.google.com
   - Click Get API Key → Create API Key → copy it
4. Click **+ Generate Tests** on the dashboard
5. Paste any public Python GitHub URL
6. Watch tests generate in real time
7. Click **Download Tests** when done

That is it. No downloads, no terminal, works on mobile.

---

## Option B — Self-hosting

### Prerequisites

| Tool | Version | Download |
|---|---|---|
| Java | 21 (LTS) | https://adoptium.net |
| Python | 3.12 | https://python.org |
| Node.js | 20 (LTS) | https://nodejs.org |
| Maven | 3.9+ | https://maven.apache.org |
| Docker Desktop | 24+ | https://docker.com/products/docker-desktop |
| Git | any | https://git-scm.com |

### 1. Clone and configure

```bash
git clone https://github.com/Akshat-Tated/UnitForge.git
cd UnitForge
cp .env.example .env
```

Edit `.env` with your settings. For LLM provider:

**Free (Gemini — recommended):**
```env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=AIzaSy...your-key
GEMINI_MODEL=gemini-1.5-flash
```

**Free (Ollama — fully local, no internet):**
```bash
# Install from https://ollama.com
ollama pull qwen2.5-coder:7b
```
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5-coder:7b
```

**Development (no AI calls):**
```env
LLM_PROVIDER=stub
```

### 2. Start infrastructure

```bash
docker-compose up postgres redis -d
```

### 3. Start all services

```bash
# Terminal 1 — Orchestrator API
cd orchestrator
mvn spring-boot:run

# Terminal 2 — Analysis engine
cd analysis-engine
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python server.py

# Terminal 3 — Test agents
cd test-agents
pip install -r requirements.txt
python agent.py

# Terminal 4 — Dashboard
cd dashboard
npm install
npm run dev
```

### 4. Open the dashboard

Go to **http://localhost:5173**
Register an account, add your Gemini API key in Settings, then click + Generate Tests.

---

## Using the CLI

```bash
cd unitforge-cli
pip install -e .

# Generate tests for a local project
unitforge generate ./my-project --download

# Generate tests from a GitHub URL
unitforge generate https://github.com/user/repo

# Check job status
unitforge status JOB-UUID

# Download tests
unitforge download JOB-UUID
```

---

## Troubleshooting

**"Failed to load jobs. Is the orchestrator running?"**
The dashboard cannot reach the backend. Make sure the orchestrator is running on port 8080.
Check: `curl http://localhost:8080/health`

**"No Gemini API key configured"**
Go to Settings and add your Gemini API key. Get a free one at https://aistudio.google.com

**"LLM generation failed: 404 model not found"**
Your Gemini model is deprecated. Update GEMINI_MODEL to `gemini-1.5-flash` in your .env or Render env vars.

**Agent not processing jobs**
Make sure `python agent.py` is running (locally or on Render). Check Redis connection in agent startup logs.

**Port 8080 already in use (Windows)**
```powershell
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

---

## Architecture overview

See [ARCHITECTURE.md](../ARCHITECTURE.md) for the complete specification.
See [docs/deployment.md](./deployment.md) for production deployment guide.

---

# Getting Started with UnitForge

This guide walks you through setting up UnitForge locally from scratch.

---

## Prerequisites

Install these before you begin:

| Tool | Version | Download |
|---|---|---|
| Java | 21 (LTS) | https://adoptium.net |
| Python | 3.12 | https://python.org/downloads |
| Node.js | 20 (LTS) | https://nodejs.org |
| Maven | 3.9+ | https://maven.apache.org/download.cgi |
| Docker Desktop | 24+ | https://docker.com/products/docker-desktop |
| Git | any | https://git-scm.com |

Verify your installs:
```bash
java --version     # openjdk 21
python --version   # Python 3.12.x
node --version     # v20.x.x
mvn --version      # Apache Maven 3.9.x
docker --version   # Docker version 24.x
```

---

## 1. Clone the repository

```bash
git clone https://github.com/your-username/UnitForge.git
cd UnitForge
```

---

## 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and choose your LLM provider:

**Free (no API key needed):**
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=deepseek-coder-v2
```
Install Ollama from https://ollama.com, then:
```bash
ollama pull deepseek-coder-v2
```

**Paid (best quality):**
```env
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=your-key-here
```

---

## 3. Start infrastructure

```bash
docker-compose up postgres redis -d
```

Verify both are healthy:
```bash
docker-compose ps
```
Both should show `running (healthy)`.

---

## 4. Start the Analysis Engine

```bash
cd analysis-engine

# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

Test it works:
```bash
python main.py --input tests/fixtures/sample_python_app --type python
```
Should print JSON with extracted functions.

---

## 5. Start the Orchestrator

Open a new terminal:
```bash
cd UnitForge/orchestrator
mvn spring-boot:run
```

Wait for:
```
Started UnitForgeApplication in X seconds
```

Test the API:
```bash
# Mac/Linux
curl -X POST http://localhost:8080/api/jobs \
  -H "Content-Type: application/json" \
  -d '{"inputType":"python","inputPath":"./sample"}'

# Windows PowerShell
Invoke-WebRequest -Uri "http://localhost:8080/api/jobs" `
  -Method POST -ContentType "application/json" `
  -Body '{"inputType":"python","inputPath":"./sample"}' `
  -UseBasicParsing | Select-Object -ExpandProperty Content
```

Expected: `{"jobId":"...","status":"QUEUED"}`

---

## 6. Start the Dashboard

Open another new terminal:
```bash
cd UnitForge/dashboard
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

---

## 7. Submit your first job

With all services running, point UnitForge at any Python project:

```bash
cd analysis-engine
python main.py --input /path/to/your/python/project --type python
```

The module map will be generated and can be sent to the orchestrator for
parallel test generation (Phase 2 feature — coming soon).

---

## Running with Docker (full stack)

To run everything in containers (takes 5–10 min to build first time):

```bash
docker-compose up -d
```

Services:
- Dashboard: http://localhost:3000
- Orchestrator API: http://localhost:8080
- PostgreSQL: localhost:5432
- Redis: localhost:6379

---

## Common issues

**`FATAL: password authentication failed`**
Your `application.yml` username/password doesn't match your Docker container.
Check both use `unitforge` / `unitforge`.

**`Port 8080 already in use`**
A previous Spring Boot process is still running. Kill it:
```bash
# Windows
netstat -ano | findstr :8080
taskkill /PID <the-pid> /F

# Mac/Linux
lsof -ti:8080 | xargs kill -9
```

**`invalid value for parameter "TimeZone": "Asia/Calcutta"`**
Your JVM timezone conflicts with PostgreSQL.
Run with: `mvn spring-boot:run "-Dspring-boot.run.jvmArguments=-Duser.timezone=UTC"`
Or add `<jvmArguments>-Duser.timezone=UTC</jvmArguments>` to pom.xml (already done).

**Ollama not connecting**
Make sure Ollama is running: open Ollama app or run `ollama serve`.
Check with: `curl http://localhost:11434/api/tags`

---

## Project structure

```
UnitForge/
├── analysis-engine/    # Python — parses code into module map
├── orchestrator/       # Spring Boot — REST API + job queue
├── test-agents/        # Python — LLM workers (Phase 2)
├── dashboard/          # React — live job monitoring UI
├── docs/               # Documentation
├── docker-compose.yml  # Infrastructure setup
└── ARCHITECTURE.md     # Source of truth
```

---

## Next steps

- Read [ARCHITECTURE.md](../ARCHITECTURE.md) to understand the full system
- Follow the [roadmap](../README.md#roadmap) to see what's coming in Phase 2
- Open an issue or PR on GitHub to contribute

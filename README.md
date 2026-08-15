---
<div align="center">

# ⚙️ UnitForge

**Open-source AI-powered unit test generation engine**

Feed it a GitHub URL. Get production-ready tests back. No installation. No setup. Works from any browser.

[![Status](https://img.shields.io/badge/status-live-brightgreen)](https://unit-forge.vercel.app)
[![License](https://img.shields.io/badge/license-MIT-blue)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://python.org)
[![Java](https://img.shields.io/badge/java-21-red)](https://adoptium.net)
[![Spring Boot](https://img.shields.io/badge/spring%20boot-3.3-brightgreen)](https://spring.io)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](./CONTRIBUTING.md)

**[Try it live →](https://unit-forge.vercel.app)** | [Architecture](#-architecture) | [Self-host](#-self-hosting) | [Contributing](./CONTRIBUTING.md)

</div>

---

## What is UnitForge?

UnitForge is an open-source AI-powered unit test generation engine. You give it a GitHub repository URL. It analyzes your Python code, spins up parallel AI agents — one per module — and generates production-quality pytest tests automatically.

No installation. No CLI. No API key required to try. Works on desktop, tablet, and mobile.

> 🆓 **BYOK model:** UnitForge uses *your* Gemini API key — 
> your quota, your data relationship with Google.
> Get a free key at [aistudio.google.com](https://aistudio.google.com).

---

## Try it now — 3 steps

1. Go to **[unit-forge.vercel.app](https://unit-forge.vercel.app)**
2. Register → Settings → paste your free Gemini API key
3. Click **+ Generate Tests** → paste any public Python GitHub URL

That is it. No downloads. No terminal.

---

## The problem it solves

Writing unit tests is the most skipped part of software development.
When developers do write them, coverage is patchy, edge cases are missed,
and tests go stale as the codebase evolves.

Enterprise tools like Diffblue Cover solve this — at **$30,000/year**,
Java-only, and completely closed-source.

**UnitForge is the open-source, free, Python-supporting alternative.**

---

## Architecture

```
User (any browser, any device)
            ↓
unit-forge.vercel.app — React dashboard
            ↓
unitforge-api.onrender.com — Spring Boot orchestrator
            ↓
unitforge-analysis.onrender.com — Python analysis engine (FastAPI)
            ↓
Upstash Redis — task queue
            ↓
unitforge-agent.onrender.com — Python test agent (24/7 cloud worker)
            ↓
Gemini API (user's own key) — AI test generation
            ↓
Supabase PostgreSQL — results storage
            ↓
Dashboard updates in real time via WebSocket
```

```
┌─────────────────────────────────────────┐
│              INPUT (from browser UI)    │
│   GitHub URL · OpenAPI spec URL         │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│         ANALYSIS ENGINE (Python/FastAPI)│
│   Clones repo · AST parser · OpenAPI    │
│   → module_map JSON                     │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│        ORCHESTRATOR (Spring Boot)       │
│   JWT auth · Redis queue · WebSocket    │
│   Per-user job isolation · PostgreSQL   │
└──────┬──────────┬──────────┬────────────┘
       │          │          │
┌──────▼──┐  ┌───▼─────┐  ┌─▼───────┐
│  Agent  │  │  Agent  │  │  Agent  │
│  Cloud  │  │  Cloud  │  │  Cloud  │  ← parallel, one per module
│  Gemini │  │  Gemini │  │  Gemini │
└──────┬──┘  └───┬─────┘  └─┬───────┘
       └─────────┴───────────┘
                   │
┌──────────────────▼──────────────────────┐
│           RESULTS & DASHBOARD           │
│   PostgreSQL · Coverage bars · React    │
│   WebSocket live updates · ZIP export   │
└─────────────────────────────────────────┘
```

---

## Features

### Core
- ✅ Python AST parsing — extracts all functions, classes, docstrings
- ✅ OpenAPI spec parsing — generates endpoint tests from YAML/JSON
- ✅ Parallel AI agents — one per module, all running simultaneously
- ✅ Real coverage measurement — `pytest --cov` with actual percentages
- ✅ Feedback loop — failed tests auto-retry with error context
- ✅ Empty module detection — skips untestable files intelligently

### Platform
- ✅ JWT authentication with per-user job isolation
- ✅ BYOK model — users bring their own Gemini API key (encrypted AES-256)
- ✅ WebSocket live updates — dashboard updates without page refresh
- ✅ Download generated tests — ZIP export directly from browser
- ✅ Rerun failed modules — one click to retry with running agent
- ✅ Works on mobile — no installation required

### Developer tools
- ✅ CLI tool — `unitforge generate ./my-project --download`
- ✅ GitHub URL support — clone and analyze any public repo
- ✅ Multiple LLM providers — Gemini (free), Claude, OpenAI, Ollama, Stub

---

## UnitForge vs Diffblue Cover

| | Diffblue Cover | UnitForge |
|---|---|---|
| Price | ~$30,000/year | Free |
| Source | Closed source | Open source (MIT) |
| Languages | Java only | Python + Java |
| Architecture | Single-threaded RL | Multi-agent parallel |
| LLM | Proprietary | Gemini / Claude / Ollama |
| Works offline | No | Yes (self-hosted + Ollama) |
| Mobile friendly | No | Yes |
| Self-hostable | No | Yes |
| Feedback loop | No | Yes |
| Real-time dashboard | No | Yes |

---

## Tech stack

| Layer | Technology |
|---|---|
| Analysis engine | Python 3.12, `ast`, PyYAML, GitPython, FastAPI |
| Orchestrator | Spring Boot 3.3, Java 21, Maven |
| Test agents | Python, google-genai SDK |
| Task queue | Redis (Upstash, SSL) |
| Database | PostgreSQL 16 (Supabase) |
| Dashboard | React 18, Vite, TypeScript, Tailwind CSS |
| Real-time | WebSocket (STOMP + SockJS) |
| Auth | JWT (RS256), BCrypt password hashing, AES-256 key encryption |
| Infrastructure | Docker, Docker Compose, Render, Vercel |

---

## Self-hosting

Want to run UnitForge on your own infrastructure?
See [docs/getting-started.md](./docs/getting-started.md) for the complete guide.

Quick start:
```bash
git clone https://github.com/Akshat-Tated/UnitForge.git
cd UnitForge
cp .env.example .env   # Edit .env with your credentials

docker-compose up postgres redis -d
cd orchestrator && mvn spring-boot:run   # terminal 1
cd test-agents && python agent.py        # terminal 2
cd dashboard && npm run dev              # terminal 3
```

CLI usage:
```bash
cd unitforge-cli
pip install -e .
unitforge generate https://github.com/user/repo --download
```

---

## Repository structure

```
UnitForge/
├── analysis-engine/        # Python FastAPI service — code analysis
│   ├── server.py           # HTTP server (POST /analyze)
│   ├── parsers/            # python_parser, openapi_parser
│   ├── models/             # ModuleMap dataclasses
│   └── github_cloner.py    # GitPython repo cloning
│
├── orchestrator/           # Spring Boot — REST API + job management
│   └── src/main/java/com/unitforge/
│       ├── controller/     # JobController, ResultController, AuthController
│       ├── service/        # JobService, TaskQueueService, JwtService, EncryptionService
│       └── model/          # TestJob, TestResult, User entities
│
├── test-agents/            # Python cloud worker — AI test generation
│   ├── agent.py            # Redis polling loop
│   ├── llm_client.py       # Gemini / Claude / Ollama / Stub providers
│   ├── prompt_builder.py   # LLM prompt construction
│   ├── test_runner.py      # pytest execution + coverage
│   └── health_server.py    # FastAPI health endpoint for Render
│
├── dashboard/              # React 18 — browser UI
│   └── src/
│       ├── pages/          # Dashboard, JobDetail, LoginPage, SettingsPage
│       └── components/     # SubmitJobModal, AgentCard, CoverageBar, StatusBadge
│
├── unitforge-cli/          # Python CLI tool
│   └── unitforge_cli/      # generate, status, download commands
│
├── docs/
│   ├── getting-started.md  # Self-hosting setup guide
│   └── deployment.md       # Production deployment guide
│
├── ARCHITECTURE.md         # Full project specification
├── docker-compose.yml      # Local infrastructure
├── render.yaml             # Render.com deployment config
└── .env.example            # Environment variable template
```

---

## Roadmap

- [x] **Phase 1** — Analysis engine, Spring Boot API, React dashboard, Docker ✅
- [x] **Phase 2** — LLM integration, Redis worker, test agent pipeline ✅
- [x] **Phase 3** — Real coverage, feedback loop, DONE status tracking ✅
- [x] **Phase 4** — WebSocket live updates, test downloads, coverage bars ✅
- [x] **Phase 5** — CLI tool, GitHub URL support, JWT auth, Gemini provider ✅
- [x] **Phase 6** — Full cloud deployment (Render + Vercel + Supabase + Upstash) ✅
- [x] **Phase 7** — Browser submit modal, BYOK API key, analysis engine as service ✅
- [ ] **Phase 8** — Google OAuth, email OTP verification, Java support, file upload

---

## Contributing

UnitForge is built in public. All contributions welcome.

1. Read [ARCHITECTURE.md](./ARCHITECTURE.md) — source of truth for all design decisions
2. Check [Issues](https://github.com/Akshat-Tated/UnitForge/issues) for things to work on
3. Read [CONTRIBUTING.md](./CONTRIBUTING.md) for dev setup
4. Open an issue before starting large features
5. Submit a PR against `main`

Good first contributions:
- Java AST parser (`analysis-engine/parsers/java_parser.py` — currently a stub)
- Spring Boot integration tests
- JavaScript/TypeScript parsing support

---

## License

MIT — free to use, modify, and distribute. See [LICENSE](./LICENSE).

---

<div align="center">
  <sub>
    Built by <a href="https://github.com/Akshat-Tated">Akshat Tated</a>
    · Open-source alternative to Diffblue Cover
    · <a href="https://unit-forge.vercel.app">Try it live</a>
    · <a href="./ARCHITECTURE.md">Architecture</a>
    · <a href="./docs/getting-started.md">Docs</a>
  </sub>
</div>

---

<div align="center">

<img src="https://img.shields.io/badge/⚙-UnitForge-cyan?style=for-the-badge" alt="UnitForge"/>

# UnitForge

**Open-source AI-powered unit test generation engine**

Feed it a codebase. Get production-ready tests back. No manual effort.

[![Status](https://img.shields.io/badge/status-phase%205%20complete-brightgreen)](https://github.com/Akshat-Tated/UnitForge)
[![License](https://img.shields.io/badge/license-MIT-blue)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://python.org)
[![Java](https://img.shields.io/badge/java-21-red)](https://adoptium.net)
[![Spring Boot](https://img.shields.io/badge/spring%20boot-3.3-brightgreen)](https://spring.io/projects/spring-boot)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](./CONTRIBUTING.md)

[Getting Started](#-quick-start) •
[Architecture](#-architecture) •
[Features](#-features) •
[Contributing](#-contributing) •
[Roadmap](#-roadmap)

</div>

---

## The problem

Writing unit tests is the most skipped part of software development.
When developers do write them, coverage is patchy, edge cases are missed,
and tests go stale as the codebase evolves.

Enterprise tools like Diffblue Cover solve this — but at **$30,000/year**,
Java-only, and completely closed-source.

**UnitForge is the open-source answer.**

> 🆓 **Free usage:** UnitForge works with [Ollama](https://ollama.com) locally —
> no API key, no cost, no data leaves your machine.
> `ollama pull qwen2.5-coder:14b`

---

## What it does

Point UnitForge at a Python or Java codebase (or an OpenAPI spec).
It spins up parallel AI agents — one per module — each generating unit tests,
integration tests, and edge cases. Failed tests feed back into the system
to generate smarter tests on the next run.

```bash
# Analyze a local project
python main.py --input ./my-project --type python

# The pipeline handles everything else automatically
```

---

## ✨ Features

### Phase 1 — Foundation
- ✅ Python AST parser — extracts functions, classes, and docstrings
- ✅ OpenAPI spec parser — generates tests from YAML/JSON API specs
- ✅ Spring Boot REST API — job management with PostgreSQL storage
- ✅ Redis task queue — distributes work across parallel agents
- ✅ React dashboard — live job monitoring with status badges
- ✅ Docker Compose — one-command infrastructure setup

### Phase 2 — AI Pipeline
- ✅ Pluggable LLM client — Claude, OpenAI, Ollama, or Stub (free dev mode)
- ✅ Redis worker agents — poll queue, call LLM, report results
- ✅ Prompt builder — specialized prompts with full AST context
- ✅ Feedback loop — failed tests retry with error context automatically
- ✅ Full pipeline — analysis engine → orchestrator → agents → results

### Phase 3 — Real Coverage
- ✅ pytest-cov integration — real coverage percentages, not placeholders
- ✅ Job DONE status — orchestrator tracks completion across all modules
- ✅ Dashboard live data — replaces mock data with real API calls
- ✅ Auto-refresh — dashboard polls every 10 seconds during active jobs
- ✅ Markdown fence stripping — handles LLM output formatting automatically

### Phase 4 — Real-time & Downloads
- ✅ WebSocket updates — dashboard refreshes instantly via STOMP/SockJS
- ✅ Toast notifications — popup when job status changes to DONE
- ✅ Download tests — exports all generated test files as a `.zip`
- ✅ Coverage visualization — animated progress bars (green/yellow/red)
- ✅ View generated tests — expandable code view per module

---

## 🏗 Architecture

```
┌─────────────────────────────────────────┐
│              INPUT                       │
│   Local folder · OpenAPI spec           │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│         ANALYSIS ENGINE (Python)         │
│   AST parser · OpenAPI parser           │
│   → module_map.json                     │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│        ORCHESTRATOR (Spring Boot)        │
│   REST API · Redis queue · WebSocket    │
└──────┬──────────┬──────────┬────────────┘
       │          │          │
┌──────▼──┐  ┌───▼─────┐  ┌─▼───────┐
│  Agent  │  │  Agent  │  │  Agent  │  ← parallel, one per module
│ Module A│  │ Module B│  │ Module C│
│   LLM   │  │   LLM   │  │   LLM   │
└──────┬──┘  └───┬─────┘  └─┬───────┘
       └─────────┴───────────┘
                   │
┌──────────────────▼──────────────────────┐
│           RESULTS & DASHBOARD            │
│   PostgreSQL · Coverage bars · React    │
│   WebSocket live updates · ZIP download │
└─────────────────────────────────────────┘
```

---

## 🛠 Tech stack

| Layer | Technology |
|---|---|
| Analysis engine | Python 3.12, `ast` module, PyYAML |
| Orchestrator | Spring Boot 3.3, Java 21, Maven |
| Task queue | Redis 7 |
| Test agents | Python, Anthropic SDK / Ollama / OpenAI |
| Database | PostgreSQL 16 |
| Dashboard | React 18, Vite, TypeScript, Tailwind CSS |
| Real-time | WebSocket (STOMP + SockJS) |
| Infrastructure | Docker, Docker Compose, nginx |

---

## Quick start

### Option A — One command (CLI)
```bash
pip install -e ./unitforge-cli
unitforge generate ./my-project
```

### Option B — Full stack
```bash
cp .env.example .env
docker-compose up postgres redis -d
cd orchestrator && mvn spring-boot:run   # terminal 1
cd test-agents && python agent.py        # terminal 2
cd dashboard && npm run dev              # terminal 3
```

---

## 📊 UnitForge vs Diffblue Cover

| | Diffblue Cover | UnitForge |
|---|---|---|
| Price | ~$30,000/year | Free (self-hosted) |
| Source | Closed, proprietary | Open source (MIT) |
| Languages | Java only | Python + Java |
| Architecture | Single-threaded RL | Multi-agent parallel |
| LLM provider | Proprietary | Claude / OpenAI / Ollama |
| Works offline | No | Yes (with Ollama) |
| Self-hostable | No | Yes |
| Feedback loop | No | Yes (auto-retry on failure) |
| Real-time dashboard | No | Yes (WebSocket) |
| Download tests | No | Yes (.zip export) |

---

## 📁 Repository structure

```
UnitForge/
├── analysis-engine/        # Python — parses code into module map
│   ├── parsers/            # python_parser, openapi_parser, java_parser
│   ├── models/             # ModuleMap, FunctionInfo, EndpointInfo dataclasses
│   ├── tests/              # pytest tests + sample fixtures
│   └── main.py             # CLI: python main.py --input PATH --type TYPE
│
├── orchestrator/           # Spring Boot — REST API + job management
│   └── src/main/java/com/unitforge/
│       ├── controller/     # JobController, ResultController, DownloadController
│       ├── service/        # JobService, TaskQueueService, WebSocketService
│       ├── model/          # TestJob, TestResult, JobStatus entities
│       └── config/         # Redis, WebSocket configuration
│
├── test-agents/            # Python workers — LLM test generation
│   ├── agent.py            # Redis worker: poll → generate → run → report
│   ├── prompt_builder.py   # Builds specialized LLM prompts from module info
│   ├── test_runner.py      # Runs generated tests via subprocess + coverage
│   └── llm_client.py      # Pluggable: Claude / OpenAI / Ollama / Stub
│
├── dashboard/              # React 18 + Vite + TypeScript + Tailwind
│   └── src/
│       ├── pages/          # Dashboard.tsx, JobDetail.tsx
│       ├── components/     # AgentCard, StatusBadge, CoverageBar
│       └── hooks/          # useWebSocket for real-time updates
│
├── docs/                   # Documentation
│   └── getting-started.md
│
├── ARCHITECTURE.md         # Full project specification (source of truth)
├── docker-compose.yml      # Infrastructure: postgres + redis + services
└── .env.example            # Environment variable template
```

---

## 🗺 Roadmap

- [x] Phase 1 — Analysis engine, Spring Boot, React dashboard ✅
- [x] Phase 2 — LLM integration, Redis worker, test agents ✅
- [x] Phase 3 — Real coverage, feedback loop, DONE status ✅
- [x] Phase 4 — WebSocket live updates, download, coverage bars ✅
- [x] Phase 5 — CLI tool, GitHub URL, JWT auth, GitHub Actions ✅
- [ ] **Phase 6** — Cloud version, managed hosting, team features

---

## 🤝 Contributing

UnitForge is built in public and welcomes contributions of all kinds.

1. Read [ARCHITECTURE.md](./ARCHITECTURE.md) — the source of truth for all design decisions
2. Check open [Issues](https://github.com/Akshat-Tated/UnitForge/issues) for things to work on
3. Read [CONTRIBUTING.md](./CONTRIBUTING.md) for development setup
4. Open an issue before starting large features
5. Submit a PR against `main`

---

## 📄 License

MIT — free to use, modify, and distribute. See [LICENSE](./LICENSE) for details.

---

<div align="center">
  <sub>
    Built by <a href="https://github.com/Akshat-Tated">Akshat Tated</a>
    · Open-source alternative to Diffblue Cover
    · <a href="./ARCHITECTURE.md">Architecture</a>
    · <a href="./docs/getting-started.md">Docs</a>
  </sub>
</div>

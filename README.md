<div align="center">
  <h1>⚙️ UnitForge</h1>
  <p><strong>Open-source AI-powered unit test generation engine</strong></p>
  <p>Feed it a codebase. Get production-ready tests back. No manual effort.</p>

  ![Status](https://img.shields.io/badge/status-phase%201%20complete-brightgreen)
  ![License](https://img.shields.io/badge/license-MIT-blue)
  ![Python](https://img.shields.io/badge/python-3.12-blue)
  ![Java](https://img.shields.io/badge/java-21-red)
  ![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)
</div>

---

## The problem

Writing unit tests is the most skipped part of software development.
When developers do write them, coverage is patchy, edge cases are missed,
and tests go stale as the codebase evolves.

Enterprise tools like Diffblue Cover solve this — but at $30,000/year,
Java-only, and completely closed-source.

**UnitForge is the open-source answer.**

> 🆓 **Free usage:** UnitForge works with [Ollama](https://ollama.com) locally —
> no API key, no cost, no data leaves your machine.
> `ollama pull deepseek-coder-v2`

---

## What it does

Point UnitForge at a Python or Java codebase (or an OpenAPI spec).
It spins up parallel AI agents — one per module — each generating unit tests,
integration tests, and edge cases. Failed tests feed back into the system
to generate smarter tests on the next run.

```bash
python main.py --input ./my-app --type python
python main.py --input ./api-spec.yaml --type openapi
```

---

## Architecture

```
┌─────────────────────────────────────────┐
│              INPUT                       │
│   GitHub URL · Local folder · OpenAPI   │
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
│  Agent  │  │  Agent  │  │  Agent  │   ← parallel, one per module
│ Module A│  │ Module B│  │ Module C│
│  LLM   │  │  LLM   │  │  LLM   │
└──────┬──┘  └───┬─────┘  └─┬───────┘
       └─────────┴───────────┘
                   │
┌──────────────────▼──────────────────────┐
│           RESULTS & DASHBOARD            │
│   PostgreSQL · Coverage map · React UI  │
│   Feedback loop → smarter next run      │
└─────────────────────────────────────────┘
```

---

## Quick start

```bash
# 1. Clone
git clone https://github.com/Akshat-Tated/UnitForge.git
cd UnitForge

# 2. Configure (free with Ollama or paid with Claude)
cp .env.example .env

# 3. Start infrastructure
docker-compose up postgres redis -d

# 4. Start orchestrator (new terminal)
cd orchestrator && mvn spring-boot:run

# 5. Start dashboard (new terminal)
cd dashboard && npm install && npm run dev

# 6. Open http://localhost:5173
```

See [docs/getting-started.md](docs/getting-started.md) for the full setup guide.

---

## Repository structure

```
UnitForge/
├── analysis-engine/        # Python — parses code into module map
│   ├── parsers/
│   │   ├── python_parser.py
│   │   ├── openapi_parser.py
│   │   └── java_parser.py
│   ├── models/
│   │   └── module_map.py
│   ├── tests/
│   │   └── fixtures/
│   ├── main.py
│   └── requirements.txt
│
├── orchestrator/           # Spring Boot — job manager + REST API
│   └── src/main/java/com/unitforge/
│
├── test-agents/            # Python workers — LLM test generation (Phase 2)
│
├── dashboard/              # React 18 + Vite + TypeScript + Tailwind
│
├── docs/
│   ├── architecture.md
│   └── getting-started.md
│
├── ARCHITECTURE.md         # Source of truth for the entire project
├── docker-compose.yml      # Infrastructure setup
└── .env.example            # Environment variable template
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Analysis engine | Python 3.12, `ast`, PyYAML, javalang |
| Orchestrator | Spring Boot 3.3, Java 21, Redis |
| Test agents | Python, Anthropic SDK (Claude) / Ollama (free) |
| Test runner | Docker (isolated execution) |
| Database | PostgreSQL 16 |
| Dashboard | React 18, Vite, TypeScript, Tailwind |

---

## UnitForge vs Diffblue Cover

| | Diffblue Cover | UnitForge |
|---|---|---|
| Price | ~$30,000/year | Free (self-hosted) |
| Source | Closed | Open source (MIT) |
| Languages | Java only | Python + Java |
| Architecture | Single-threaded | Multi-agent parallel |
| LLM provider | Proprietary | Claude / OpenAI / Ollama |
| Works offline | No | Yes (with Ollama) |
| Self-hostable | No | Yes |

---

## Roadmap

- [x] **Phase 1** — Analysis engine (Python AST + OpenAPI parser) · Spring Boot REST API · Redis queue · React dashboard ✅
- [ ] **Phase 2** — LLM integration (Claude + Ollama), Redis worker, parallel test agents
- [ ] **Phase 3** — Docker test runner, coverage analysis, feedback loop
- [ ] **Phase 4** — WebSocket live updates, downloadable reports, CI/CD integration
- [ ] **Phase 5** — Cloud version, authentication, team features

---

## Contributing

UnitForge is being built in public. All contributions, issues, and ideas are welcome.

1. Fork the repo
2. Read [`ARCHITECTURE.md`](./ARCHITECTURE.md) — this is the source of truth
3. Open an issue before starting any major work
4. Submit a PR against `main`

See [`docs/getting-started.md`](./docs/getting-started.md) for detailed setup.

---

## License

MIT — free to use, modify, and distribute.

---

<div align="center">
  <sub>Built by <a href="https://github.com/Akshat-Tated">Akshat</a> · Open-source alternative to Diffblue Cover</sub>
</div>

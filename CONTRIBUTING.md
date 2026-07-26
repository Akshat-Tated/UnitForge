# Contributing to UnitForge

Thank you for your interest in contributing to UnitForge.
This document explains how to get set up and how contributions work.

---

## Before you start

Read [ARCHITECTURE.md](./ARCHITECTURE.md) first. It is the single source of truth
for every design decision in the project — naming, folder structure, API contracts,
technology choices, and phase roadmap. Any contribution should align with it.

---

## What we need help with

Check the [Issues](https://github.com/Akshat-Tated/UnitForge/issues) tab.
Good first contributions:

- **Java parser** — `analysis-engine/parsers/java_parser.py` is a stub.
  Implementing it using the `javalang` library would be hugely valuable.
- **Test coverage** — The Spring Boot orchestrator has no automated tests.
  Adding integration tests with H2 in-memory database would improve reliability.
- **Language support** — Adding JavaScript/TypeScript parsing via AST.
- **Bug reports** — If something does not work, open an issue with
  the exact error message and your OS / Python / Java versions.
- **Documentation** — Improving `docs/getting-started.md` or adding examples.

---

## Development setup

### Prerequisites

| Tool | Version | Download |
|---|---|---|
| Java | 21 (LTS) | https://adoptium.net |
| Python | 3.12 | https://python.org |
| Node.js | 20 (LTS) | https://nodejs.org |
| Maven | 3.9+ | https://maven.apache.org |
| Docker Desktop | 24+ | https://docker.com/products/docker-desktop |

### Clone and set up

```bash
git clone https://github.com/Akshat-Tated/UnitForge.git
cd UnitForge
cp .env.example .env
```

### Start infrastructure

```bash
docker-compose up postgres redis -d
```

### Run the analysis engine tests

```bash
cd analysis-engine
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
pip install -r requirements.txt
pytest tests/ -v
```

All tests must pass before submitting a PR.

### Run the orchestrator

```bash
cd orchestrator
mvn spring-boot:run
```

### Run the test agents

```bash
cd test-agents
pip install -r requirements.txt
# Set LLM_PROVIDER=stub in .env for development (no API key needed)
python agent.py
```

### Run the dashboard

```bash
cd dashboard
npm install
npm run dev
```

---

## Project structure (quick reference)

```
analysis-engine/   ← Python: code parsing, AST, OpenAPI
orchestrator/      ← Java Spring Boot: REST API, job queue
test-agents/       ← Python: LLM calls, test running
dashboard/         ← React: job monitoring UI
docs/              ← Documentation
```

Each folder is independent. If you are fixing a Python parser bug,
you only need to touch `analysis-engine/`. If you are adding a new
API endpoint, only `orchestrator/` changes.

---

## Contribution workflow

1. **Fork** the repository
2. **Create a branch** for your change:
   ```bash
   git checkout -b feat/java-parser
   git checkout -b fix/coverage-parsing-bug
   ```
3. **Make your changes** — keep each PR focused on one thing
4. **Write or update tests** — PRs without tests will be asked to add them
5. **Run existing tests** — make sure nothing is broken:
   ```bash
   cd analysis-engine && pytest tests/ -v
   ```
6. **Commit with a clear message:**
   ```bash
   git commit -m "feat(analysis-engine): implement Java AST parser using javalang"
   git commit -m "fix(test-runner): handle syntax errors in generated test code"
   ```
7. **Push and open a PR** — describe what you changed and why

---

## Commit message format

We use conventional commits:

```
type(scope): short description

Types: feat, fix, docs, chore, test, refactor
Scopes: analysis-engine, orchestrator, test-agents, dashboard, docs, infra
```

Examples:
```
feat(test-agents): add OpenAI provider to llm_client
fix(orchestrator): set timezone to UTC to fix PostgreSQL Asia/Calcutta error
docs(readme): update quick start with Ollama instructions
test(analysis-engine): add edge case tests for empty Python files
```

---

## Code standards

### Python (analysis-engine, test-agents)
- Type hints on every function and variable
- Docstrings on every public function
- `dataclasses` for structured data
- `logging` module (not `print` statements)
- All exceptions handled gracefully

### Java (orchestrator)
- Lombok `@Data`, `@Builder`, `@RequiredArgsConstructor` everywhere
- No business logic in controllers
- Use `@Value` for configuration, never hardcode strings
- Constructor injection (not field injection with `@Autowired`)

### React (dashboard)
- TypeScript strict mode
- Functional components only, no class components
- Tailwind utility classes only, no inline styles
- Handle loading and error states in every component that fetches data

---

## Questions?

Open a [GitHub Issue](https://github.com/Akshat-Tated/UnitForge/issues/new)
with the `question` label. Happy to help.

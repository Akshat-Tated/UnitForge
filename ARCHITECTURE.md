# UnitForge — Project Initialization Brief

You are bootstrapping a new open-source project called **UnitForge** from scratch.
GitHub repo: https://github.com/Akshat-Tated/UnitForge

Read this entire brief before writing a single file. When you are done reading,
dispatch 3 parallel agents as described at the bottom.

---

## What UnitForge is

UnitForge is an open-source, AI-powered multi-agent unit test generation engine.
It reads a Python or Java codebase (or an OpenAPI spec) and autonomously generates
unit tests, integration tests, and edge-case tests — in parallel, one agent per module.

It is the open-source alternative to Diffblue Cover (Java-only, $30,000/year, closed-source).
UnitForge supports Python + Java, is self-hostable, and has a feedback loop: failed tests
teach the system to generate smarter tests on the next run.

Target users: developers and small-to-mid teams who cannot afford Diffblue.
Monetization: OSS core forever. Paid cloud version later (open-core model like PostHog/Sentry).

---

## Five-Layer Architecture

Layer 1 — INPUT
  Accepts: GitHub repo URL, local folder, or OpenAPI spec (YAML/JSON)

Layer 2 — ANALYSIS ENGINE (Python)
  - Clones/reads the codebase
  - Parses Python files with AST (ast module), Java files with javalang
  - Parses OpenAPI specs with PyYAML + jsonschema
  - Builds a MODULE MAP: JSON describing each module's functions,
    classes, dependencies, and endpoints
  - Output: module_map.json passed to orchestrator

Layer 3 — ORCHESTRATOR (Spring Boot)
  - REST API that accepts jobs
  - Splits module_map.json into per-module tasks
  - Pushes tasks onto a Redis task queue
  - Dispatches N parallel TestAgent workers (one per module)
  - WebSocket endpoint for real-time status updates to frontend

Layer 4 — TEST AGENTS (Python workers)
  - Each agent picks one module task from Redis
  - Builds an LLM prompt with: function signatures, docstrings, dependencies
  - Calls Claude API (claude-sonnet-4-6) to generate test code
  - Executes generated tests in an isolated Docker container
  - Reports: pass/fail, coverage %, generated test file
  - On failure: refines the prompt and retries once (feedback loop)

Layer 5 — RESULTS + DASHBOARD (React + Spring Boot)
  - Postgres stores: TestRun, TestResult, CoverageReport, AgentLog
  - Spring Boot REST API serves results
  - React dashboard shows: live agent status, coverage map, downloadable test files

---

## Tech Stack — exact versions

Python:        3.12
  Libraries:   ast (stdlib), javalang 0.13, PyYAML 6.0, jsonschema 4.23,
               anthropic 0.30 (Claude SDK), pytest 8.2, redis-py 5.0,
               docker 7.1, coverage 7.5

Spring Boot:   3.3.x (Java 21)
  Libraries:   Spring Web, Spring Data JPA, Spring WebSocket,
               Spring Data Redis, Lombok, PostgreSQL driver

React:         18.x (Vite)
  Libraries:   Tailwind CSS 3.x, Recharts, React Query, Zustand

Infrastructure: Redis 7, PostgreSQL 16, Docker 24

---

## Monorepo Structure to create

UnitForge/
├── README.md                        ← project overview (write this)
├── docker-compose.yml               ← Redis + Postgres + all services
├── .gitignore
│
├── analysis-engine/                 ← Python: parses code into module map
│   ├── README.md
│   ├── requirements.txt
│   ├── main.py                      ← CLI entry: --input <path> --type <python|java|openapi>
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── python_parser.py         ← AST-based Python module parser
│   │   ├── openapi_parser.py        ← OpenAPI YAML/JSON parser
│   │   └── java_parser.py           ← javalang-based Java parser (stub for now)
│   ├── models/
│   │   ├── __init__.py
│   │   └── module_map.py            ← ModuleMap, ModuleInfo, FunctionInfo dataclasses
│   └── tests/
│       ├── fixtures/
│       │   ├── sample_python_app/   ← a tiny Python app with 3 functions to parse
│       │   └── sample_openapi.yaml  ← a 5-endpoint OpenAPI spec
│       └── test_python_parser.py
│
├── orchestrator/                    ← Spring Boot: job manager + REST API
│   ├── README.md
│   ├── pom.xml
│   └── src/main/java/com/unitforge/
│       ├── UnitForgeApplication.java
│       ├── controller/
│       │   ├── JobController.java   ← POST /api/jobs, GET /api/jobs/{id}
│       │   └── ResultController.java ← GET /api/jobs/{id}/results
│       ├── service/
│       │   ├── JobService.java
│       │   └── TaskQueueService.java ← pushes to Redis list unitforge:tasks
│       ├── model/
│       │   ├── TestJob.java         ← JPA entity
│       │   ├── TestResult.java      ← JPA entity
│       │   └── JobStatus.java       ← enum: QUEUED, RUNNING, DONE, FAILED
│       ├── repository/
│       │   ├── TestJobRepository.java
│       │   └── TestResultRepository.java
│       └── config/
│           ├── RedisConfig.java
│           └── WebSocketConfig.java
│
├── test-agents/                     ← Python workers: generate + run tests
│   ├── README.md
│   ├── requirements.txt
│   ├── agent.py                     ← main worker loop: poll Redis → process → report
│   ├── prompt_builder.py            ← builds LLM prompt from ModuleInfo
│   ├── llm_client.py               ← wraps anthropic SDK
│   ├── test_runner.py              ← runs generated tests in subprocess/Docker
│   └── tests/
│       └── test_prompt_builder.py
│
├── dashboard/                       ← React frontend
│   ├── README.md
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── pages/
│       │   ├── Dashboard.tsx        ← job list + status overview
│       │   └── JobDetail.tsx        ← per-job: agent status, coverage, test files
│       ├── components/
│       │   ├── AgentCard.tsx        ← live status of one agent (module name, %, pass/fail)
│       │   └── CoverageBar.tsx
│       └── api/
│           └── client.ts            ← axios wrapper for Spring Boot REST
│
└── docs/
    ├── architecture.md
    └── getting-started.md

---

## Phase 1 — What to build RIGHT NOW

Build only Phase 1. Do not build everything at once.

Phase 1 goal: A working analysis engine that can parse a Python file or OpenAPI spec
and produce a valid module_map.json. Nothing else should be built beyond the skeletons.

### Agent A — Python Analysis Engine (build fully working code)
Tasks:
1. Create analysis-engine/ with all files listed above
2. python_parser.py must:
   - Use Python ast module to walk a .py file
   - Extract: module name, all functions (name, args, return type hint if present,
     docstring, line number), all classes (name, methods), imports
   - Return a ModuleInfo object (defined in models/module_map.py)
3. openapi_parser.py must:
   - Load a YAML or JSON OpenAPI 3.x spec
   - Extract: each path + method as an "endpoint"
   - For each endpoint: path, method, summary, parameters (name, type, required),
     request body schema (if present), response schema for 200/201
   - Return a list of EndpointInfo objects
4. models/module_map.py must define:
   - FunctionInfo(name, args, return_type, docstring, line_no)
   - ClassInfo(name, methods: List[FunctionInfo])
   - EndpointInfo(path, method, summary, parameters, request_body, response_schema)
   - ModuleInfo(name, file_path, type: 'python'|'openapi', functions, classes, endpoints)
   - ModuleMap(modules: List[ModuleInfo]) with a .to_json() method
5. main.py must be a CLI:
   python main.py --input ./my_app --type python → prints module_map.json to stdout
   python main.py --input ./spec.yaml --type openapi → prints module_map.json to stdout
6. Create sample fixtures (sample_python_app/ with 3 real functions, sample_openapi.yaml
   with 5 endpoints) so tests have real data to run against
7. Write test_python_parser.py with at least 5 pytest tests covering:
   - Function extraction (name, args, docstring)
   - Class method extraction
   - Import detection
   - Edge case: empty file
   - Edge case: file with only classes, no top-level functions

### Agent B — Spring Boot Orchestrator skeleton (compilable, not fully wired)
Tasks:
1. Create orchestrator/ with a valid pom.xml (Spring Boot 3.3, Java 21)
2. Create the package structure with all files listed above
3. TestJob entity: fields = id (UUID), status (JobStatus), inputType, inputPath,
   createdAt, updatedAt
4. TestResult entity: fields = id, jobId (FK), moduleName, passed (boolean),
   coveragePercent, generatedTestCode (text), agentLog (text), createdAt
5. JobController: POST /api/jobs (accepts { inputType, inputPath }), returns job ID
6. GET /api/jobs/{id} returns job status
7. GET /api/jobs/{id}/results returns list of TestResult for that job
8. TaskQueueService: pushes module tasks to Redis list key "unitforge:tasks"
9. application.yml: configure postgres datasource (localhost:5432/unitforge),
   redis (localhost:6379), server port 8080
10. The app must compile and start with mvn spring-boot:run (even if endpoints
    return stub data for now)

### Agent C — Project skeleton + docs
Tasks:
1. Write README.md: project description, architecture diagram in ASCII art,
   tech stack table, quick start instructions (docker-compose up), contribution guide
2. Write docker-compose.yml:
   services: postgres (image: postgres:16, env POSTGRES_DB=unitforge), 
   redis (image: redis:7-alpine), 
   analysis-engine (build: ./analysis-engine, command: python main.py),
   orchestrator (build: ./orchestrator, port 8080),
   dashboard (build: ./dashboard, port 3000)
3. Create React dashboard/: Vite + React 18 + TypeScript + Tailwind setup
4. Dashboard.tsx: a simple page showing "UnitForge" header + a list of jobs
   from GET /api/jobs (mock data for now, 3 example jobs with status badges)
5. Write docs/architecture.md explaining the 5-layer system
6. Write .gitignore covering Python, Java/Maven, Node, and Docker

---

## Coding Conventions

- Python: snake_case, type hints everywhere, docstrings on all public functions,
  dataclasses for models, no external ORM (raw dataclasses + json)
- Java: camelCase, Lombok @Data/@Builder on entities, no business logic in controllers
- React: TypeScript strict mode, functional components only, no class components
- All strings that call the LLM go in prompt_builder.py only — never inline
- No hardcoded API keys anywhere — use environment variables (ANTHROPIC_API_KEY)
- Every Python module must have a corresponding test file before marking Phase 1 done

---

## What NOT to build yet (Phase 2+)

- Do not build the LLM call (llm_client.py) yet — stub it to return a hardcoded
  test string
- Do not build the Docker test runner yet — stub test_runner.py to return
  { passed: True, coverage: 85.0 }
- Do not build WebSocket real-time updates yet
- Do not set up CI/CD yet
- Do not build the feedback loop yet

---

## Verification checklist before marking Phase 1 complete

Agent A must verify:
  [ ] python main.py --input tests/fixtures/sample_python_app --type python
      produces valid JSON with at least 3 functions extracted
  [ ] python main.py --input tests/fixtures/sample_openapi.yaml --type openapi
      produces valid JSON with at least 5 endpoints extracted
  [ ] pytest tests/ passes with 0 failures

Agent B must verify:
  [ ] mvn spring-boot:run starts without errors
  [ ] curl -X POST http://localhost:8080/api/jobs -H "Content-Type: application/json"
      -d '{"inputType":"python","inputPath":"./sample"}' returns a job ID

Agent C must verify:
  [ ] docker-compose up starts postgres and redis without errors
  [ ] npm run dev in dashboard/ opens a page at localhost:3000 without errors
  [ ] README renders correctly on GitHub
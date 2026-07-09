# UnitForge — Analysis Engine

The **Analysis Engine** is Layer 2 of UnitForge. It reads a Python codebase or
OpenAPI specification and produces a structured `module_map.json` that the
orchestrator uses to dispatch parallel test-generation agents.

## Supported inputs

| Input type | Parser            | Status       |
|------------|-------------------|--------------|
| Python     | `ast` (stdlib)    | ✅ Working   |
| OpenAPI    | PyYAML + jsonschema | ✅ Working |
| Java       | `javalang`        | 🔜 Stub     |

## Quick start

```bash
# Install dependencies
pip install -r requirements.txt

# Parse a Python project
python main.py --input ./my_app --type python

# Parse an OpenAPI spec
python main.py --input ./spec.yaml --type openapi
```

## Running tests

```bash
pytest tests/ -v
```

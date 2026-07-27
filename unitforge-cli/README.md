# UnitForge CLI

Command-line interface for UnitForge.

## Install

```bash
cd unitforge-cli
pip install -e .
```

## Usage

```bash
# Generate tests for a local project
unitforge generate ./my-project

# Generate tests from a GitHub URL
unitforge generate https://github.com/user/repo

# Generate and download tests in one command
unitforge generate ./my-project --download

# Check job status
unitforge status <job-id>

# Download tests for a completed job
unitforge download <job-id>
```

## Requirements

The orchestrator must be running:
  cd orchestrator && mvn spring-boot:run

The test agent must be running:
  cd test-agents && python agent.py

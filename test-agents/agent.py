"""
UnitForge — Test Agent Worker
===============================
Main worker process that polls Redis for test-generation tasks,
builds LLM prompts, generates test code, runs the tests, and
reports results back to the orchestrator.

Usage:
    python agent.py

Configuration via environment variables (or .env file):
    REDIS_HOST          (default: localhost)
    REDIS_PORT          (default: 6379)
    ORCHESTRATOR_URL    (default: http://localhost:8080)
    MAX_RETRY_ATTEMPTS  (default: 2)
    LLM_PROVIDER        (default: stub)
"""

import json
import logging
import os
import sys
from typing import Any, Optional

import requests
from dotenv import load_dotenv

from llm_client import LLMClient, LLMResponse
from prompt_builder import build_system_prompt, build_test_prompt
from test_runner import TestRunResult, run_tests

# ─────────────────────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger: logging.Logger = logging.getLogger("unitforge.agent")


# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

def _load_config() -> dict[str, Any]:
    """Load agent configuration from environment variables.

    Returns:
        A dictionary with all configuration values, using defaults
        where environment variables are not set.
    """
    load_dotenv()

    config: dict[str, Any] = {
        "redis_host": os.getenv("REDIS_HOST", "localhost"),
        "redis_port": int(os.getenv("REDIS_PORT", "6379")),
        "orchestrator_url": os.getenv("ORCHESTRATOR_URL", "http://localhost:8080"),
        "max_retry_attempts": int(os.getenv("MAX_RETRY_ATTEMPTS", "2")),
        "redis_queue_key": os.getenv("REDIS_QUEUE_KEY", "unitforge:tasks"),
    }
    return config


# ─────────────────────────────────────────────────────────────
# Redis connection
# ─────────────────────────────────────────────────────────────

def _connect_redis(host: str, port: int) -> Any:
    """Connect to Redis and verify the connection.

    Args:
        host: Redis server hostname.
        port: Redis server port.

    Returns:
        A connected redis.Redis client instance.

    Raises:
        ConnectionError: If Redis is unreachable.
    """
    import redis

    client: Any = redis.Redis(host=host, port=port, decode_responses=True)

    try:
        client.ping()
        logger.info("Connected to Redis at %s:%d", host, port)
    except redis.ConnectionError as exc:
        raise ConnectionError(
            f"Cannot connect to Redis at {host}:{port}. "
            f"Is Redis running? Error: {exc}"
        ) from exc

    return client


# ─────────────────────────────────────────────────────────────
# Result reporting
# ─────────────────────────────────────────────────────────────

def _report_result(
    orchestrator_url: str,
    job_id: str,
    module_name: str,
    passed: bool,
    coverage_percent: float,
    generated_test_code: str,
    agent_log: str,
) -> None:
    """Report test results back to the orchestrator via HTTP POST.

    Args:
        orchestrator_url: Base URL of the orchestrator service.
        job_id: The job ID this result belongs to.
        module_name: Name of the module that was tested.
        passed: Whether the generated tests passed.
        coverage_percent: Code coverage percentage.
        generated_test_code: The generated test source code.
        agent_log: Human-readable log of what the agent did.
    """
    # NOTE: The orchestrator currently only has GET /api/jobs/{id}/results.
    # A POST endpoint must be added to the orchestrator to receive these results.
    # See: orchestrator/src/main/java/com/unitforge/controller/JobController.java
    url: str = f"{orchestrator_url}/api/jobs/{job_id}/results"
    payload: dict[str, Any] = {
        "moduleName": module_name,
        "passed": passed,
        "coveragePercent": coverage_percent,
        "generatedTestCode": generated_test_code,
        "agentLog": agent_log,
    }

    try:
        response: requests.Response = requests.post(
            url,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        logger.info(
            "Reported result for module '%s' to %s (status=%d)",
            module_name,
            url,
            response.status_code,
        )
    except requests.RequestException as exc:
        logger.error(
            "Failed to report result for module '%s' to %s: %s",
            module_name,
            url,
            exc,
        )


# ─────────────────────────────────────────────────────────────
# Task processing
# ─────────────────────────────────────────────────────────────

def _process_task(
    task: dict[str, Any],
    llm_client: LLMClient,
    config: dict[str, Any],
) -> None:
    """Process a single task from the Redis queue.

    Builds the LLM prompt, generates test code, runs the tests,
    retries on failure if allowed, and reports results.

    Args:
        task: The parsed task dictionary from Redis.
        llm_client: The configured LLM client instance.
        config: Agent configuration dictionary.
    """
    module_name: str = task.get("moduleName", "unknown")
    job_id: str = task.get("jobId", "unknown")
    module_info_json: str = task.get("moduleInfoJson", "{}")

    logger.info("Processing task — job=%s, module=%s", job_id, module_name)

    # ── Parse module info ────────────────────────────────────
    try:
        module_info: dict[str, Any] = json.loads(module_info_json)
    except json.JSONDecodeError as exc:
        logger.error("Invalid moduleInfoJson for module '%s': %s", module_name, exc)
        _report_result(
            orchestrator_url=config["orchestrator_url"],
            job_id=job_id,
            module_name=module_name,
            passed=False,
            coverage_percent=0.0,
            generated_test_code="",
            agent_log=f"Failed to parse moduleInfoJson: {exc}",
        )
        return

    # ── Build prompt and generate tests ──────────────────────
    module_code: str = task.get("moduleCode", "")
    base_prompt: str = build_test_prompt(module_info, module_code=module_code)
    system_prompt: str = build_system_prompt()

    max_retries: int = config["max_retry_attempts"]
    retry_count: int = 0
    test_code: str = ""
    result: Optional[TestRunResult] = None
    prompt: str = base_prompt

    while retry_count <= max_retries:
        attempt_label: str = (
            "initial attempt" if retry_count == 0
            else f"retry {retry_count}/{max_retries}"
        )
        logger.info("Generating tests for '%s' (%s)", module_name, attempt_label)

        try:
            llm_response: LLMResponse = llm_client.generate(
                prompt=prompt,
                system=system_prompt,
            )
            test_code = llm_response.content
        except Exception as exc:
            logger.error(
                "LLM generation failed for module '%s': %s",
                module_name,
                exc,
            )
            _report_result(
                orchestrator_url=config["orchestrator_url"],
                job_id=job_id,
                module_name=module_name,
                passed=False,
                coverage_percent=0.0,
                generated_test_code="",
                agent_log=f"LLM generation failed: {exc}",
            )
            return

        # ── Run the generated tests ──────────────────────────
        try:
            result = run_tests(test_code=test_code, module_name=module_name)
        except Exception as exc:
            logger.error(
                "Test execution failed for module '%s': %s",
                module_name,
                exc,
            )
            result = TestRunResult(
                passed=False,
                coverage_percent=0.0,
                error_message=f"Test execution error: {exc}",
                output=str(exc),
                generated_file_path="",
            )

        if result.passed:
            logger.info(
                "Tests PASSED for module '%s' (coverage=%.1f%%)",
                module_name,
                result.coverage_percent,
            )
            break

        # ── Retry with error context ─────────────────────────
        retry_count += 1
        if retry_count <= max_retries:
            logger.warning(
                "Tests FAILED for module '%s'. Retrying with error context...",
                module_name,
            )
            # Rebuild from the base prompt each time to avoid unbounded growth
            error_context: str = result.error_message or "Tests failed"
            prompt = (
                f"{base_prompt}\n\n"
                f"=== Previous Attempt Failed ===\n"
                f"The previously generated tests failed with the following error:\n"
                f"{error_context}\n\n"
                f"Please fix the issues and regenerate the test code.\n"
                f"Return ONLY the corrected Python test code."
            )
        else:
            logger.error(
                "Tests FAILED for module '%s' after %d retries.",
                module_name,
                max_retries,
            )

    # ── Report result ────────────────────────────────────────
    if result is None:
        # Should not happen, but guard against it
        result = TestRunResult(
            passed=False,
            coverage_percent=0.0,
            error_message="No test result produced",
            output="",
            generated_file_path="",
        )

    total_attempts: int = retry_count + 1 if not result.passed else retry_count + 1
    agent_log: str = (
        f"Generated tests in {total_attempts} attempt(s). "
        f"{'All tests passed.' if result.passed else 'Tests failed after retries.'}"
    )

    _report_result(
        orchestrator_url=config["orchestrator_url"],
        job_id=job_id,
        module_name=module_name,
        passed=result.passed,
        coverage_percent=result.coverage_percent,
        generated_test_code=test_code,
        agent_log=agent_log,
    )


# ─────────────────────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────────────────────

REDIS_QUEUE_KEY: str = "unitforge:tasks"  # Overridden by config["redis_queue_key"]
BLPOP_TIMEOUT: int = 5


def main() -> None:
    """Entry point — starts the agent worker loop.

    Connects to Redis, initialises the LLM client, and enters
    a continuous loop that polls for tasks and processes them.
    Handles graceful shutdown on Ctrl+C.
    """
    logger.info("=" * 60)
    logger.info("UnitForge Test Agent starting up...")
    logger.info("=" * 60)

    # ── Load configuration ───────────────────────────────────
    config: dict[str, Any] = _load_config()
    logger.info("Config: redis=%s:%d, orchestrator=%s, max_retries=%d",
                config["redis_host"], config["redis_port"],
                config["orchestrator_url"], config["max_retry_attempts"])

    # ── Connect to Redis ─────────────────────────────────────
    try:
        redis_client: Any = _connect_redis(
            host=config["redis_host"],
            port=config["redis_port"],
        )
    except ConnectionError as exc:
        logger.error("Failed to connect to Redis: %s", exc)
        sys.exit(1)

    # ── Initialise LLM client ────────────────────────────────
    try:
        llm_client: LLMClient = LLMClient.from_env()
        logger.info("LLM client ready (provider=%s)", llm_client.provider_name)
    except Exception as exc:
        logger.error("Failed to initialise LLM client: %s", exc)
        sys.exit(1)

    # ── Worker loop ──────────────────────────────────────────
    queue_key: str = config["redis_queue_key"]
    logger.info("Listening for tasks on Redis queue '%s'...", queue_key)

    try:
        while True:
            # BLPOP with timeout — returns (key, value) or None
            result: Optional[tuple[str, str]] = redis_client.blpop(
                queue_key,
                timeout=BLPOP_TIMEOUT,
            )

            if result is None:
                # No task available — loop back and try again
                continue

            _queue_key, task_json = result

            # ── Parse the task JSON ──────────────────────────
            try:
                task: dict[str, Any] = json.loads(task_json)
            except json.JSONDecodeError as exc:
                logger.error("Failed to parse task JSON: %s — raw: %s", exc, task_json[:200])
                continue

            # ── Process the task ─────────────────────────────
            try:
                _process_task(task=task, llm_client=llm_client, config=config)
            except Exception as exc:
                logger.error(
                    "Unhandled error processing task: %s",
                    exc,
                    exc_info=True,
                )
                # Agent must never crash — log and continue
                continue

    except KeyboardInterrupt:
        logger.info("Received Ctrl+C — shutting down gracefully.")
        sys.exit(0)


# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()

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
import threading
from typing import Any, Optional
from urllib.parse import quote

import requests
from dotenv import load_dotenv

from llm_client import LLMClient, LLMResponse
from prompt_builder import build_retry_prompt, build_system_prompt, build_test_prompt
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
# LLM output sanitisation
# ─────────────────────────────────────────────────────────────

def extract_python_code(raw_text: str) -> str:
    """Extract Python code from LLM response.

    LLMs often wrap code in markdown fences like ```python ... ```.
    This function strips those fences and returns clean Python code.

    Args:
        raw_text: The raw LLM response string.

    Returns:
        Clean Python code with markdown fences removed.
    """
    import re

    # Try to extract from ```python ... ``` block
    pattern_with_lang: re.Match[str] | None = re.search(
        r'```python\s*\n(.*?)\n\s*```',
        raw_text,
        re.DOTALL,
    )
    if pattern_with_lang:
        return pattern_with_lang.group(1).strip()

    # Try to extract from ``` ... ``` block (no language specified)
    pattern_plain: re.Match[str] | None = re.search(
        r'```\s*\n(.*?)\n\s*```',
        raw_text,
        re.DOTALL,
    )
    if pattern_plain:
        return pattern_plain.group(1).strip()

    # No markdown fences found — return as-is (already clean code)
    return raw_text.strip()


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
    import ssl as ssl_lib

    redis_ssl = os.getenv("REDIS_SSL", "false").lower() == "true"

    client: Any = redis.Redis(
        host=host,
        port=port,
        password=os.getenv("REDIS_PASSWORD", None) or None,
        ssl=redis_ssl,
        ssl_cert_reqs=ssl_lib.CERT_NONE if redis_ssl else None,
        decode_responses=True,
    )

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


def report_result(
    job_id: str,
    payload: dict,
    orchestrator_url: str
) -> None:
    """POST result to orchestrator. Never raises — agent must not crash."""
    url = f"{orchestrator_url}/api/jobs/{job_id}/results"
    
    headers = {"Content-Type": "application/json"}
    agent_token = os.getenv("AGENT_TOKEN", "")
    if agent_token:
        headers["Authorization"] = f"Bearer {agent_token}"
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30,
        )
        # Log but don't raise — agent must survive any server error
        if response.status_code >= 400:
            logger.warning(
                f"Orchestrator returned {response.status_code} "
                f"for result POST to {url}: {response.text[:200]}"
            )
        else:
            logger.info(
                f"Reported result for '{payload.get('moduleName')}' "
                f"(status={response.status_code})"
            )
    except requests.exceptions.ConnectionError:
        logger.error(
            f"Cannot reach orchestrator at {url}. "
            "Result lost — check ORCHESTRATOR_URL env var."
        )
    except requests.exceptions.Timeout:
        logger.error(f"Timeout posting result to {url}")
    except Exception as e:
        logger.error(f"Unexpected error posting result: {e}")
    # Never re-raise — the agent loop must continue


# ─────────────────────────────────────────────────────────────
# User API key (BYOK — Bring Your Own Key)
# ─────────────────────────────────────────────────────────────

def get_user_api_key(
    owner_email: str,
    orchestrator_url: str,
) -> Optional[str]:
    """Fetch the decrypted Gemini API key for a job owner.

    Returns None if no key is configured for this user.

    Args:
        owner_email: The email of the job owner.
        orchestrator_url: Base URL of the orchestrator service.

    Returns:
        The decrypted API key string, or None.
    """
    if not owner_email or owner_email == "anonymous":
        return None

    # URL-encode the email — @ becomes %40
    encoded_email = quote(owner_email, safe='')

    headers = {}
    agent_token = os.getenv("AGENT_TOKEN", "")
    if agent_token:
        headers["Authorization"] = f"Bearer {agent_token}"

    try:
        response = requests.get(
            f"{orchestrator_url}/api/users/apikey/lookup/{encoded_email}",
            headers=headers,
            timeout=10,
        )
        if response.status_code == 200:
            key = response.json().get("apiKey")
            if key:
                logger.info(
                    f"Retrieved personal API key for {owner_email}"
                )
            return key
        logger.warning(
            f"API key fetch returned {response.status_code} "
            f"for {owner_email}"
        )
        return None
    except Exception as e:
        logger.warning(
            f"Could not fetch API key for {owner_email}: {e}"
        )
        return None


# ─────────────────────────────────────────────────────────────
# Task processing
# ─────────────────────────────────────────────────────────────

def process_task_with_timeout(
    task: dict[str, Any],
    config: dict[str, Any],
    task_llm: LLMClient,
    timeout_seconds: int = 300
) -> None:
    """
    Process a single task with a hard timeout.
    If the task takes longer than timeout_seconds,
    report failure and move on.
    """
    result_container = {"done": False, "error": None}

    def target():
        try:
            _process_task(task, task_llm, config)
            result_container["done"] = True
        except Exception as e:
            result_container["error"] = str(e)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)

    if thread.is_alive():
        # Task timed out
        module_name = task.get("moduleName", "unknown")
        job_id = task.get("jobId", "unknown")
        logger.warning(
            f"Module '{module_name}' timed out after "
            f"{timeout_seconds}s — reporting failure and moving on"
        )
        report_result(
            job_id,
            {
                "moduleName": module_name,
                "passed": False,
                "coveragePercent": 0.0,
                "generatedTestCode": "",
                "agentLog": (
                    f"Module timed out after {timeout_seconds} seconds. "
                    "This module may have complex dependencies or "
                    "generated tests that hang during execution."
                ),
            },
            config["orchestrator_url"],
        )


def _process_task(
    task: dict[str, Any],
    llm_client: LLMClient,
    config: dict[str, Any],
) -> None:
    """Process a single task from the Redis queue.

    Builds the LLM prompt, generates test code, runs the tests,
    retries on failure with error context (feedback loop), and
    reports results to the orchestrator.

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

    # Skip modules with no testable content
    functions = module_info.get("functions", [])
    classes = module_info.get("classes", [])
    endpoints = module_info.get("endpoints", [])

    if not functions and not classes and not endpoints:
        logger.info(
            f"Skipping module '{module_name}' — no functions, "
            f"classes, or endpoints to test"
        )
        # Report as skipped (passed=True, coverage=0, with a note)
        result_payload = {
            "moduleName": module_name,
            "passed": True,
            "coveragePercent": 0.0,
            "generatedTestCode": "# No testable content found in this module",
            "agentLog": "Skipped — module has no functions, classes, or endpoints",
        }
        # POST the skip result to orchestrator
        report_result(job_id, result_payload, config["orchestrator_url"])
        return  # move to next task

    # ── Extract source code for coverage measurement ─────────
    source_code: str = module_info.get("source_code", "")
    system_prompt: str = build_system_prompt()

    # ── Feedback loop: generate → run → retry on failure ─────
    max_attempts: int = config["max_retry_attempts"]
    attempt: int = 1
    test_code: str = ""
    result: Optional[TestRunResult] = None
    last_error: str = ""

    while attempt <= max_attempts:
        # ── Build prompt (initial or retry) ───────────────────
        if attempt == 1:
            prompt: str = build_test_prompt(module_info)
            logger.info("Generating tests for '%s' (attempt %d)", module_name, attempt)
        else:
            prompt = build_retry_prompt(
                module_info=module_info,
                previous_test_code=test_code,
                error_message=last_error,
            )
            logger.warning(
                "Tests failed for '%s', retrying (attempt %d/%d)",
                module_name,
                attempt,
                max_attempts,
            )

        # ── Generate test code via LLM ───────────────────────
        try:
            llm_response: LLMResponse = llm_client.generate(
                prompt=prompt,
                system=system_prompt,
            )
            test_code = extract_python_code(llm_response.content)
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
            result = run_tests(
                test_code=test_code,
                module_name=module_name,
                source_code=source_code,
                timeout=60,
            )
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
                "Tests PASSED for '%s' on attempt %d (coverage=%.1f%%)",
                module_name,
                attempt,
                result.coverage_percent,
            )
            break
        else:
            last_error = result.error_message or result.output
            logger.warning(
                "Tests FAILED for '%s' on attempt %d: %s",
                module_name,
                attempt,
                last_error[:200],
            )
            attempt += 1

    # ── Report result (pass or fail after all retries) ───────
    if result is None:
        # Should not happen, but guard against it
        result = TestRunResult(
            passed=False,
            coverage_percent=0.0,
            error_message="No test result produced",
            output="",
            generated_file_path="",
        )

    agent_log: str = (
        f"Generated tests in {attempt} attempt(s). "
        f"{'All tests passed.' if result.passed else 'Tests failed after all retries.'}"
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
    
    redis_ssl = os.getenv("REDIS_SSL", "false").lower() == "true"
    mode = "CLOUD" if redis_ssl else "LOCAL"
    
    logger.info(f"Running in {mode} mode")
    logger.info(f"Redis: {config['redis_host']}:{config['redis_port']} (SSL: {redis_ssl})")
    logger.info(f"Orchestrator: {config['orchestrator_url']}")
    logger.info(f"LLM provider: {os.getenv('LLM_PROVIDER', 'stub')}")

    # Start HTTP health server for Render Web Service free tier
    from health_server import start_in_background, agent_status
    start_in_background()
    logger.info("Health server started on port " + os.getenv("PORT", "8002"))

    # ── Connect to Redis ─────────────────────────────────────
    try:
        redis_client: Any = _connect_redis(
            host=config["redis_host"],
            port=config["redis_port"],
        )
        agent_status["redis_connected"] = True
        agent_status["status"] = "listening"
    except ConnectionError as exc:
        logger.error("Failed to connect to Redis: %s", exc)
        sys.exit(1)

    # ── Initialise LLM client ────────────────────────────────
    llm_client: Optional[LLMClient] = None
    try:
        llm_client = LLMClient.from_env()
        logger.info("Global LLM client ready (provider=%s)", llm_client.provider_name)
        agent_status["provider"] = llm_client.provider_name
    except Exception as exc:
        logger.info(
            "No global LLM client configured (%s). "
            "Agent will rely on per-task BYOK keys.",
            exc,
        )
        agent_status["provider"] = os.getenv("LLM_PROVIDER", "unknown")

    # ── Worker loop ──────────────────────────────────────────
    queue_key: str = config["redis_queue_key"]
    logger.info("Listening for tasks on Redis queue '%s'...", queue_key)

    while True:
        try:
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

            # ── BYOK: use owner's personal API key if available ──
            owner_email = task.get("ownerEmail", "") or ""
            
            # Only try to get user key if we have a real email
            # Skip "anonymous" and empty strings
            if owner_email and owner_email != "anonymous":
                user_api_key: Optional[str] = get_user_api_key(
                    owner_email, config["orchestrator_url"]
                )
                if user_api_key:
                    logger.info(f"Using personal API key for {owner_email}")
                    try:
                        llm = LLMClient.from_env(api_key=user_api_key)
                    except Exception as exc:
                        logger.error("Failed to initialize user LLM client: %s", exc)
                        llm = None
                else:
                    logger.info(
                        f"No personal key for {owner_email} "
                        "— using default LLM client"
                    )
                    llm = llm_client
            else:
                logger.info("Anonymous job — using default LLM client")
                llm = llm_client

            if not llm:
                logger.warning(
                    f"No API key available for user {owner_email}. "
                    "User must add their Gemini key in Settings."
                )
                module_name: str = task.get("moduleName", "unknown")
                job_id: str = task.get("jobId", "unknown")
                report_result(job_id, {
                    "moduleName": module_name,
                    "passed": False,
                    "coveragePercent": 0.0,
                    "generatedTestCode": "",
                    "agentLog": (
                        "No Gemini API key configured. "
                        "Please add your Gemini API key in Settings → "
                        "https://aistudio.google.com to get a free key."
                    ),
                }, config["orchestrator_url"])
                continue

            # ── Process the task ─────────────────────────────
            try:
                module_timeout = int(os.getenv("MODULE_TIMEOUT_SECONDS", "300"))
                process_task_with_timeout(
                    task, config, llm, module_timeout
                )
                agent_status["tasks_processed"] += 1
            except Exception as exc:
                logger.error(
                    f"Unhandled error processing task "
                    f"{task.get('moduleName', 'unknown')}: {exc}",
                    exc_info=True
                )
                # Try to report failure so job does not stall
                try:
                    report_result(
                        task.get("jobId", "unknown"),
                        {
                            "moduleName": task.get("moduleName", "unknown"),
                            "passed": False,
                            "coveragePercent": 0.0,
                            "generatedTestCode": "",
                            "agentLog": f"Agent error: {str(exc)[:500]}",
                        },
                        config["orchestrator_url"],
                    )
                except Exception:
                    pass  # Already safe — report_result never raises

        except KeyboardInterrupt:
            logger.info("Agent shutting down")
            break
        except Exception as e:
            logger.error(f"Outer loop error: {e} — continuing")
            continue  # Never stop — always keep polling


# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()

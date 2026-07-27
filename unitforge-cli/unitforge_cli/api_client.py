"""HTTP client for communicating with the UnitForge orchestrator."""

import requests
import json
import time
import subprocess
import sys
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class JobResult:
    """Final result of a UnitForge job."""
    job_id: str
    status: str
    results: list
    total_modules: int
    passed_modules: int
    failed_modules: int
    average_coverage: float


def run_analysis_engine(input_path: str, input_type: str) -> dict:
    """
    Run the analysis engine on the given input and return module_map dict.

    Finds the analysis-engine directory relative to this file's location.
    Runs: python main.py --input <path> --type <type>
    Returns the parsed JSON as a Python dict.

    Raises:
        RuntimeError if analysis engine fails or returns invalid JSON
    """
    # Find analysis-engine relative to unitforge-cli
    cli_dir = Path(__file__).parent.parent
    engine_dir = cli_dir.parent / "analysis-engine"

    if not engine_dir.exists():
        raise RuntimeError(
            f"Analysis engine not found at {engine_dir}. "
            "Make sure you are running from inside the UnitForge project."
        )

    main_py = engine_dir / "main.py"

    result = subprocess.run(
        [sys.executable, str(main_py), "--input", input_path, "--type", input_type],
        capture_output=True,
        text=True,
        cwd=str(engine_dir),
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Analysis engine failed:\n{result.stderr}"
        )

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Analysis engine returned invalid JSON: {e}\n"
            f"Output was: {result.stdout[:500]}"
        )


def submit_job(
    module_map: dict,
    input_type: str,
    input_path: str,
    orchestrator_url: str = "http://localhost:8080",
) -> str:
    """
    Submit a job to the orchestrator.

    Returns the job ID as a string.
    Raises requests.HTTPError on failure.
    """
    payload = {
        "inputType": input_type,
        "inputPath": input_path,
        "moduleMap": module_map,
    }

    response = requests.post(
        f"{orchestrator_url}/api/jobs",
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["jobId"]


def poll_job_until_done(
    job_id: str,
    orchestrator_url: str = "http://localhost:8080",
    poll_interval: int = 5,
    timeout: int = 600,
) -> JobResult:
    """
    Poll the orchestrator every poll_interval seconds until job is DONE or FAILED.

    Args:
        job_id: The UUID of the job to poll
        orchestrator_url: Base URL of the orchestrator
        poll_interval: Seconds between polls (default 5)
        timeout: Maximum seconds to wait (default 600 = 10 minutes)

    Returns:
        JobResult with full details of the completed job

    Raises:
        TimeoutError if job does not complete within timeout seconds
    """
    elapsed = 0

    while elapsed < timeout:
        job_response = requests.get(
            f"{orchestrator_url}/api/jobs/{job_id}",
            timeout=10,
        )
        job_response.raise_for_status()
        job = job_response.json()

        status = job.get("status", "UNKNOWN")

        if status in ("DONE", "FAILED"):
            # Get results
            results_response = requests.get(
                f"{orchestrator_url}/api/jobs/{job_id}/results",
                timeout=10,
            )
            results_response.raise_for_status()
            results = results_response.json()

            passed = sum(1 for r in results if r.get("passed", False))
            failed = len(results) - passed

            coverages = [
                r.get("coveragePercent", 0.0)
                for r in results
                if r.get("coveragePercent", 0.0) > 0
            ]
            avg_coverage = sum(coverages) / len(coverages) if coverages else 0.0

            return JobResult(
                job_id=job_id,
                status=status,
                results=results,
                total_modules=job.get("totalModules", 0),
                passed_modules=passed,
                failed_modules=failed,
                average_coverage=avg_coverage,
            )

        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(
        f"Job {job_id} did not complete within {timeout} seconds. "
        "Check that the test agent is running: python agent.py"
    )


def download_tests(
    job_id: str,
    output_path: str,
    orchestrator_url: str = "http://localhost:8080",
) -> None:
    """
    Download generated tests as a zip file.

    Args:
        job_id: The job ID to download tests for
        output_path: Local file path to save the zip
        orchestrator_url: Base URL of the orchestrator
    """
    response = requests.get(
        f"{orchestrator_url}/api/jobs/{job_id}/download",
        timeout=30,
        stream=True,
    )
    response.raise_for_status()

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

"""
UnitForge — Test Runner
========================
Takes generated test code (a Python string), writes it to a temporary file,
runs pytest via subprocess, and returns structured results.

Phase 3: runs in the current Python environment with real coverage
measurement via pytest-cov. When source_code is provided, the module
under test is written alongside the test file so --cov can measure it.

Usage:
    from test_runner import run_tests, TestRunResult

    result = run_tests(
        test_code="from calculator import add\\ndef test_add(): ...",
        module_name="calculator",
        source_code="def add(a, b): return a + b",
    )
    print(result.passed, result.coverage_percent)
"""

import logging
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Optional

logger: logging.Logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Result dataclass
# ─────────────────────────────────────────────────────────────

@dataclass
class TestRunResult:
    """Structured result from running a generated test file.

    Attributes:
        passed: Whether all tests passed.
        coverage_percent: Code coverage percentage (0.0 if not measured).
        error_message: Error details if the run failed, None otherwise.
        output: Full stdout + stderr from the test run.
        generated_file_path: Path to the temporary test file that was executed.
    """

    passed: bool
    coverage_percent: float
    error_message: Optional[str]
    output: str
    generated_file_path: str


# ─────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────

def _validate_syntax(test_code: str) -> Optional[str]:
    """Check the test code for Python syntax errors.

    Args:
        test_code: The generated Python test code string.

    Returns:
        An error message string if a syntax error is found, None otherwise.
    """
    try:
        compile(test_code, "<generated_test>", "exec")
        return None
    except SyntaxError as exc:
        return f"Syntax error at line {exc.lineno}: {exc.msg}"


def _parse_pytest_passed(output: str, returncode: int | None = None) -> bool:
    """Determine whether pytest reported all tests as passed.

    Uses the subprocess return code as the primary signal (0 = all passed).
    Falls back to text parsing if return code is unavailable.

    Args:
        output: Combined stdout/stderr from the pytest run.
        returncode: The subprocess exit code (0 means success).

    Returns:
        True if all tests passed.
    """
    # Primary signal: pytest exit code 0 means all tests passed
    if returncode is not None:
        return returncode == 0

    # Fallback: text-based parsing
    if re.search(r'\d+ failed', output.lower()):
        return False
    if re.search(r'\d+ passed', output.lower()):
        return True
    return False


def _parse_coverage_percent(output: str, module_name: str) -> float:
    """Extract the coverage percentage from pytest-cov output.

    pytest-cov prints a table like::

        Name              Stmts   Miss  Cover
        -------------------------------------
        calculator           10      2    80%

    Args:
        output: Combined stdout/stderr from the test run.
        module_name: The module name to look for in the coverage table.

    Returns:
        The coverage percentage as a float, or 0.0 if not found.
    """
    for line in output.split("\n"):
        if module_name in line and "%" in line:
            parts: list[str] = line.split()
            for part in reversed(parts):
                if "%" in part:
                    coverage_str: str = part.replace("%", "")
                    try:
                        return float(coverage_str)
                    except ValueError:
                        continue

    # Fallback: TOTAL line pattern
    match: Optional[re.Match[str]] = re.search(
        r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output
    )
    if match:
        return float(match.group(1))

    return 0.0


def _extract_failure_summary(output: str) -> str:
    """Extract a concise failure summary from pytest output.

    Args:
        output: Combined stdout/stderr from the pytest run.

    Returns:
        A string summarising the failures.
    """
    lines: list[str] = output.splitlines()
    failure_lines: list[str] = []
    capture: bool = False

    for line in lines:
        if "FAILED" in line or "ERROR" in line:
            failure_lines.append(line.strip())
        if "short test summary" in line.lower():
            capture = True
            continue
        if capture and line.strip():
            failure_lines.append(line.strip())
        if capture and not line.strip():
            capture = False

    if failure_lines:
        return "\n".join(failure_lines[:10])  # Cap at 10 lines
    return "Tests failed — see full output for details."


def _cleanup_temp_dir(temp_dir: str) -> None:
    """Remove temporary test directory and its contents.

    Args:
        temp_dir: Path to the temporary directory to remove.
    """
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.debug("Cleaned up temp directory: %s", temp_dir)
    except Exception as exc:
        logger.warning("Failed to clean up temp directory %s: %s", temp_dir, exc)


# ─────────────────────────────────────────────────────────────
# Main public function
# ─────────────────────────────────────────────────────────────

def run_tests(
    test_code: str,
    module_name: str,
    source_code: str = "",
    timeout: int = 60,
) -> TestRunResult:
    """Run generated test code and return results.

    Writes the test code to a temporary file, invokes pytest via
    subprocess, captures output, and parses pass/fail status.
    When ``source_code`` is provided, also writes the module source
    and runs pytest-cov for real coverage measurement.

    Args:
        test_code: The generated Python test code as a string.
        module_name: Name of the module under test (used for file naming).
        source_code: The source code of the module under test. When
            provided, enables real coverage measurement via pytest-cov.
        timeout: Maximum seconds to allow the test run (default: 60).

    Returns:
        A TestRunResult with pass/fail status, coverage, and output.
    """
    # ── Pre-flight: syntax check ─────────────────────────────
    syntax_error: Optional[str] = _validate_syntax(test_code)
    if syntax_error:
        logger.error("Generated test code has syntax errors: %s", syntax_error)
        return TestRunResult(
            passed=False,
            coverage_percent=0.0,
            error_message=syntax_error,
            output=f"Syntax validation failed: {syntax_error}",
            generated_file_path="",
        )

    # ── Create temp directory and write files ─────────────────
    temp_dir: str = tempfile.mkdtemp(prefix="unitforge_")
    test_file_name: str = f"test_{module_name}.py"
    test_file_path: str = os.path.join(temp_dir, test_file_name)
    has_source: bool = bool(source_code.strip())

    try:
        # Write test file
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(test_code)
        logger.info("Wrote generated tests to %s", test_file_path)

        # Write source module (enables real coverage measurement)
        if has_source:
            source_file_path: str = os.path.join(temp_dir, f"{module_name}.py")
            with open(source_file_path, "w", encoding="utf-8") as f:
                f.write(source_code)
            logger.info("Wrote source module to %s", source_file_path)

    except OSError as exc:
        logger.error("Failed to write files: %s", exc)
        _cleanup_temp_dir(temp_dir)
        return TestRunResult(
            passed=False,
            coverage_percent=0.0,
            error_message=f"Failed to write files: {exc}",
            output="",
            generated_file_path="",
        )

    # ── Build pytest command ─────────────────────────────────
    cmd: list[str] = [
        "python", "-m", "pytest",
        test_file_path,
        "-v",
        "--tb=short",
        "--no-header",
    ]

    if has_source:
        cmd.extend([
            f"--cov={module_name}",
            "--cov-report=term-missing",
        ])

    # ── Run pytest via subprocess ────────────────────────────
    stdout: str = ""
    stderr: str = ""
    combined_output: str = ""
    run_result: Optional[TestRunResult] = None

    try:
        logger.info("Running: %s (timeout=%ds)", " ".join(cmd), timeout)
        result: subprocess.CompletedProcess[str] = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=temp_dir,
        )
        stdout = result.stdout
        stderr = result.stderr
        combined_output = f"{stdout}\n{stderr}".strip()

        passed: bool = _parse_pytest_passed(combined_output, returncode=result.returncode)
        coverage: float = (
            _parse_coverage_percent(combined_output, module_name)
            if has_source
            else 0.0
        )

        error_msg: Optional[str] = None
        if not passed:
            error_msg = _extract_failure_summary(combined_output)

        logger.info(
            "Test run complete — passed=%s, coverage=%.1f%%",
            passed,
            coverage,
        )

        run_result = TestRunResult(
            passed=passed,
            coverage_percent=coverage,
            error_message=error_msg,
            output=combined_output,
            generated_file_path="",
        )

    except subprocess.TimeoutExpired:
        error_msg_timeout: str = f"Test execution timed out after {timeout} seconds"
        logger.error(error_msg_timeout)
        run_result = TestRunResult(
            passed=False,
            coverage_percent=0.0,
            error_message=error_msg_timeout,
            output=error_msg_timeout,
            generated_file_path="",
        )

    except Exception as exc:
        error_msg_exc: str = f"Unexpected error running tests: {exc}"
        logger.error(error_msg_exc, exc_info=True)
        run_result = TestRunResult(
            passed=False,
            coverage_percent=0.0,
            error_message=error_msg_exc,
            output=f"{combined_output}\n{error_msg_exc}".strip(),
            generated_file_path="",
        )

    finally:
        # ── Cleanup temp files ───────────────────────────────
        _cleanup_temp_dir(temp_dir)

    return run_result

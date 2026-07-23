"""
Tests for prompt_builder module.
=================================
Verifies that build_test_prompt and build_system_prompt produce
correct, well-structured prompts for both Python and OpenAPI modules.
"""

import pytest

from prompt_builder import build_test_prompt, build_system_prompt, build_retry_prompt


# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────

PYTHON_MODULE_INFO: dict = {
    "type": "python",
    "name": "calculator",
    "file_path": "src/calculator.py",
    "functions": [
        {
            "name": "add",
            "args": [
                {"name": "a", "type": "int"},
                {"name": "b", "type": "int"},
            ],
            "return_type": "int",
            "docstring": "Return the sum of two integers.",
        },
        {
            "name": "divide",
            "args": [
                {"name": "numerator", "type": "float"},
                {"name": "denominator", "type": "float"},
            ],
            "return_type": "float",
            "docstring": "Divide numerator by denominator.",
        },
    ],
    "classes": [],
}

OPENAPI_MODULE_INFO: dict = {
    "type": "openapi",
    "name": "user_api",
    "endpoints": [
        {
            "path": "/api/users",
            "method": "GET",
            "summary": "List all users",
            "parameters": [
                {"name": "page", "type": "integer", "required": False},
            ],
        },
        {
            "path": "/api/users/{id}",
            "method": "GET",
            "summary": "Get user by ID",
            "parameters": [
                {"name": "id", "type": "string", "required": True},
            ],
        },
    ],
}

EMPTY_MODULE_INFO: dict = {
    "type": "python",
    "name": "empty_module",
    "file_path": "src/empty.py",
    "functions": [],
    "classes": [],
}

# Args as list[str] — matches analysis engine's FunctionInfo.args shape
PYTHON_MODULE_INFO_STR_ARGS: dict = {
    "type": "python",
    "name": "math_utils",
    "file_path": "src/math_utils.py",
    "functions": [
        {
            "name": "multiply",
            "args": ["x", "y"],
            "return_type": "float",
            "docstring": "Multiply two numbers.",
        },
    ],
    "classes": [],
}


# ─────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────

def test_prompt_contains_function_name() -> None:
    """Verify that function names appear in the generated prompt."""
    prompt: str = build_test_prompt(PYTHON_MODULE_INFO)
    assert "add" in prompt, "Function name 'add' not found in prompt"
    assert "divide" in prompt, "Function name 'divide' not found in prompt"


def test_prompt_contains_argument_names() -> None:
    """Verify that argument names appear in the generated prompt."""
    prompt: str = build_test_prompt(PYTHON_MODULE_INFO)
    assert "a" in prompt, "Argument 'a' not found in prompt"
    assert "b" in prompt, "Argument 'b' not found in prompt"
    assert "numerator" in prompt, "Argument 'numerator' not found in prompt"
    assert "denominator" in prompt, "Argument 'denominator' not found in prompt"


def test_prompt_contains_docstring() -> None:
    """Verify that docstrings appear in the prompt when present."""
    prompt: str = build_test_prompt(PYTHON_MODULE_INFO)
    assert "Return the sum of two integers." in prompt, (
        "Docstring for 'add' not found in prompt"
    )
    assert "Divide numerator by denominator." in prompt, (
        "Docstring for 'divide' not found in prompt"
    )


def test_prompt_for_openapi_contains_endpoint() -> None:
    """Verify that endpoint paths appear in the OpenAPI prompt."""
    prompt: str = build_test_prompt(OPENAPI_MODULE_INFO)
    assert "/api/users" in prompt, "Endpoint path '/api/users' not found in prompt"
    assert "/api/users/{id}" in prompt, (
        "Endpoint path '/api/users/{id}' not found in prompt"
    )
    assert "GET" in prompt, "HTTP method 'GET' not found in prompt"
    assert "List all users" in prompt, "Endpoint summary not found in prompt"


def test_prompt_for_empty_module() -> None:
    """Verify that an empty module (no functions) is handled gracefully."""
    prompt: str = build_test_prompt(EMPTY_MODULE_INFO)
    # Should still produce a prompt without errors
    assert isinstance(prompt, str), "Prompt should be a string"
    assert len(prompt) > 0, "Prompt should not be empty even for empty modules"
    assert "empty_module" in prompt, "Module name should appear in prompt"


def test_system_prompt_not_empty() -> None:
    """Verify that system prompt returns a non-empty string."""
    system: str = build_system_prompt()
    assert isinstance(system, str), "System prompt should be a string"
    assert len(system) > 0, "System prompt should not be empty"
    assert "test" in system.lower(), (
        "System prompt should mention testing"
    )


def test_prompt_handles_string_args() -> None:
    """Verify that args as plain strings (analysis engine format) are handled."""
    prompt: str = build_test_prompt(PYTHON_MODULE_INFO_STR_ARGS)
    assert "multiply" in prompt, "Function name 'multiply' not found in prompt"
    assert "x" in prompt, "Argument 'x' not found in prompt"
    assert "y" in prompt, "Argument 'y' not found in prompt"


def test_retry_prompt_contains_error_message() -> None:
    """Verify that the error message appears in the retry prompt."""
    error_msg: str = "ImportError: No module named 'calculator'"
    prompt: str = build_retry_prompt(
        module_info=PYTHON_MODULE_INFO,
        previous_test_code="def test_add(): assert add(1, 2) == 3",
        error_message=error_msg,
    )
    assert error_msg in prompt, "Error message not found in retry prompt"
    assert "previous attempt" in prompt.lower(), (
        "Retry prompt should mention the previous attempt"
    )


def test_retry_prompt_contains_previous_code() -> None:
    """Verify that the previous test code appears in the retry prompt."""
    previous_code: str = "def test_add():\n    assert add(1, 2) == 3"
    prompt: str = build_retry_prompt(
        module_info=PYTHON_MODULE_INFO,
        previous_test_code=previous_code,
        error_message="AssertionError: assert 4 == 3",
    )
    assert previous_code in prompt, "Previous test code not found in retry prompt"
    assert "calculator" in prompt, (
        "Original module context should still be present in retry prompt"
    )

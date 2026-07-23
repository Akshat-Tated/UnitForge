"""
UnitForge — Prompt Builder
============================
Builds structured LLM prompts from module information.

Takes a module info dictionary (parsed from the Redis task JSON)
and returns a well-structured string prompt that asks the LLM
to generate pytest-compatible test code.

Handles two module types:
  - "python"  → functions and classes
  - "openapi" → REST API endpoints

Usage:
    from prompt_builder import build_test_prompt, build_system_prompt

    prompt = build_test_prompt(module_info, module_code="def add(a, b): ...")
    system = build_system_prompt()
"""

import logging
from typing import Any

logger: logging.Logger = logging.getLogger(__name__)


def build_system_prompt() -> str:
    """Return the system prompt used for all test generation.

    This prompt instructs the LLM to act as an expert Python test engineer
    who produces high-quality, runnable pytest test code.
    """
    return (
        "You are an expert Python test engineer with deep experience in pytest, "
        "test-driven development, and software quality assurance.\n\n"
        "Your job is to generate comprehensive, production-quality pytest test code.\n\n"
        "Rules you MUST follow:\n"
        "1. Write ONLY valid Python code — no markdown, no explanations, no code fences.\n"
        "2. Include all necessary imports at the top of the file.\n"
        "3. Use descriptive test function names that explain what is being tested, e.g. "
        "test_add_returns_sum_of_two_positives.\n"
        "4. Cover normal cases, edge cases (empty input, None, zero, negative numbers, "
        "boundary values), and error cases (invalid types, missing arguments).\n"
        "5. Use pytest.raises for expected exceptions.\n"
        "6. Each test function should test exactly one behaviour.\n"
        "7. Do NOT use unittest — use pytest only.\n"
        "8. Return ONLY the raw Python test code. No prose before or after."
    )


def _build_python_prompt(module_info: dict[str, Any], module_code: str) -> str:
    """Build a prompt for generating tests for a Python module.

    Args:
        module_info: Dictionary describing the module (name, file_path,
                     functions, classes).
        module_code: The raw source code of the module under test.

    Returns:
        A formatted prompt string ready to send to an LLM.
    """
    lines: list[str] = []

    module_name: str = module_info.get("name", "unknown_module")
    file_path: str = module_info.get("file_path", "unknown_path")

    lines.append(f"Generate comprehensive pytest tests for the Python module '{module_name}'.")
    lines.append(f"File path: {file_path}")
    lines.append("")

    # ── Functions ────────────────────────────────────────────
    functions: list[dict[str, Any]] = module_info.get("functions", [])
    if functions:
        lines.append("=== Functions ===")
        for func in functions:
            func_name: str = func.get("name", "unknown")
            args: list[Any] = func.get("args", [])
            return_type: str = func.get("return_type", "Any")
            docstring: str = func.get("docstring", "")

            arg_parts: list[str] = []
            for arg in args:
                if isinstance(arg, str):
                    # Analysis engine FunctionInfo.args is list[str]
                    arg_parts.append(arg)
                else:
                    # Enriched format: list[dict] with name/type keys
                    arg_name: str = arg.get("name", "arg")
                    arg_type: str = arg.get("type", "Any")
                    arg_parts.append(f"{arg_name}: {arg_type}")
            arg_str: str = ", ".join(arg_parts)

            lines.append(f"\nFunction: {func_name}({arg_str}) -> {return_type}")
            if docstring:
                lines.append(f"  Docstring: {docstring}")

        lines.append("")

    # ── Classes ──────────────────────────────────────────────
    classes: list[dict[str, Any]] = module_info.get("classes", [])
    if classes:
        lines.append("=== Classes ===")
        for cls in classes:
            cls_name: str = cls.get("name", "UnknownClass")
            lines.append(f"\nClass: {cls_name}")
            methods: list[dict[str, Any]] = cls.get("methods", [])
            for method in methods:
                method_name: str = method.get("name", "unknown")
                m_args: list[Any] = method.get("args", [])
                m_return: str = method.get("return_type", "Any")
                m_doc: str = method.get("docstring", "")

                m_arg_parts: list[str] = []
                for arg in m_args:
                    if isinstance(arg, str):
                        m_arg_parts.append(arg)
                    else:
                        m_arg_parts.append(
                            f"{arg.get('name', 'arg')}: {arg.get('type', 'Any')}"
                        )
                m_arg_str: str = ", ".join(m_arg_parts)

                lines.append(f"  Method: {method_name}({m_arg_str}) -> {m_return}")
                if m_doc:
                    lines.append(f"    Docstring: {m_doc}")

        lines.append("")

    # ── Source code (if provided) ────────────────────────────
    if module_code:
        lines.append("=== Source Code ===")
        lines.append(module_code)
        lines.append("")

    # ── Instructions ─────────────────────────────────────────
    lines.append("=== Instructions ===")
    lines.append("1. Generate pytest test functions for every function and method listed above.")
    lines.append("2. Include all necessary imports at the top of the test file.")
    lines.append(
        "3. Test edge cases: empty input, None values, invalid input types, "
        "boundary values, zero, negative numbers."
    )
    lines.append(
        "4. Use descriptive test function names like "
        "test_add_returns_sum_of_two_positives."
    )
    lines.append("5. Use pytest.raises for expected exceptions.")
    lines.append(
        "6. Return ONLY the Python test code — no explanation, "
        "no markdown code blocks, just the raw Python."
    )

    return "\n".join(lines)


def _build_openapi_prompt(module_info: dict[str, Any], module_code: str) -> str:
    """Build a prompt for generating tests for an OpenAPI spec module.

    Args:
        module_info: Dictionary describing the module with endpoint information.
        module_code: The raw OpenAPI spec source (YAML/JSON), if available.

    Returns:
        A formatted prompt string ready to send to an LLM.
    """
    lines: list[str] = []

    module_name: str = module_info.get("name", "unknown_api")
    lines.append(f"Generate comprehensive pytest tests for the API '{module_name}'.")
    lines.append("")

    # ── Endpoints ────────────────────────────────────────────
    endpoints: list[dict[str, Any]] = module_info.get("endpoints", [])
    if endpoints:
        lines.append("=== Endpoints ===")
        for ep in endpoints:
            path: str = ep.get("path", "/unknown")
            method: str = ep.get("method", "GET").upper()
            summary: str = ep.get("summary", "")
            parameters: list[dict[str, Any]] = ep.get("parameters", [])

            lines.append(f"\nEndpoint: {method} {path}")
            if summary:
                lines.append(f"  Summary: {summary}")
            if parameters:
                lines.append("  Parameters:")
                for param in parameters:
                    p_name: str = param.get("name", "param")
                    p_type: str = param.get("type", "string")
                    p_required: bool = param.get("required", False)
                    req_label: str = "required" if p_required else "optional"
                    lines.append(f"    - {p_name}: {p_type} ({req_label})")

        lines.append("")

    # ── Source spec (if provided) ────────────────────────────
    if module_code:
        lines.append("=== API Spec ===")
        lines.append(module_code)
        lines.append("")

    # ── Instructions ─────────────────────────────────────────
    lines.append("=== Instructions ===")
    lines.append("1. Generate pytest tests using the `requests` library.")
    lines.append("2. Test success responses (200, 201) with valid parameters.")
    lines.append("3. Test error responses (400, 404, 422) with invalid or missing parameters.")
    lines.append("4. Test missing required parameters.")
    lines.append("5. Use descriptive test function names.")
    lines.append("6. Include the base URL as a fixture or constant at the top.")
    lines.append(
        "7. Return ONLY the Python test code — no explanation, "
        "no markdown code blocks, just the raw Python."
    )

    return "\n".join(lines)


def build_test_prompt(module_info: dict[str, Any], module_code: str = "") -> str:
    """Build an LLM prompt for generating pytest tests for a module.

    Dispatches to the appropriate builder based on the module type
    (``"python"`` or ``"openapi"``).

    Args:
        module_info: A dictionary describing the module under test.
            Expected keys vary by type:
              - ``"type"``: ``"python"`` or ``"openapi"`` (default: ``"python"``)
              - ``"name"``: Module name
              - ``"file_path"``: Path to the source file
              - ``"functions"``: List of function descriptors (python type)
              - ``"classes"``: List of class descriptors (python type)
              - ``"endpoints"``: List of endpoint descriptors (openapi type)
        module_code: Optional raw source code to include in the prompt
            for additional context.

    Returns:
        A fully formatted prompt string ready to be sent to an LLM.
    """
    module_type: str = module_info.get("type", "python")

    if module_type == "openapi":
        logger.info("Building OpenAPI test prompt for '%s'", module_info.get("name", "?"))
        return _build_openapi_prompt(module_info, module_code)

    # Default to python
    logger.info("Building Python test prompt for '%s'", module_info.get("name", "?"))
    return _build_python_prompt(module_info, module_code)


def build_retry_prompt(
    module_info: dict[str, Any],
    previous_test_code: str,
    error_message: str,
) -> str:
    """Build a retry prompt that includes the previous failed test and error.

    Used by the feedback loop in agent.py when generated tests fail.
    Provides the LLM with the original module context, the code it
    previously generated, and the error so it can produce a corrected
    version.

    Args:
        module_info: The module info dictionary (same as build_test_prompt).
        previous_test_code: The test code from the previous attempt that failed.
        error_message: The error message or pytest output from the failure.

    Returns:
        A formatted retry prompt string ready to be sent to an LLM.
    """
    original_prompt: str = build_test_prompt(module_info)

    retry_prompt: str = (
        f"{original_prompt}\n\n"
        f"IMPORTANT: Your previous attempt to write tests for this module failed.\n"
        f"Here is the test code you generated:\n\n"
        f"```python\n"
        f"{previous_test_code}\n"
        f"```\n\n"
        f"It failed with this error:\n"
        f"{error_message}\n\n"
        f"Please fix the test code to resolve this error.\n"
        f"Common issues to check:\n"
        f"- Missing imports at the top of the file\n"
        f"- Incorrect function names or argument counts\n"
        f"- Wrong expected values in assertions\n"
        f"- Missing module that needs to be imported\n\n"
        f"Write the complete corrected test file from scratch.\n"
        f"Return ONLY the Python code, no explanation."
    )

    logger.info("Building retry prompt for '%s'", module_info.get("name", "?"))
    return retry_prompt

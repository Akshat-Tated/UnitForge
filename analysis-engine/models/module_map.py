"""Module map dataclasses for the UnitForge analysis engine.

These dataclasses represent the structured output of code and spec parsers.
The orchestrator consumes the serialised ModuleMap (module_map.json) to
dispatch parallel test-generation agents — one per module.

All models are plain stdlib dataclasses with type hints.  No Pydantic, no ORM.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Literal


@dataclass
class FunctionInfo:
    """A single function extracted from a source file.

    Attributes:
        name: Function name (e.g. ``calculate_total``).
        args: Ordered list of parameter names.
        return_type: Return-type annotation as a string, or ``None``
            if the function has no annotation.
        docstring: First expression-statement string (the docstring),
            or ``None`` if absent.
        line_no: 1-based line number where the ``def`` statement starts.
    """

    name: str
    args: list[str]
    return_type: str | None
    docstring: str | None
    line_no: int


@dataclass
class ClassInfo:
    """A class extracted from a source file.

    Attributes:
        name: Class name (e.g. ``UserService``).
        methods: List of methods defined directly in the class body.
    """

    name: str
    methods: list[FunctionInfo]


@dataclass
class EndpointInfo:
    """A single REST endpoint extracted from an OpenAPI spec.

    Attributes:
        path: URL path (e.g. ``/api/users/{id}``).
        method: HTTP method in uppercase (``GET``, ``POST``, etc.).
        summary: Human-readable summary from the spec, or ``None``.
        parameters: List of parameter dicts, each containing at least
            ``name``, ``in``, ``type``, and ``required``.
        request_body: Schema dict for the request body, or ``None``
            if the endpoint has no request body.
        response_schema: Schema dict for the primary success response
            (200 or 201), or ``None`` if not defined.
    """

    path: str
    method: str
    summary: str | None
    parameters: list[dict[str, Any]]
    request_body: dict[str, Any] | None
    response_schema: dict[str, Any] | None


@dataclass
class ModuleInfo:
    """Parsed representation of a single source module or spec file.

    Attributes:
        name: Human-readable module name (e.g. ``utils`` or ``pet-store``).
        file_path: Path to the source file, relative to the input root.
        type: Source type — ``"python"``, ``"java"``, or ``"openapi"``.
        functions: Top-level functions (empty for OpenAPI modules).
        classes: Classes defined in the module (empty for OpenAPI modules).
        imports: List of import strings (e.g. ``["os", "json"]``).
        endpoints: Endpoints extracted from an OpenAPI spec
            (empty for language modules).
    """

    name: str
    file_path: str
    type: Literal["python", "java", "openapi"]
    functions: list[FunctionInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    endpoints: list[EndpointInfo] = field(default_factory=list)


@dataclass
class ModuleMap:
    """Top-level container holding every parsed module.

    This is the object serialised to ``module_map.json`` and handed off
    to the orchestrator.

    Attributes:
        modules: All parsed modules in the analysis run.
    """

    modules: list[ModuleInfo] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Serialise the module map to a formatted JSON string.

        Args:
            indent: Number of spaces for JSON indentation.  Defaults to 2.

        Returns:
            A JSON string representing the full module map.
        """
        return json.dumps(self.to_dict(), indent=indent)

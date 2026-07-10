"""OpenAPI 3.x specification parser for the UnitForge analysis engine.

Loads an OpenAPI spec (YAML or JSON) and extracts every path + method
combination as an :class:`EndpointInfo`.  The resulting list is wrapped
in a :class:`ModuleInfo` with ``type="openapi"`` for inclusion in the
module map.

Usage::

    from parsers.openapi_parser import parse_openapi_spec

    module = parse_openapi_spec("petstore.yaml")
    for ep in module.endpoints:
        print(ep.method, ep.path, ep.summary)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from models.module_map import EndpointInfo, ModuleInfo


# ---------------------------------------------------------------------------
# HTTP methods defined by the OpenAPI specification
# ---------------------------------------------------------------------------

_HTTP_METHODS: frozenset[str] = frozenset(
    {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_parameters(operation: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract parameter metadata from an operation object.

    Each parameter is normalised to a dict with at least ``name``,
    ``in``, ``type``, and ``required`` keys so downstream consumers
    have a predictable shape.

    Args:
        operation: A single OpenAPI operation object (e.g. the value
            under ``paths["/users"]["get"]``).

    Returns:
        A list of parameter dicts.
    """
    params: list[dict[str, Any]] = []
    for param in operation.get("parameters", []):
        schema = param.get("schema", {})
        params.append({
            "name": param.get("name", ""),
            "in": param.get("in", "query"),
            "type": schema.get("type", "string"),
            "required": param.get("required", False),
        })
    return params


def _extract_request_body(operation: dict[str, Any]) -> dict[str, Any] | None:
    """Extract the request body schema from an operation, if present.

    Looks for ``application/json`` content first, then falls back to
    the first available media type.

    Args:
        operation: A single OpenAPI operation object.

    Returns:
        The schema dict for the request body, or ``None`` if the
        operation has no request body.
    """
    req_body = operation.get("requestBody")
    if req_body is None:
        return None

    content = req_body.get("content", {})
    # Prefer application/json; fall back to first available media type.
    media = content.get("application/json") or next(iter(content.values()), None)
    if media is None:
        return None

    return media.get("schema")


def _extract_response_schema(operation: dict[str, Any]) -> dict[str, Any] | None:
    """Extract the schema for the primary success response (200 or 201).

    Args:
        operation: A single OpenAPI operation object.

    Returns:
        The response schema dict, or ``None`` if neither 200 nor 201
        defines a JSON schema.
    """
    responses = operation.get("responses", {})

    for status in ("200", "201"):
        response = responses.get(status)
        if response is None:
            continue

        content = response.get("content", {})
        media = content.get("application/json") or next(iter(content.values()), None)
        if media is not None:
            schema = media.get("schema")
            if schema is not None:
                return schema

    return None


def _load_spec(file_path: Path) -> dict[str, Any]:
    """Load an OpenAPI spec from a YAML or JSON file.

    Args:
        file_path: Path to the spec file.

    Returns:
        The parsed spec as a plain dict.

    Raises:
        FileNotFoundError: If *file_path* does not exist.
        ValueError: If the file extension is not recognised.
    """
    text = file_path.read_text(encoding="utf-8")
    suffix = file_path.suffix.lower()

    if suffix in (".yaml", ".yml"):
        # yaml.safe_load returns None for empty / comments-only files.
        return yaml.safe_load(text) or {}
    elif suffix == ".json":
        return json.loads(text)
    else:
        raise ValueError(
            f"Unsupported file extension '{suffix}'. "
            "Expected .yaml, .yml, or .json."
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_openapi_spec(file_path: str) -> ModuleInfo:
    """Parse an OpenAPI 3.x spec and return a :class:`ModuleInfo`.

    Each ``path + method`` combination in the spec becomes an
    :class:`EndpointInfo` in the returned module.

    .. note::

        ``$ref`` pointers are **not** resolved in Phase 1.  Specs that
        use ``$ref`` for parameters, request bodies, or schemas will
        produce incomplete data.  See TODO below.

    Args:
        file_path: Path to a ``.yaml``, ``.yml``, or ``.json`` OpenAPI
            specification file.

    Returns:
        A :class:`ModuleInfo` with ``type="openapi"`` and a populated
        ``endpoints`` list.

    Raises:
        FileNotFoundError: If *file_path* does not exist.
        ValueError: If the file extension is unsupported.
    """
    path = Path(file_path)
    spec = _load_spec(path)

    endpoints: list[EndpointInfo] = []
    paths = spec.get("paths", {})

    for url_path, path_item in paths.items():
        # Collect path-level parameters (shared across all methods).
        path_level_params = path_item.get("parameters", [])

        for method, operation in path_item.items():
            if method.lower() not in _HTTP_METHODS:
                # Skip non-method keys like "parameters", "summary", etc.
                continue

            # Merge path-level parameters with operation-level parameters.
            # Operation-level params override path-level ones by name+in.
            merged_operation = dict(operation)
            if path_level_params:
                op_params = operation.get("parameters", [])
                op_param_keys = {
                    (p.get("name"), p.get("in")) for p in op_params
                }
                inherited = [
                    p for p in path_level_params
                    if (p.get("name"), p.get("in")) not in op_param_keys
                ]
                merged_operation["parameters"] = inherited + op_params

            # TODO: resolve $ref pointers before extraction (Phase 2).
            endpoints.append(
                EndpointInfo(
                    path=url_path,
                    method=method.upper(),
                    summary=merged_operation.get("summary"),
                    parameters=_extract_parameters(merged_operation),
                    request_body=_extract_request_body(merged_operation),
                    response_schema=_extract_response_schema(merged_operation),
                )
            )

    # Derive a human-readable module name from the spec title or filename.
    info = spec.get("info", {})
    module_name = info.get("title", path.stem)

    return ModuleInfo(
        name=module_name,
        file_path=str(path),
        type="openapi",
        endpoints=endpoints,
    )

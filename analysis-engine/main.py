"""UnitForge Analysis Engine — CLI entry point.

Parses a Python codebase or OpenAPI specification and prints the
resulting module map as JSON to stdout.

Usage::

    # Parse a Python project directory
    python main.py --input ./my_app --type python

    # Parse a single Python file
    python main.py --input ./app/utils.py --type python

    # Parse an OpenAPI spec
    python main.py --input ./spec.yaml --type openapi
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from models.module_map import ModuleMap
from parsers.openapi_parser import parse_openapi_spec
from parsers.python_parser import parse_python_directory, parse_python_file


def _build_argument_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser.

    Returns:
        A configured :class:`argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(
        prog="analysis-engine",
        description=(
            "UnitForge Analysis Engine — parse source code or API specs "
            "into a structured module map (JSON)."
        ),
    )
    parser.add_argument(
        "--input",
        required=True,
        dest="input_path",
        help="Path to a source directory, file, or OpenAPI spec.",
    )
    parser.add_argument(
        "--type",
        required=True,
        dest="input_type",
        choices=("python", "java", "openapi"),
        help="Type of input to parse.",
    )
    return parser


def _parse_python(input_path: Path) -> ModuleMap:
    """Parse Python source(s) and return a :class:`ModuleMap`.

    If *input_path* is a directory, every ``.py`` file inside it is
    parsed.  If it is a single file, only that file is parsed.

    Args:
        input_path: Path to a Python file or directory.

    Returns:
        A :class:`ModuleMap` containing the parsed module(s).
    """
    if input_path.is_dir():
        modules = parse_python_directory(str(input_path))
    else:
        modules = [parse_python_file(str(input_path))]
    return ModuleMap(modules=modules)


def _parse_openapi(input_path: Path) -> ModuleMap:
    """Parse an OpenAPI spec and return a :class:`ModuleMap`.

    Args:
        input_path: Path to a ``.yaml``, ``.yml``, or ``.json`` spec.

    Returns:
        A :class:`ModuleMap` containing one module with endpoints.
    """
    module = parse_openapi_spec(str(input_path))
    return ModuleMap(modules=[module])


def main(argv: list[str] | None = None) -> int:
    """Run the analysis engine CLI.

    Args:
        argv: Command-line arguments.  Defaults to ``sys.argv[1:]``.

    Returns:
        Exit code — ``0`` on success, ``1`` on error.
    """
    parser = _build_argument_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input_path)
    if not input_path.exists():
        print(f"Error: path does not exist: {input_path}", file=sys.stderr)
        return 1

    input_type: str = args.input_type

    if input_type == "python":
        module_map = _parse_python(input_path)
    elif input_type == "openapi":
        module_map = _parse_openapi(input_path)
    elif input_type == "java":
        print(
            "Error: Java parsing is not yet implemented (Phase 2).",
            file=sys.stderr,
        )
        return 1
    else:
        # argparse choices guard makes this unreachable, but defensive.
        print(f"Error: unsupported type: {input_type}", file=sys.stderr)
        return 1

    print(module_map.to_json())
    return 0


if __name__ == "__main__":
    sys.exit(main())

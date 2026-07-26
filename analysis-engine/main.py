"""UnitForge Analysis Engine — CLI entry point.

Parses a Python codebase, OpenAPI specification, or GitHub repository
and prints the resulting module map as JSON to stdout.

Usage::

    # Parse a Python project directory
    python main.py --input ./my_app --type python

    # Parse a single Python file
    python main.py --input ./app/utils.py --type python

    # Parse an OpenAPI spec
    python main.py --input ./spec.yaml --type openapi

    # Parse a GitHub repository
    python main.py --input https://github.com/user/repo --type python
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from github_cloner import cleanup_clone, clone_repository, is_github_url
from models.module_map import ModuleMap
from parsers.openapi_parser import parse_openapi_spec
from parsers.python_parser import parse_python_directory, parse_python_file

logger = logging.getLogger(__name__)


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
        help=(
            "Path to a source directory, file, OpenAPI spec, "
            "or a GitHub URL (e.g. https://github.com/user/repo)."
        ),
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

    If ``--input`` is a GitHub URL the repository is cloned to a
    temporary directory, analysed, and the temp directory is cleaned
    up automatically.

    Args:
        argv: Command-line arguments.  Defaults to ``sys.argv[1:]``.

    Returns:
        Exit code — ``0`` on success, ``1`` on error.
    """
    parser = _build_argument_parser()
    args = parser.parse_args(argv)

    raw_input: str = args.input_path
    input_type: str = args.input_type
    clone_result = None

    try:
        # --- Resolve input path (local or GitHub) -------------------
        if is_github_url(raw_input):
            logger.info("GitHub URL detected: %s", raw_input)
            clone_result = clone_repository(raw_input)

            if not clone_result.success:
                print(
                    f"Error: {clone_result.error_message}",
                    file=sys.stderr,
                )
                return 1

            actual_path = Path(clone_result.local_path)  # type: ignore[arg-type]
            logger.info("Analyzing cloned repo at: %s", actual_path)
        else:
            actual_path = Path(raw_input)
            if not actual_path.exists():
                print(
                    f"Error: path does not exist: {actual_path}",
                    file=sys.stderr,
                )
                return 1

        # --- Run the appropriate parser -----------------------------
        if input_type == "python":
            module_map = _parse_python(actual_path)
        elif input_type == "openapi":
            module_map = _parse_openapi(actual_path)
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

    finally:
        # Always clean up temp directories, even on errors.
        if clone_result is not None:
            cleanup_clone(clone_result)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )
    sys.exit(main())

"""AST-based Python source parser for the UnitForge analysis engine.

Walks a ``.py`` file (or a directory of ``.py`` files) using the stdlib
``ast`` module and extracts functions, classes, imports, and metadata
into :class:`ModuleInfo` objects.

Usage::

    from parsers.python_parser import parse_python_file, parse_python_directory

    module = parse_python_file("app/utils.py")
    modules = parse_python_directory("app/")
"""

from __future__ import annotations

import ast
import os
from pathlib import Path

from models.module_map import ClassInfo, FunctionInfo, ModuleInfo


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _unparse_annotation(node: ast.expr | None) -> str | None:
    """Convert an AST annotation node back to its source-code string.

    Args:
        node: An AST expression node representing a type annotation,
            or ``None`` if no annotation is present.

    Returns:
        The annotation as a string (e.g. ``"int"``, ``"list[str]"``),
        or ``None`` when *node* is ``None``.
    """
    if node is None:
        return None
    return ast.unparse(node)


def _extract_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionInfo:
    """Build a :class:`FunctionInfo` from an AST function node.

    Captures positional args, keyword-only args, ``*args``, and
    ``**kwargs`` so the orchestrator/test-agent receives a complete
    function signature.

    Args:
        node: An ``ast.FunctionDef`` or ``ast.AsyncFunctionDef`` node.

    Returns:
        A populated :class:`FunctionInfo` dataclass.
    """
    args: list[str] = [arg.arg for arg in node.args.args]

    # *args
    if node.args.vararg is not None:
        args.append(f"*{node.args.vararg.arg}")

    # keyword-only args (appear after * or *args)
    for arg in node.args.kwonlyargs:
        args.append(arg.arg)

    # **kwargs
    if node.args.kwarg is not None:
        args.append(f"**{node.args.kwarg.arg}")

    return_type = _unparse_annotation(node.returns)
    docstring = ast.get_docstring(node)

    return FunctionInfo(
        name=node.name,
        args=args,
        return_type=return_type,
        docstring=docstring,
        line_no=node.lineno,
    )


def _extract_class(node: ast.ClassDef) -> ClassInfo:
    """Build a :class:`ClassInfo` from an AST class node.

    Args:
        node: An ``ast.ClassDef`` node.

    Returns:
        A populated :class:`ClassInfo` dataclass whose ``methods`` list
        contains every ``def`` / ``async def`` in the class body.
    """
    methods: list[FunctionInfo] = []
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(_extract_function(child))
    return ClassInfo(name=node.name, methods=methods)


def _extract_imports(tree: ast.Module) -> list[str]:
    """Collect all imported module names from the top-level of an AST.

    Both ``import foo`` and ``from foo import bar`` produce ``"foo"`` in
    the returned list.  Relative imports (``from . import x``) record
    the dotted prefix (e.g. ``"."``) to preserve information without
    fabricating a module name.

    Args:
        tree: The parsed AST module.

    Returns:
        A deduplicated, sorted list of imported module name strings.
    """
    names: set[str] = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                names.add(node.module)
            else:
                # Relative import with no module (e.g. ``from . import x``)
                names.add("." * (node.level or 1))
    return sorted(names)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_python_file(file_path: str) -> ModuleInfo:
    """Parse a single Python file and return its :class:`ModuleInfo`.

    Args:
        file_path: Path to a ``.py`` file (absolute or relative).

    Returns:
        A :class:`ModuleInfo` with ``type="python"``, populated
        ``functions``, ``classes``, and ``imports`` fields.

    Raises:
        FileNotFoundError: If *file_path* does not exist.
        SyntaxError: If the file contains invalid Python.
    """
    path = Path(file_path)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))

    functions: list[FunctionInfo] = []
    classes: list[ClassInfo] = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(_extract_function(node))
        elif isinstance(node, ast.ClassDef):
            classes.append(_extract_class(node))

    imports = _extract_imports(tree)

    # Derive a human-readable module name from the filename.
    module_name = path.stem

    return ModuleInfo(
        name=module_name,
        file_path=str(path),
        type="python",
        functions=functions,
        classes=classes,
        imports=imports,
    )


def parse_python_directory(directory_path: str) -> list[ModuleInfo]:
    """Recursively parse every ``.py`` file under *directory_path*.

    Skips ``__init__.py`` (package markers) and prunes hidden/internal
    directories (``__pycache__``, ``.git``, ``.venv``, etc.) so the
    output focuses on user-written application code.

    Args:
        directory_path: Path to a directory containing Python source
            files.

    Returns:
        A list of :class:`ModuleInfo` objects, one per ``.py`` file
        found.  The ``file_path`` field on each object is relative to
        *directory_path*.

    Raises:
        NotADirectoryError: If *directory_path* is not a directory.
    """
    root = Path(directory_path)
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    modules: list[ModuleInfo] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune hidden dirs and __pycache__ in-place so os.walk
        # does not descend into them.
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(("__", "."))
        ]

        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue
            # Skip package init files — not user application logic.
            if filename == "__init__.py":
                continue

            full_path = Path(dirpath) / filename
            module = parse_python_file(str(full_path))

            # Store relative path for portability.
            module.file_path = str(full_path.relative_to(root))
            modules.append(module)

    return modules

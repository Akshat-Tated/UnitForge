"""Tests for the AST-based Python parser.

Covers the five scenarios mandated by ARCHITECTURE.md plus directory parsing:
  1. Function extraction (name, args, docstring)
  2. Class method extraction
  3. Import detection
  4. Edge case — empty file
  5. Edge case — file with only classes, no top-level functions
  6. Directory parsing (pruning, relative paths, __init__.py skipping)
"""

from __future__ import annotations

from pathlib import Path

import pytest

from parsers.python_parser import parse_python_file, parse_python_directory
from models.module_map import ModuleInfo

# ---------------------------------------------------------------------------
# Fixture paths
# ---------------------------------------------------------------------------

_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "sample_python_app"
_TASK_MANAGER = str(_FIXTURES / "task_manager.py")
_STORAGE = str(_FIXTURES / "storage.py")
_EMPTY = str(_FIXTURES / "empty.py")


# ---------------------------------------------------------------------------
# Shared pytest fixtures — parse each file once per class
# ---------------------------------------------------------------------------

@pytest.fixture(scope="class")
def task_manager_info() -> ModuleInfo:
    """Parse task_manager.py once and share across all tests in a class."""
    return parse_python_file(_TASK_MANAGER)


@pytest.fixture(scope="class")
def storage_info() -> ModuleInfo:
    """Parse storage.py once and share across all tests in a class."""
    return parse_python_file(_STORAGE)


@pytest.fixture(scope="class")
def empty_info() -> ModuleInfo:
    """Parse empty.py once and share across all tests in a class."""
    return parse_python_file(_EMPTY)


# ---------------------------------------------------------------------------
# 1. Function extraction (name, args, docstring)
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("task_manager_info")
class TestFunctionExtraction:
    """Verify that top-level functions are fully extracted."""

    def test_function_names_and_count(self, task_manager_info: ModuleInfo) -> None:
        """Parser finds all 4 top-level functions in task_manager.py."""
        names = [f.name for f in task_manager_info.functions]
        assert len(names) == 4
        assert "create_task" in names
        assert "filter_tasks" in names
        assert "export_tasks_to_json" in names
        assert "calculate_deadline" in names

    def test_function_args_with_defaults(self, task_manager_info: ModuleInfo) -> None:
        """``create_task`` has three positional args including one with a default."""
        create = next(f for f in task_manager_info.functions if f.name == "create_task")
        assert create.args == ["title", "description", "priority"]

    def test_function_varargs_and_kwargs(self, task_manager_info: ModuleInfo) -> None:
        """``filter_tasks`` captures *tags; ``export_tasks_to_json`` captures **options."""
        filter_fn = next(f for f in task_manager_info.functions if f.name == "filter_tasks")
        assert "*tags" in filter_fn.args

        export_fn = next(f for f in task_manager_info.functions if f.name == "export_tasks_to_json")
        assert "**options" in export_fn.args

    def test_function_docstring(self, task_manager_info: ModuleInfo) -> None:
        """``create_task`` docstring is captured and starts correctly."""
        create = next(f for f in task_manager_info.functions if f.name == "create_task")
        assert create.docstring is not None
        assert create.docstring.startswith("Create a new task dictionary")

    def test_function_return_type(self, task_manager_info: ModuleInfo) -> None:
        """``create_task`` return type annotation is ``dict``."""
        create = next(f for f in task_manager_info.functions if f.name == "create_task")
        assert create.return_type == "dict"

    def test_function_line_numbers(self, task_manager_info: ModuleInfo) -> None:
        """Line numbers are positive integers and in ascending order."""
        line_nos = [f.line_no for f in task_manager_info.functions]
        assert all(ln > 0 for ln in line_nos)
        assert line_nos == sorted(line_nos)


# ---------------------------------------------------------------------------
# 2. Class method extraction
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("storage_info")
class TestClassMethodExtraction:
    """Verify that classes and their methods are extracted."""

    def test_class_names(self, storage_info: ModuleInfo) -> None:
        """Parser finds both classes in storage.py."""
        class_names = [c.name for c in storage_info.classes]
        assert "TaskStore" in class_names
        assert "PersistentTaskStore" in class_names

    def test_method_names(self, storage_info: ModuleInfo) -> None:
        """``TaskStore`` exposes __init__, add, get, delete, list_all."""
        store = next(c for c in storage_info.classes if c.name == "TaskStore")
        method_names = [m.name for m in store.methods]
        assert "__init__" in method_names
        assert "add" in method_names
        assert "get" in method_names
        assert "delete" in method_names
        assert "list_all" in method_names

    def test_method_has_self_arg(self, storage_info: ModuleInfo) -> None:
        """Every method's first argument is ``self``."""
        store = next(c for c in storage_info.classes if c.name == "TaskStore")
        for method in store.methods:
            assert method.args[0] == "self", f"{method.name} missing 'self'"

    def test_method_docstring(self, storage_info: ModuleInfo) -> None:
        """``TaskStore.add`` has a docstring."""
        store = next(c for c in storage_info.classes if c.name == "TaskStore")
        add = next(m for m in store.methods if m.name == "add")
        assert add.docstring is not None
        assert "Add a task" in add.docstring


# ---------------------------------------------------------------------------
# 3. Import detection
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("task_manager_info")
class TestImportDetection:
    """Verify that imports are collected correctly."""

    def test_imports_present(self, task_manager_info: ModuleInfo) -> None:
        """task_manager.py imports os, json, datetime, and typing."""
        assert "os" in task_manager_info.imports
        assert "json" in task_manager_info.imports
        assert "datetime" in task_manager_info.imports
        assert "typing" in task_manager_info.imports

    def test_imports_sorted_and_unique(self, task_manager_info: ModuleInfo) -> None:
        """Import list is sorted alphabetically with no duplicates."""
        assert task_manager_info.imports == sorted(set(task_manager_info.imports))


# ---------------------------------------------------------------------------
# 4. Edge case — empty file
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("empty_info")
class TestEmptyFile:
    """Verify graceful handling of an empty .py file."""

    def test_empty_file_returns_module_info(self, empty_info: ModuleInfo) -> None:
        """An empty file still produces a valid ModuleInfo."""
        assert isinstance(empty_info, ModuleInfo)
        assert empty_info.type == "python"

    def test_empty_file_has_no_functions(self, empty_info: ModuleInfo) -> None:
        """No functions are extracted from an empty file."""
        assert empty_info.functions == []

    def test_empty_file_has_no_classes(self, empty_info: ModuleInfo) -> None:
        """No classes are extracted from an empty file."""
        assert empty_info.classes == []

    def test_empty_file_has_no_imports(self, empty_info: ModuleInfo) -> None:
        """No imports are extracted from an empty file."""
        assert empty_info.imports == []


# ---------------------------------------------------------------------------
# 5. Edge case — file with only classes, no top-level functions
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("storage_info")
class TestClassesOnlyFile:
    """Verify that a file with classes but no top-level functions is handled."""

    def test_no_top_level_functions(self, storage_info: ModuleInfo) -> None:
        """storage.py has zero top-level functions."""
        assert storage_info.functions == []

    def test_classes_still_extracted(self, storage_info: ModuleInfo) -> None:
        """Classes are still found even when there are no functions."""
        assert len(storage_info.classes) == 2

    def test_module_name(self, storage_info: ModuleInfo) -> None:
        """Module name is derived from the filename stem."""
        assert storage_info.name == "storage"


# ---------------------------------------------------------------------------
# 6. Directory parsing
# ---------------------------------------------------------------------------

class TestDirectoryParsing:
    """Verify parse_python_directory walker: pruning, paths, skipping."""

    def test_finds_all_py_files(self) -> None:
        """Directory parse discovers task_manager, storage, and empty."""
        modules = parse_python_directory(str(_FIXTURES))
        names = [m.name for m in modules]
        assert "task_manager" in names
        assert "storage" in names
        assert "empty" in names

    def test_excludes_init_files(self) -> None:
        """__init__.py is skipped by the directory walker."""
        modules = parse_python_directory(str(_FIXTURES))
        file_paths = [m.file_path for m in modules]
        assert not any("__init__" in fp for fp in file_paths)

    def test_file_paths_are_relative(self) -> None:
        """file_path on each module is relative to the input directory."""
        modules = parse_python_directory(str(_FIXTURES))
        for module in modules:
            assert not Path(module.file_path).is_absolute(), (
                f"{module.name} has absolute file_path: {module.file_path}"
            )

    def test_not_a_directory_raises(self) -> None:
        """Passing a file path raises NotADirectoryError."""
        with pytest.raises(NotADirectoryError):
            parse_python_directory(_TASK_MANAGER)

"""Storage backends for the task manager — classes-only fixture.

This module intentionally has NO top-level functions, only classes.
Used to test the parser's handling of class-only modules.
"""

from typing import Optional


class TaskStore:
    """In-memory task storage with basic CRUD operations."""

    def __init__(self) -> None:
        """Initialise an empty task store."""
        self._tasks: dict[str, dict] = {}

    def add(self, task: dict) -> str:
        """Add a task and return its ID.

        Args:
            task: A task dictionary (must contain an ``"id"`` key).

        Returns:
            The task's ID string.
        """
        task_id = task["id"]
        self._tasks[task_id] = task
        return task_id

    def get(self, task_id: str) -> Optional[dict]:
        """Retrieve a task by ID, or ``None`` if not found."""
        return self._tasks.get(task_id)

    def delete(self, task_id: str) -> bool:
        """Remove a task by ID.

        Returns:
            ``True`` if the task existed and was removed, ``False``
            otherwise.
        """
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def list_all(self) -> list[dict]:
        """Return all stored tasks as a list."""
        return list(self._tasks.values())


class PersistentTaskStore(TaskStore):
    """Extends TaskStore with file-based persistence (stub)."""

    def __init__(self, db_path: str) -> None:
        """Initialise with a file path for persistence.

        Args:
            db_path: Path to the JSON file used for storage.
        """
        super().__init__()
        self._db_path: str = db_path

    def save(self) -> None:
        """Write current tasks to disk (stub — not implemented)."""
        raise NotImplementedError("Persistence not yet implemented")

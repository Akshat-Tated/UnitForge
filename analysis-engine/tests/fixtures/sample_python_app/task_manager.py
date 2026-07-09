"""Task manager utilities — sample fixture for parser tests.

A small but realistic module with top-level functions, imports, type
hints, docstrings, and varied argument signatures.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional


def create_task(title: str, description: str, priority: int = 3) -> dict:
    """Create a new task dictionary with metadata.

    Args:
        title: Short title for the task.
        description: Detailed description of what needs to be done.
        priority: Urgency level from 1 (highest) to 5 (lowest).

    Returns:
        A dictionary representing the task with an auto-generated ID
        and creation timestamp.
    """
    return {
        "id": os.urandom(8).hex(),
        "title": title,
        "description": description,
        "priority": priority,
        "created_at": datetime.now().isoformat(),
        "completed": False,
    }


def filter_tasks(tasks: list[dict], *tags: str, completed: bool = False) -> list[dict]:
    """Filter a list of tasks by completion status and optional tags.

    Args:
        tasks: The full list of task dictionaries.
        *tags: If provided, only return tasks whose title contains
            at least one of the given tags.
        completed: When ``True``, return only completed tasks.

    Returns:
        A filtered list of task dictionaries.
    """
    results = [t for t in tasks if t.get("completed") == completed]
    if tags:
        results = [
            t for t in results
            if any(tag.lower() in t["title"].lower() for tag in tags)
        ]
    return results


def export_tasks_to_json(tasks: list[dict], file_path: str, **options) -> None:
    """Serialise a list of tasks to a JSON file.

    Args:
        tasks: Task dictionaries to write.
        file_path: Destination path for the JSON output.
        **options: Extra keyword arguments forwarded to ``json.dump``
            (e.g. ``indent=2``).
    """
    with open(file_path, "w", encoding="utf-8") as fh:
        json.dump(tasks, fh, **options)


def calculate_deadline(days_from_now: int) -> str:
    """Return an ISO-formatted date string *days_from_now* days in the future."""
    return (datetime.now() + timedelta(days=days_from_now)).date().isoformat()

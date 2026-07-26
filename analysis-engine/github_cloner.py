"""UnitForge — GitHub Repository Cloner.

Clones a GitHub repository to a temporary directory for analysis
by the python_parser.  Supports HTTPS URLs with or without the
``https://`` prefix and ``.git`` suffix.

Usage::

    from github_cloner import is_github_url, clone_repository, cleanup_clone

    if is_github_url(user_input):
        result = clone_repository(user_input)
        try:
            # ... analyse result.local_path ...
        finally:
            cleanup_clone(result)
"""

from __future__ import annotations

import logging
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CloneResult:
    """Result of a GitHub clone operation.

    Attributes:
        success: Whether the clone completed without errors.
        local_path: Absolute path to the cloned repository on disk,
            or ``None`` if the clone failed.
        error_message: Human-readable error description, or ``None``
            on success.
        repo_name: Repository name extracted from the URL
            (e.g. ``"UnitForge"``).
        is_temp: ``True`` if a temporary directory was created and
            should be cleaned up by the caller via
            :func:`cleanup_clone`.
    """

    success: bool
    local_path: str | None
    error_message: str | None
    repo_name: str
    is_temp: bool


def is_github_url(input_path: str) -> bool:
    """Check if *input_path* is a GitHub URL rather than a local path.

    Examples that return ``True``::

        https://github.com/user/repo
        https://github.com/user/repo.git
        github.com/user/repo

    Args:
        input_path: The raw ``--input`` value from the CLI.

    Returns:
        ``True`` if the string contains ``github.com``.
    """
    return "github.com" in input_path


def extract_repo_name(github_url: str) -> str:
    """Extract the repository name from a GitHub URL.

    Example::

        >>> extract_repo_name("https://github.com/Akshat-Tated/UnitForge")
        'UnitForge'

    Args:
        github_url: A GitHub URL (with or without ``.git`` suffix).

    Returns:
        The repository name as a plain string.
    """
    # Remove .git suffix and trailing slash if present.
    url = github_url.rstrip("/").replace(".git", "")
    # The last path segment is the repo name.
    return url.split("/")[-1]


def clone_repository(github_url: str) -> CloneResult:
    """Clone a GitHub repository to a temporary directory.

    Performs a shallow clone (``depth=1``) to minimise download time
    and disk usage.

    Args:
        github_url: The GitHub URL to clone, e.g.
            ``https://github.com/user/repo``.

    Returns:
        A :class:`CloneResult` with ``local_path`` pointing to the
        cloned repository.

    Note:
        The caller is responsible for cleaning up the temporary
        directory when ``is_temp=True``.  Use :func:`cleanup_clone`
        for this.
    """
    try:
        import git  # noqa: F811 — lazy import to give a clear error message
    except ImportError:
        return CloneResult(
            success=False,
            local_path=None,
            error_message="gitpython not installed. Run: pip install gitpython",
            repo_name="unknown",
            is_temp=False,
        )

    # Ensure URL has https:// prefix.
    url = github_url
    if not url.startswith("http"):
        url = "https://" + url

    repo_name = extract_repo_name(url)
    temp_dir = tempfile.mkdtemp(prefix=f"unitforge_{repo_name}_")

    logger.info("Cloning %s to %s...", url, temp_dir)

    try:
        git.Repo.clone_from(url, temp_dir, depth=1)
        logger.info("Successfully cloned %s", repo_name)
        return CloneResult(
            success=True,
            local_path=temp_dir,
            error_message=None,
            repo_name=repo_name,
            is_temp=True,
        )
    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        error = str(exc)
        logger.error("Failed to clone %s: %s", url, error)
        return CloneResult(
            success=False,
            local_path=None,
            error_message=f"Failed to clone repository: {error}",
            repo_name=repo_name,
            is_temp=False,
        )


def cleanup_clone(clone_result: CloneResult) -> None:
    """Remove the temporary directory created by :func:`clone_repository`.

    Safe to call multiple times or on a failed :class:`CloneResult` —
    it is a no-op when there is nothing to clean up.

    Args:
        clone_result: The result object returned by
            :func:`clone_repository`.
    """
    if clone_result.is_temp and clone_result.local_path:
        shutil.rmtree(clone_result.local_path, ignore_errors=True)
        logger.info("Cleaned up temp directory: %s", clone_result.local_path)

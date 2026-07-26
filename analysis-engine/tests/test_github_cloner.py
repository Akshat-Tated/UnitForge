"""Tests for the GitHub repository cloner helpers.

Only tests the pure helper functions ``is_github_url`` and
``extract_repo_name``.  No tests call ``clone_repository`` because
that would require network access and be slow/flaky.
"""

from __future__ import annotations

import pytest

from github_cloner import extract_repo_name, is_github_url


# ---------------------------------------------------------------------------
# is_github_url
# ---------------------------------------------------------------------------

class TestIsGithubUrl:
    """Verify GitHub URL detection."""

    def test_is_github_url_with_https(self) -> None:
        """A full HTTPS GitHub URL is recognised."""
        assert is_github_url("https://github.com/user/repo") is True

    def test_is_github_url_with_local_path(self) -> None:
        """A relative local path is not a GitHub URL."""
        assert is_github_url("./my-project") is False

    def test_is_github_url_without_scheme(self) -> None:
        """A bare github.com URL (no https://) is still recognised."""
        assert is_github_url("github.com/user/repo") is True

    def test_is_github_url_with_git_suffix(self) -> None:
        """A .git-suffixed URL is recognised."""
        assert is_github_url("https://github.com/user/repo.git") is True

    def test_is_github_url_with_absolute_path(self) -> None:
        """An absolute local path is not a GitHub URL."""
        assert is_github_url("C:\\Users\\dev\\project") is False


# ---------------------------------------------------------------------------
# extract_repo_name
# ---------------------------------------------------------------------------

class TestExtractRepoName:
    """Verify repository name extraction from GitHub URLs."""

    def test_extract_repo_name_basic(self) -> None:
        """Standard HTTPS URL extracts the repo name."""
        result = extract_repo_name("https://github.com/Akshat-Tated/UnitForge")
        assert result == "UnitForge"

    def test_extract_repo_name_with_git_suffix(self) -> None:
        """The ``.git`` suffix is stripped from the repo name."""
        result = extract_repo_name("https://github.com/user/myrepo.git")
        assert result == "myrepo"

    def test_extract_repo_name_with_trailing_slash(self) -> None:
        """A trailing slash does not affect extraction."""
        result = extract_repo_name("https://github.com/user/myrepo/")
        assert result == "myrepo"

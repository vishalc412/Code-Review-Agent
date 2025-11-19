"""Tests for utility functions."""

import pytest
from core.utils import (
    truncate_text,
    parse_repository_name,
    should_exclude_file,
    sanitize_branch_name,
)


def test_truncate_text():
    """Test text truncation."""
    text = "a" * 100
    truncated = truncate_text(text, max_length=50)

    assert len(truncated) <= 50
    assert truncated.endswith("...")


def test_parse_repository_name():
    """Test repository name parsing."""
    owner, repo = parse_repository_name("owner/repo")

    assert owner == "owner"
    assert repo == "repo"


def test_parse_repository_name_invalid():
    """Test repository name parsing with invalid format."""
    with pytest.raises(ValueError):
        parse_repository_name("invalid")


def test_should_exclude_file():
    """Test file exclusion."""
    patterns = ["*.md", "*.txt", "test/**"]

    assert should_exclude_file("README.md", patterns) is True
    assert should_exclude_file("test.txt", patterns) is True
    assert should_exclude_file("src/main.py", patterns) is False


def test_sanitize_branch_name():
    """Test branch name sanitization."""
    name = "feature/My Feature (WIP)"
    sanitized = sanitize_branch_name(name)

    assert "/" in sanitized or "-" in sanitized
    assert "(" not in sanitized
    assert ")" not in sanitized
    assert sanitized.islower()

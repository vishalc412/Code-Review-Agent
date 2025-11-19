"""Tests for diff parser."""

import pytest
from parsers.diff_parser import DiffParser


def test_parse_simple_diff(sample_diff):
    """Test parsing a simple diff."""
    parser = DiffParser()
    file_diffs = parser.parse(sample_diff)

    assert len(file_diffs) > 0
    assert file_diffs[0].file_path == "test.py"


def test_diff_stats(sample_diff):
    """Test diff statistics."""
    parser = DiffParser()
    file_diffs = parser.parse(sample_diff)
    stats = parser.get_file_changes_summary(file_diffs)

    assert 'total_files' in stats
    assert 'additions' in stats
    assert 'deletions' in stats
    assert stats['total_files'] >= 1


def test_parse_empty_diff():
    """Test parsing an empty diff."""
    parser = DiffParser()
    file_diffs = parser.parse("")

    assert len(file_diffs) == 0

"""Tests for the diff parser module."""

import pytest

from git_sage.git.diff_parser import parse_diff, get_changed_files, estimate_tokens


class TestParseDiff:
    """Tests for parse_diff()."""

    def test_parse_valid_diff(self, sample_diff):
        """Should parse a valid diff into structured chunks."""
        chunks = parse_diff(sample_diff)
        assert len(chunks) == 1
        assert chunks[0]["file"] == "src/auth.py"
        assert chunks[0]["additions"] > 0

    def test_parse_empty_diff(self, empty_diff):
        """Should return empty list for empty diff."""
        chunks = parse_diff(empty_diff)
        assert chunks == []

    def test_parse_diff_with_multiple_files(self, sample_diff_with_secret):
        """Should parse diff with file changes."""
        chunks = parse_diff(sample_diff_with_secret)
        assert len(chunks) >= 1
        assert any(c["file"] == "config.py" for c in chunks)

    def test_parse_diff_hunks(self, sample_diff):
        """Should extract hunks with line info."""
        chunks = parse_diff(sample_diff)
        assert len(chunks[0]["hunks"]) > 0
        hunk = chunks[0]["hunks"][0]
        assert "source_start" in hunk
        assert "content" in hunk


class TestGetChangedFiles:
    """Tests for get_changed_files()."""

    def test_returns_file_paths(self, sample_diff):
        """Should return list of changed file paths."""
        files = get_changed_files(sample_diff)
        assert "src/auth.py" in files

    def test_empty_diff_returns_empty(self, empty_diff):
        """Should return empty list for empty diff."""
        files = get_changed_files(empty_diff)
        assert files == []


class TestEstimateTokens:
    """Tests for estimate_tokens()."""

    def test_estimates_tokens(self):
        """Should return a positive token count for non-empty text."""
        tokens = estimate_tokens("Hello, world! This is a test string.")
        assert tokens > 0

    def test_empty_string(self):
        """Should return 0 for empty string."""
        tokens = estimate_tokens("")
        assert tokens == 0

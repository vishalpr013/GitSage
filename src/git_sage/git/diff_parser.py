"""Diff parser — parse unified diffs into structured chunks.

Uses the `unidiff` library to convert raw diff text into
structured data that agents can process file-by-file.
"""

from __future__ import annotations

from io import StringIO

from unidiff import PatchSet


def parse_diff(diff_text: str) -> list[dict]:
    """Parse a unified diff string into structured file chunks.

    Each chunk contains:
      - file: file path
      - additions: count of added lines
      - deletions: count of deleted lines
      - hunks: list of hunk dicts with context
      - content: the raw diff text for this file

    Returns an empty list if the diff is empty or unparseable.
    """
    if not diff_text or not diff_text.strip():
        return []

    try:
        patch_set = PatchSet(StringIO(diff_text))
    except Exception:

        # If unidiff can't parse it, return the whole diff as one chunk
        return [
            {
                "file": "unknown",
                "additions": 0,
                "deletions": 0,
                "hunks": [],
                "content": diff_text,
            }
        ]

    chunks = []
    for patched_file in patch_set:
        file_path = patched_file.path

        hunks = []
        for hunk in patched_file:
            hunk_lines = []
            for line in hunk:
                prefix = " "
                if line.is_added:
                    prefix = "+"
                elif line.is_removed:
                    prefix = "-"
                hunk_lines.append(f"{prefix}{line.value.rstrip()}")

            hunks.append(
                {
                    "source_start": hunk.source_start,
                    "source_length": hunk.source_length,
                    "target_start": hunk.target_start,
                    "target_length": hunk.target_length,
                    "content": "\n".join(hunk_lines),
                }
            )

        chunks.append(
            {
                "file": file_path,
                "additions": patched_file.added,
                "deletions": patched_file.removed,
                "is_new": patched_file.is_added_file,
                "is_deleted": patched_file.is_removed_file,
                "is_renamed": patched_file.is_rename,
                "hunks": hunks,
                "content": str(patched_file),
            }
        )

    return chunks


def get_changed_files(diff_text: str) -> list[str]:
    """Extract the list of changed file paths from a diff."""
    chunks = parse_diff(diff_text)
    return [c["file"] for c in chunks]


def estimate_tokens(diff_text: str) -> int:
    """Rough token estimate for a diff string.

    Uses the ~4 chars per token heuristic.
    More accurate estimation would use tiktoken.
    """
    return len(diff_text) // 4

"""Patch application — apply AI-generated fixes to files."""

from __future__ import annotations

from typing import Optional

from git import Repo


def apply_patch(repo: Repo, patch: dict) -> bool:
    """Apply a single patch dict to the working tree.

    The patch dict should contain:
      - file: relative file path
      - original: the original code snippet to find
      - replacement: the replacement code snippet

    Returns True if the patch was applied successfully.
    """
    import os

    file_path = patch.get("file", "")
    original = patch.get("original", "")
    replacement = patch.get("replacement", "")

    if not file_path or not original:
        return False

    full_path = os.path.join(repo.working_tree_dir or "", file_path)

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        if original not in content:
            return False

        # Replace the first occurrence
        new_content = content.replace(original, replacement, 1)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        # Stage the fixed file
        repo.index.add([file_path])

        return True

    except (FileNotFoundError, PermissionError, UnicodeDecodeError):
        return False

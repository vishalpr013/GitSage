"""Git context extraction — diffs, logs, blame, commit details.

Uses GitPython to interact with the local Git repository.
"""

from __future__ import annotations

from typing import Optional

from git import Repo, InvalidGitRepositoryError, GitCommandError


def get_repo() -> Optional[Repo]:
    """Get the Git repo from the current working directory.

    Returns None if not inside a Git repository.
    """
    try:
        return Repo(search_parent_directories=True)
    except InvalidGitRepositoryError:
        return None


def get_staged_diff(repo: Repo) -> str:
    """Get the unified diff of all staged (indexed) changes.

    Equivalent to `git diff --cached`.
    """
    try:
        return repo.git.diff("--cached", "--unified=3")
    except GitCommandError:
        return ""


def get_commit_diff(repo: Repo, sha: str) -> str:
    """Get the diff introduced by a specific commit.

    Equivalent to `git show --format="" <sha>`.
    """
    try:
        return repo.git.show(sha, format="", unified=3)
    except GitCommandError:
        return ""


def get_commit_details(repo: Repo, sha: str) -> Optional[dict]:
    """Get structured details about a commit.

    Returns a dict with SHA, author, date, message, diff, and file list.
    """
    try:
        commit = repo.commit(sha)
        diff_text = get_commit_diff(repo, str(commit.hexsha))

        return {
            "sha": str(commit.hexsha),
            "short_sha": str(commit.hexsha)[:7],
            "author": f"{commit.author.name} <{commit.author.email}>",
            "date": commit.committed_datetime.isoformat(),
            "subject": commit.message.split("\n")[0].strip(),
            "body": "\n".join(commit.message.split("\n")[1:]).strip(),
            "diff": diff_text,
            "files_changed": [
                item.a_path or item.b_path
                for item in commit.diff(commit.parents[0] if commit.parents else None)
            ],
        }
    except (GitCommandError, ValueError, IndexError):
        return None


def get_recent_log(
    repo: Repo, max_count: int = 20, file_path: Optional[str] = None
) -> list[dict]:
    """Get recent commit log with diffs for blame analysis.

    Returns a list of commit dicts with SHA, message, date, and diff.
    """
    result = []
    try:
        log_args = ["--max-count", str(max_count)]
        if file_path:
            log_args.extend(["--", file_path])

        for commit in repo.iter_commits(max_count=max_count):
            diff_text = get_commit_diff(repo, str(commit.hexsha))
            result.append(
                {
                    "sha": str(commit.hexsha),
                    "short_sha": str(commit.hexsha)[:7],
                    "author": str(commit.author.name),
                    "date": commit.committed_datetime.isoformat(),
                    "message": commit.message.strip(),
                    "diff": diff_text[:3000],  # Truncate large diffs for token efficiency
                }
            )
    except GitCommandError:
        pass

    return result


def get_log_between(
    repo: Repo,
    from_ref: Optional[str] = None,
    to_ref: str = "HEAD",
) -> list[dict]:
    """Get commit log between two refs for changelog generation.

    If from_ref is None, tries to find the most recent tag.
    """
    result = []
    try:
        # Find the starting point
        if from_ref is None:
            try:
                from_ref = repo.git.describe("--tags", "--abbrev=0", to_ref)
            except GitCommandError:
                # No tags found — use first commit
                from_ref = repo.git.rev_list("--max-parents=0", "HEAD").split("\n")[0]

        rev_range = f"{from_ref}..{to_ref}"

        for commit in repo.iter_commits(rev_range):
            result.append(
                {
                    "sha": str(commit.hexsha),
                    "short_sha": str(commit.hexsha)[:7],
                    "author": str(commit.author.name),
                    "date": commit.committed_datetime.isoformat(),
                    "message": commit.message.strip(),
                }
            )
    except GitCommandError:
        pass

    return result


def run_git_commit(repo: Repo, message: str) -> None:
    """Create a commit with the given message.

    Assumes files are already staged.
    """
    repo.index.commit(message)


def get_file_content(repo: Repo, file_path: str) -> Optional[str]:
    """Read the current content of a file in the working tree.

    Used to provide full file context to agents when needed.
    """
    import os

    full_path = os.path.join(repo.working_tree_dir or "", file_path)
    try:
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except (FileNotFoundError, PermissionError):
        return None

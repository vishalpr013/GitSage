"""git-sage explain — Explain a commit in plain English."""

import typer
from rich.console import Console
from rich.panel import Panel

from git_sage.config.settings import get_settings
from git_sage.git.context import get_repo, get_commit_details
from git_sage.output.console import error_panel
from git_sage.output.spinners import sage_spinner

console = Console()


def explain(
    sha: str = typer.Argument(help="Commit SHA or reference (e.g., HEAD, abc123, HEAD~3)."),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Include motivation analysis."
    ),
) -> None:
    """Explain any commit in plain English, including what and why."""
    settings = get_settings()

    repo = get_repo()
    if repo is None:
        console.print(error_panel("Not a Git repository."))
        raise typer.Exit(code=1)

    # ── Get commit details ──────────────────────────────────────
    commit_info = get_commit_details(repo, sha)
    if commit_info is None:
        console.print(error_panel(f"Commit [bold]{sha}[/] not found."))
        raise typer.Exit(code=1)

    # ── Generate explanation ────────────────────────────────────
    from git_sage.agents.graph import run_explain_pipeline

    with sage_spinner(f"Analyzing commit {commit_info['short_sha']}..."):
        explanation = run_explain_pipeline(
            commit_info=commit_info,
            verbose=verbose,
            settings=settings,
        )

    # ── Display ─────────────────────────────────────────────────
    console.print(
        Panel(
            explanation,
            title=f"[bold]📖 Commit {commit_info['short_sha']}[/] — {commit_info['subject']}",
            border_style="blue",
            padding=(1, 2),
        )
    )

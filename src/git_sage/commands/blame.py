"""git-sage blame — Trace a runtime error to the responsible commit."""

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from git_sage.config.settings import get_settings
from git_sage.git.context import get_repo, get_recent_log
from git_sage.output.console import error_panel
from git_sage.output.spinners import sage_spinner

console = Console()


def blame(
    error: str = typer.Argument(help="The error message to trace (e.g., 'TypeError: ...')"),
    file: Optional[str] = typer.Option(
        None, "--file", "-f", help="Restrict search to a specific file."
    ),
    fix: bool = typer.Option(False, "--fix", help="Include a fix suggestion."),
    depth: int = typer.Option(
        20, "--depth", "-n", help="Number of recent commits to search through."
    ),
) -> None:
    """Trace a runtime error back to the commit most likely responsible."""
    settings = get_settings()

    repo = get_repo()
    if repo is None:
        console.print(error_panel("Not a Git repository."))
        raise typer.Exit(code=1)

    # ── Gather recent commit history ────────────────────────────
    with sage_spinner(f"Searching last {depth} commits..."):
        log_data = get_recent_log(repo, max_count=depth, file_path=file)

    if not log_data:
        console.print(error_panel("No commits found in the specified range."))
        raise typer.Exit(code=1)

    # ── Run AI blame analysis ───────────────────────────────────
    from git_sage.agents.graph import run_blame_pipeline

    with sage_spinner("AI analyzing commit history for the error source..."):
        result = run_blame_pipeline(
            error_message=error,
            log_data=log_data,
            include_fix=fix,
            settings=settings,
        )

    # ── Display results ─────────────────────────────────────────
    console.print(
        Panel(
            result,
            title="[bold]🔎 AI Blame Result[/]",
            border_style="yellow",
            padding=(1, 2),
        )
    )

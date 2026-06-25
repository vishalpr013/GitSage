"""git-sage commit — Generate semantic commit messages."""

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from git_sage.config.settings import get_settings
from git_sage.git.context import get_staged_diff, get_repo, run_git_commit
from git_sage.output.console import error_panel, info_panel
from git_sage.output.spinners import sage_spinner

console = Console()


def commit(
    style: str = typer.Option(
        "conventional",
        "--style",
        "-s",
        help="Commit message style: conventional, descriptive, emoji.",
    ),
    prefix: Optional[str] = typer.Option(
        None, "--prefix", "-p", help="Custom prefix for the commit message."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d", help="Preview the commit message without committing."
    ),
) -> None:
    """Generate a semantic commit message from staged changes using AI."""
    settings = get_settings()

    # ── Validate git repo ───────────────────────────────────────
    repo = get_repo()
    if repo is None:
        console.print(error_panel("Not a Git repository."))
        raise typer.Exit(code=1)

    # ── Get staged diff ─────────────────────────────────────────
    diff_text = get_staged_diff(repo)
    if not diff_text or diff_text.strip() == "":
        console.print(info_panel("No staged changes. Stage files with [bold]git add[/] first."))
        raise typer.Exit()

    # ── Generate commit message ─────────────────────────────────
    from git_sage.agents.graph import run_commit_pipeline

    with sage_spinner("Generating commit message..."):
        message = run_commit_pipeline(
            diff_text=diff_text,
            style=style,
            prefix=prefix,
            settings=settings,
        )

    # ── Display the generated message ───────────────────────────
    console.print(
        Panel(
            message,
            title="[bold green]💬 Generated Commit Message[/]",
            border_style="green",
            padding=(1, 2),
        )
    )

    if dry_run:
        console.print("[dim]Dry run — commit was not created.[/]")
        return

    # ── Ask for confirmation ────────────────────────────────────
    if Confirm.ask("\n[bold]Use this commit message?[/]", default=True):
        run_git_commit(repo, message)
        console.print("[bold green]✓[/] Commit created successfully!")
    else:
        console.print("[dim]Commit aborted.[/]")

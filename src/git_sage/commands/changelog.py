"""git-sage changelog — Generate changelog from Git history."""

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from git_sage.config.settings import get_settings
from git_sage.git.context import get_repo, get_log_between
from git_sage.output.console import error_panel
from git_sage.output.spinners import sage_spinner

console = Console()


def changelog(
    from_ref: Optional[str] = typer.Option(
        None, "--from", help="Start reference (tag/commit). Defaults to last tag."
    ),
    to_ref: Optional[str] = typer.Option(
        None, "--to", help="End reference. Defaults to HEAD."
    ),
    format: str = typer.Option(
        "markdown", "--format", "-f", help="Output format: markdown, json, keep-a-changelog."
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Write changelog to a file instead of stdout."
    ),
) -> None:
    """Generate categorized release notes from Git history using AI."""
    settings = get_settings()

    repo = get_repo()
    if repo is None:
        console.print(error_panel("Not a Git repository."))
        raise typer.Exit(code=1)

    # ── Get commit log ──────────────────────────────────────────
    with sage_spinner("Reading commit history..."):
        log_data = get_log_between(repo, from_ref=from_ref, to_ref=to_ref or "HEAD")

    if not log_data:
        console.print(error_panel("No commits found in the specified range."))
        raise typer.Exit(code=1)

    console.print(f"  [dim]Found {len(log_data)} commits to process.[/]\n")

    # ── Generate changelog ──────────────────────────────────────
    from git_sage.agents.graph import run_changelog_pipeline

    with sage_spinner("Generating changelog..."):
        changelog_text = run_changelog_pipeline(
            log_data=log_data,
            output_format=format,
            settings=settings,
        )

    # ── Output ──────────────────────────────────────────────────
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(changelog_text)
        console.print(f"[bold green]✓[/] Changelog written to [cyan]{output}[/]")
    else:
        console.print(
            Panel(
                changelog_text,
                title="[bold]📋 Changelog[/]",
                border_style="magenta",
                padding=(1, 2),
            )
        )

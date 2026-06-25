"""git-sage review — Review staged changes with AI agents."""

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from git_sage.config.settings import get_settings
from git_sage.git.context import get_staged_diff, get_repo
from git_sage.git.diff_parser import parse_diff
from git_sage.output.console import error_panel, info_panel, success_panel
from git_sage.output.spinners import sage_spinner

console = Console()


def review(
    fix: bool = typer.Option(False, "--fix", "-f", help="Auto-fix detected issues after approval."),
    severity: Optional[str] = typer.Option(
        None, "--severity", "-s", help="Minimum severity to report: critical, warning, info."
    ),
    agents: Optional[str] = typer.Option(
        None, "--agents", "-a", help="Comma-separated list of agents to run (e.g., bug,security)."
    ),
    fast: bool = typer.Option(False, "--fast", help="Fast mode: only run Bug + Security agents."),
    estimate: bool = typer.Option(
        False, "--estimate", "-e", help="Show estimated cost before running."
    ),
) -> None:
    """Review staged changes with AI-powered multi-agent analysis."""
    settings = get_settings()

    # ── Validate we're in a git repo ────────────────────────────
    repo = get_repo()
    if repo is None:
        console.print(error_panel("Not a Git repository. Run this command inside a Git repo."))
        raise typer.Exit(code=1)

    # ── Get staged diff ─────────────────────────────────────────
    with sage_spinner("Reading staged changes..."):
        diff_text = get_staged_diff(repo)

    if not diff_text or diff_text.strip() == "":
        console.print(
            info_panel("No staged changes found. Stage files with [bold]git add[/] first.")
        )
        raise typer.Exit()

    # ── Parse diff ──────────────────────────────────────────────
    diff_chunks = parse_diff(diff_text)
    total_files = len(diff_chunks)
    total_lines = sum(chunk["additions"] + chunk["deletions"] for chunk in diff_chunks)

    console.print(
        Panel(
            Text.from_markup(
                f"Analyzing [bold cyan]{total_files}[/] file(s) • "
                f"[green]+{sum(c['additions'] for c in diff_chunks)}[/] "
                f"[red]-{sum(c['deletions'] for c in diff_chunks)}[/] lines"
            ),
            title="[bold]🧙 git-sage review[/]",
            border_style="cyan",
        )
    )

    # ── Determine which agents to run ───────────────────────────
    if fast:
        agent_list = ["bug", "security"]
    elif agents:
        agent_list = [a.strip().lower() for a in agents.split(",")]
    else:
        agent_list = [a for a in settings.agents.enabled]

    console.print(
        f"  [dim]Agents:[/] {', '.join(f'[bold]{a}[/]' for a in agent_list)}\n"
    )

    # ── Run the agent pipeline ──────────────────────────────────
    from git_sage.agents.graph import run_review_pipeline

    with sage_spinner("Running AI review agents..."):
        verdict = run_review_pipeline(
            diff_text=diff_text,
            diff_chunks=diff_chunks,
            agent_list=agent_list,
            settings=settings,
        )

    # ── Render results ──────────────────────────────────────────
    from git_sage.output.review_report import render_verdict

    render_verdict(verdict, severity_filter=severity)

    # ── Handle fix request ──────────────────────────────────────
    if fix and verdict and not verdict.commit_allowed:
        from git_sage.commands.fix import run_fix_flow

        run_fix_flow(verdict, diff_text, repo, settings)
    elif verdict and verdict.commit_allowed:
        console.print(success_panel("All clear! You can commit your changes."))

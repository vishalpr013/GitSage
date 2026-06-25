"""git-sage CLI entry point.

This is the main Typer application that registers all subcommands.
"""

import sys
import os

import typer
from rich.console import Console

from git_sage import __version__
from git_sage.commands import review, commit, explain, blame, changelog, config_cmd

# ── Fix Windows console encoding ───────────────────────────────
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# ── Main Typer app ──────────────────────────────────────────────
app = typer.Typer(
    name="git-sage",
    help="git-sage -- AI-Powered Git Assistant",
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=False,
)

console = Console()

# ── Register subcommands ────────────────────────────────────────
app.command(name="review", help="Review staged changes with AI agents")(review.review)
app.command(name="commit", help="Generate a semantic commit message")(commit.commit)
app.command(name="explain", help="Explain a commit in plain English")(explain.explain)
app.command(name="blame", help="Trace an error to the responsible commit")(blame.blame)
app.command(name="changelog", help="Generate changelog from Git history")(changelog.changelog)
app.command(name="config", help="Manage git-sage settings")(config_cmd.config)


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(
        False, "--version", "-v", help="Show git-sage version and exit."
    ),
) -> None:
    """git-sage -- AI-Powered Git Assistant.

    Analyze staged changes, review code, generate commits, trace bugs,
    and create changelogs -- all from the terminal.
    """
    if version:
        console.print(f"[bold cyan]git-sage[/] version [green]{__version__}[/]")
        raise typer.Exit()


if __name__ == "__main__":
    app()

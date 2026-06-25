"""git-sage config — Manage git-sage settings."""

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from git_sage.config.settings import get_settings, get_config_path

console = Console()


def config(
    action: str = typer.Argument(
        "show", help="Action: show, set, path."
    ),
    key: Optional[str] = typer.Argument(None, help="Config key (e.g., llm.model)."),
    value: Optional[str] = typer.Argument(None, help="Value to set."),
) -> None:
    """View or update git-sage configuration."""
    if action == "show":
        _show_config()
    elif action == "set":
        if key is None or value is None:
            console.print("[red]Usage:[/] git-sage config set <key> <value>")
            raise typer.Exit(code=1)
        _set_config(key, value)
    elif action == "path":
        config_path = get_config_path()
        console.print(f"[bold]Config file:[/] {config_path}")
    else:
        console.print(f"[red]Unknown action:[/] {action}. Use: show, set, path.")
        raise typer.Exit(code=1)


def _show_config() -> None:
    """Display the current configuration."""
    settings = get_settings()
    import json

    config_dict = settings.model_dump()
    config_json = json.dumps(config_dict, indent=2, default=str)

    console.print(
        Panel(
            Syntax(config_json, "json", theme="monokai", line_numbers=False),
            title="[bold]⚙️  git-sage Configuration[/]",
            border_style="cyan",
        )
    )


def _set_config(key: str, value: str) -> None:
    """Set a configuration value."""
    # For now, guide the user to edit the config file directly
    config_path = get_config_path()
    console.print(f"[yellow]⚠[/]  Direct config editing is coming soon.")
    console.print(f"    For now, edit [cyan]{config_path}[/] directly.")
    console.print(f"    Key: [bold]{key}[/] → Value: [bold]{value}[/]")

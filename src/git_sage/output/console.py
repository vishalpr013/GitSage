"""Console helpers — reusable Rich panels and formatting."""

from rich.panel import Panel
from rich.text import Text


def error_panel(message: str) -> Panel:
    """Create a red error panel."""
    return Panel(
        Text.from_markup(f"[bold red]✗[/]  {message}"),
        border_style="red",
        padding=(0, 1),
    )


def success_panel(message: str) -> Panel:
    """Create a green success panel."""
    return Panel(
        Text.from_markup(f"[bold green]✓[/]  {message}"),
        border_style="green",
        padding=(0, 1),
    )


def info_panel(message: str) -> Panel:
    """Create a blue info panel."""
    return Panel(
        Text.from_markup(f"[bold blue]ℹ[/]  {message}"),
        border_style="blue",
        padding=(0, 1),
    )


def warning_panel(message: str) -> Panel:
    """Create a yellow warning panel."""
    return Panel(
        Text.from_markup(f"[bold yellow]⚠[/]  {message}"),
        border_style="yellow",
        padding=(0, 1),
    )

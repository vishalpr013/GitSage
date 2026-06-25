"""Loading spinners for git-sage CLI."""

from contextlib import contextmanager

from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live

console = Console()


@contextmanager
def sage_spinner(message: str = "Working..."):
    """Context manager that shows a spinner with a message.

    Usage:
        with sage_spinner("Analyzing..."):
            do_work()
    """
    spinner = Spinner("dots", text=f"  [cyan]{message}[/]")
    with Live(spinner, console=console, transient=True):
        yield

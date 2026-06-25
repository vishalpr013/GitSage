"""git-sage fix — Interactive fix flow after review."""

from rich.console import Console
from rich.prompt import Confirm

from git_sage.output.spinners import sage_spinner

console = Console()


def run_fix_flow(verdict, diff_text: str, repo, settings) -> None:
    """Run the interactive fix flow after a failed review.

    Shows findings and asks user to approve auto-fixes one by one.
    """
    critical_findings = [f for f in verdict.findings if f.severity == "critical"]
    warning_findings = [f for f in verdict.findings if f.severity == "warning"]

    if not critical_findings and not warning_findings:
        console.print("[dim]No fixable issues found.[/]")
        return

    console.print(
        f"\n[bold yellow]🔧 Fix Agent[/] — "
        f"{len(critical_findings)} critical, {len(warning_findings)} warnings\n"
    )

    # ── Generate fixes ──────────────────────────────────────────
    from git_sage.agents.graph import run_fix_pipeline

    with sage_spinner("Generating fixes..."):
        patches = run_fix_pipeline(
            findings=critical_findings + warning_findings,
            diff_text=diff_text,
            settings=settings,
        )

    if not patches:
        console.print("[dim]Fix agent could not generate patches.[/]")
        return

    # ── Interactive approval ────────────────────────────────────
    for i, patch in enumerate(patches, 1):
        console.print(f"\n[bold]Patch {i}/{len(patches)}:[/]")
        console.print(f"  [cyan]{patch.get('file', 'unknown')}[/]: {patch.get('description', '')}")
        console.print(f"  [dim]{patch.get('diff_preview', '')}[/]")

        if Confirm.ask("  Apply this fix?", default=True):
            from git_sage.git.patch import apply_patch

            success = apply_patch(repo, patch)
            if success:
                console.print("  [bold green]✓[/] Applied.")
            else:
                console.print("  [bold red]✗[/] Failed to apply patch.")
        else:
            console.print("  [dim]Skipped.[/]")

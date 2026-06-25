"""Review report renderer — formats the verdict for terminal display."""

from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from git_sage.agents.state import Verdict, Finding

console = Console()

# ── Agent display config ────────────────────────────────────────
AGENT_ICONS = {
    "bug": "🐛",
    "security": "🔐",
    "style": "✨",
    "complexity": "⚡",
}

SEVERITY_ICONS = {
    "critical": "🚨",
    "warning": "⚠",
    "info": "ℹ",
}

SEVERITY_COLORS = {
    "critical": "bold red",
    "warning": "yellow",
    "info": "dim",
}

STATUS_DISPLAY = {
    "pass": ("[bold green]PASS[/]", "green"),
    "fail": ("[bold red]FAIL[/]", "red"),
    "warn": ("[bold yellow]WARN[/]", "yellow"),
    "error": ("[bold red]ERROR[/]", "red"),
}


def render_verdict(verdict: Optional[Verdict], severity_filter: Optional[str] = None) -> None:
    """Render the full review verdict to the terminal."""
    if verdict is None:
        console.print("[red]No verdict received from the review pipeline.[/]")
        return

    # ── Group findings by agent ─────────────────────────────────
    findings_by_agent: dict[str, list[Finding]] = {}
    for finding in verdict.findings:
        agent = finding.agent
        if agent not in findings_by_agent:
            findings_by_agent[agent] = []
        findings_by_agent[agent].append(finding)

    # ── Render each agent's section ─────────────────────────────
    for agent_name in ["bug", "security", "style", "complexity"]:
        icon = AGENT_ICONS.get(agent_name, "🔹")
        findings = findings_by_agent.get(agent_name, [])

        # Apply severity filter
        if severity_filter:
            severity_order = {"critical": 0, "warning": 1, "info": 2}
            threshold = severity_order.get(severity_filter, 2)
            findings = [f for f in findings if severity_order.get(f.severity, 2) <= threshold]

        # Determine agent status
        if not findings:
            status_text, status_color = STATUS_DISPLAY["pass"]
        elif any(f.severity == "critical" for f in findings):
            status_text, status_color = STATUS_DISPLAY["fail"]
        elif any(f.severity == "warning" for f in findings):
            status_text, status_color = STATUS_DISPLAY["warn"]
        else:
            status_text, status_color = STATUS_DISPLAY["pass"]

        # Agent header
        header = f"{icon} [bold]{agent_name.capitalize()} Agent[/] {'─' * 40} {status_text}"
        console.print(header)

        if not findings:
            console.print("  [green]✓[/] No issues detected.\n")
        else:
            for finding in findings:
                _render_finding(finding)
            console.print()

    # ── Final verdict panel ─────────────────────────────────────
    status_text, status_color = STATUS_DISPLAY.get(
        verdict.overall_status, ("[bold red]ERROR[/]", "red")
    )

    verdict_content = Text.from_markup(
        f"  {status_text} — "
        f"[red]{verdict.critical_count}[/] critical, "
        f"[yellow]{verdict.warning_count}[/] warning, "
        f"[dim]{verdict.info_count}[/] info\n"
        f"  {verdict.summary}\n\n"
        f"  {'[green]✓ Safe to commit.[/]' if verdict.commit_allowed else '[red]✗ Fix issues before committing.[/]'}"
    )

    console.print(
        Panel(
            verdict_content,
            title="[bold]Final Verdict[/]",
            border_style=status_color,
            padding=(1, 2),
        )
    )


def _render_finding(finding: Finding) -> None:
    """Render a single finding."""
    icon = SEVERITY_ICONS.get(finding.severity, "•")
    color = SEVERITY_COLORS.get(finding.severity, "white")

    console.print(
        f"  [{color}]{icon} {finding.file}:{finding.line_start}-{finding.line_end}[/]  "
        f"{finding.message}"
    )
    if finding.suggestion:
        console.print(f"    [dim]→ {finding.suggestion}[/]")
    if finding.confidence < 1.0:
        console.print(f"    [dim]Confidence: {finding.confidence:.0%}[/]")

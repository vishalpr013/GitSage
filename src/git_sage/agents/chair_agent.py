"""Chair Agent — Aggregates all agent findings and produces the final verdict."""

from __future__ import annotations

import json

from langchain_core.messages import SystemMessage, HumanMessage

from git_sage.agents.state import AgentReport, Verdict, ReviewState
from git_sage.llm.provider import get_llm

SYSTEM_PROMPT = """You are the Chair Agent — the final decision-maker in a code review pipeline.

You receive reports from multiple specialized agents (Bug, Security, Style, Complexity).
Your job is to:

1. **Aggregate** all findings from all agents
2. **Deduplicate** — remove redundant findings that overlap between agents
3. **Prioritize** — rank findings by severity (critical > warning > info)
4. **Reconcile conflicts** — if agents disagree, use your judgment
5. **Produce a final verdict**:
   - "fail" — if ANY critical issues exist
   - "warn" — if warnings exist but no criticals
   - "pass" — if only info-level or no issues

## Rules
- Preserve all critical and warning findings from agents
- You may downgrade or remove findings you believe are false positives
- Set commit_allowed = True only if overall_status is "pass" or "warn"
- Set commit_allowed = False if overall_status is "fail"
- Write a concise executive summary (2-3 sentences max)
- Count findings accurately by severity level

## Output
Return a Verdict with all aggregated findings and your decision."""


def chair_agent_node(state: ReviewState) -> dict:
    """Aggregate agent reports and produce the final verdict."""
    llm = get_llm()
    structured_llm = llm.with_structured_output(Verdict)

    agent_reports = state.get("agent_reports", [])

    if not agent_reports:
        return {
            "verdict": Verdict(
                overall_status="pass",
                critical_count=0,
                warning_count=0,
                info_count=0,
                summary="No agent reports received.",
                findings=[],
                commit_allowed=True,
            )
        }

    # Serialize agent reports for the LLM
    reports_text = ""
    for report in agent_reports:
        if isinstance(report, AgentReport):
            report_dict = report.model_dump()
        else:
            report_dict = report
        reports_text += f"\n--- {report_dict.get('agent_name', 'unknown')} Agent ---\n"
        reports_text += json.dumps(report_dict, indent=2, default=str)
        reports_text += "\n"

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"Here are the agent reports. Produce the final verdict:\n{reports_text}"
        ),
    ]

    try:
        verdict: Verdict = structured_llm.invoke(messages)
    except Exception as e:
        # Fallback: manually aggregate without LLM
        verdict = _manual_aggregate(agent_reports, str(e))

    return {"verdict": verdict}


def _manual_aggregate(reports: list[AgentReport], error_msg: str) -> Verdict:
    """Fallback aggregation if the Chair LLM call fails."""
    all_findings = []
    for report in reports:
        if isinstance(report, AgentReport):
            all_findings.extend(report.findings)

    critical = [f for f in all_findings if f.severity == "critical"]
    warnings = [f for f in all_findings if f.severity == "warning"]
    infos = [f for f in all_findings if f.severity == "info"]

    if critical:
        status = "fail"
    elif warnings:
        status = "warn"
    else:
        status = "pass"

    return Verdict(
        overall_status=status,
        critical_count=len(critical),
        warning_count=len(warnings),
        info_count=len(infos),
        summary=f"Aggregated {len(all_findings)} findings (Chair LLM unavailable: {error_msg})",
        findings=sorted(
            all_findings,
            key=lambda f: {"critical": 0, "warning": 1, "info": 2}.get(f.severity, 3),
        ),
        commit_allowed=status != "fail",
    )

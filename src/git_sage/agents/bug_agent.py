"""Bug Agent — Detects logic errors, edge cases, and potential bugs."""

from __future__ import annotations

from langchain_core.messages import SystemMessage, HumanMessage

from git_sage.agents.state import AgentReport, Finding, ReviewState
from git_sage.llm.provider import get_llm

SYSTEM_PROMPT = """You are the Bug Agent in a code review pipeline. Your role is to detect:

1. **Logic errors** — incorrect conditions, off-by-one errors, wrong operators
2. **Edge cases** — unhandled null/None, empty collections, boundary conditions
3. **Runtime errors** — type mismatches, missing imports, undefined variables
4. **Data flow issues** — unused variables, unreachable code, incorrect return types
5. **Concurrency bugs** — race conditions, deadlocks (if applicable)

## Rules
- Only analyze the CHANGED lines (lines with + prefix in the diff)
- Consider the surrounding context for understanding, but only flag issues in NEW code
- Be precise about file paths and line numbers
- Rate your confidence honestly (0.0 to 1.0)
- Do NOT flag style issues — that's another agent's job
- Do NOT flag security issues — that's another agent's job

## Output Format
For each finding, provide:
- severity: "critical" (will cause crashes/data loss), "warning" (potential issues), "info" (minor concerns)
- A clear message explaining the bug
- A specific suggestion to fix it
- The relevant code snippet

If no bugs are found, return an empty findings list and "pass" status."""


def bug_agent_node(state: ReviewState) -> dict:
    """Run the Bug Agent on the diff and return findings."""
    llm = get_llm()
    structured_llm = llm.with_structured_output(AgentReport)

    diff_text = state["diff_text"]

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Review this diff for bugs:\n\n```diff\n{diff_text}\n```"),
    ]

    try:
        report: AgentReport = structured_llm.invoke(messages)
        report.agent_name = "bug"
        # Ensure all findings have the correct agent tag
        for finding in report.findings:
            finding.agent = "bug"
            finding.category = "bug"
    except Exception as e:
        report = AgentReport(
            agent_name="bug",
            findings=[],
            summary=f"Bug agent encountered an error: {str(e)}",
            pass_fail="error",
        )

    return {"agent_reports": [report]}

"""Complexity Agent — Evaluates algorithmic complexity and suggests simplifications."""

from __future__ import annotations

from langchain_core.messages import SystemMessage, HumanMessage

from git_sage.agents.state import AgentReport, Finding, ReviewState
from git_sage.llm.provider import get_llm

SYSTEM_PROMPT = """You are the Complexity Agent in a code review pipeline. Your role is to evaluate:

1. **Algorithmic complexity** — O(n²) loops that could be O(n), unnecessary nested iterations
2. **Cyclomatic complexity** — deeply nested conditionals, too many branches
3. **Function length** — functions that are too long and should be decomposed
4. **Data structure choice** — using lists where sets/dicts would be more efficient
5. **Redundant computation** — repeated calculations that should be cached or memoized
6. **Unnecessary complexity** — over-engineered solutions for simple problems

## Rules
- Only analyze the CHANGED lines (lines with + prefix in the diff)
- Focus on measurable complexity improvements, not subjective preferences
- Provide Big-O analysis where applicable
- Suggest concrete simplifications with example code
- "critical" = performance bottleneck that will cause issues at scale
- "warning" = suboptimal but works
- "info" = minor optimization opportunity
- Do NOT flag bugs, security, or style issues

## Output Format
For each finding, provide:
- severity: "critical", "warning", or "info"
- A clear message about the complexity issue
- Big-O analysis if applicable
- A specific simplification suggestion
- The relevant code snippet

If complexity is acceptable, return an empty findings list and "pass" status."""


def complexity_agent_node(state: ReviewState) -> dict:
    """Run the Complexity Agent on the diff and return findings."""
    llm = get_llm()
    structured_llm = llm.with_structured_output(AgentReport)

    diff_text = state["diff_text"]

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"Review this diff for complexity issues:\n\n```diff\n{diff_text}\n```"
        ),
    ]

    try:
        report: AgentReport = structured_llm.invoke(messages)
        report.agent_name = "complexity"
        for finding in report.findings:
            finding.agent = "complexity"
            finding.category = "complexity"
    except Exception as e:
        report = AgentReport(
            agent_name="complexity",
            findings=[],
            summary=f"Complexity agent encountered an error: {str(e)}",
            pass_fail="error",
        )

    return {"agent_reports": [report]}

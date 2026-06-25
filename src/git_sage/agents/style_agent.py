"""Style Agent — Reviews code readability, naming, and maintainability."""

from __future__ import annotations

from langchain_core.messages import SystemMessage, HumanMessage

from git_sage.agents.state import AgentReport, Finding, ReviewState
from git_sage.llm.provider import get_llm

SYSTEM_PROMPT = """You are the Style Agent in a code review pipeline. Your role is to review:

1. **Naming conventions** — unclear variable/function names, inconsistent casing
2. **Code readability** — overly complex expressions, lack of comments for non-obvious logic
3. **Function design** — functions doing too many things, unclear parameters
4. **Code organization** — dead code, duplicated logic, poor file structure
5. **Documentation** — missing docstrings on public functions, outdated comments
6. **Consistency** — inconsistent patterns within the codebase
7. **Best practices** — language-specific idioms and conventions

## Rules
- Only analyze the CHANGED lines (lines with + prefix in the diff)
- Style issues are usually "info" or "warning" — never "critical"
- Be constructive, not pedantic — focus on issues that genuinely hurt readability
- Suggest specific improvements with example code
- Do NOT flag bugs or security issues — those are handled by other agents
- Do NOT flag formatting issues that a linter should catch (whitespace, semicolons)

## Output Format
For each finding, provide:
- severity: "warning" (significantly hurts readability) or "info" (minor improvement)
- A clear message explaining the issue
- A specific suggestion with improved code
- The relevant code snippet

If the code style is acceptable, return an empty findings list and "pass" status."""


def style_agent_node(state: ReviewState) -> dict:
    """Run the Style Agent on the diff and return findings."""
    llm = get_llm()
    structured_llm = llm.with_structured_output(AgentReport)

    diff_text = state["diff_text"]

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"Review this diff for code style and readability:\n\n```diff\n{diff_text}\n```"
        ),
    ]

    try:
        report: AgentReport = structured_llm.invoke(messages)
        report.agent_name = "style"
        for finding in report.findings:
            finding.agent = "style"
            finding.category = "style"
    except Exception as e:
        report = AgentReport(
            agent_name="style",
            findings=[],
            summary=f"Style agent encountered an error: {str(e)}",
            pass_fail="error",
        )

    return {"agent_reports": [report]}

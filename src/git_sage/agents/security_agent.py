"""Security Agent — Identifies vulnerabilities and insecure coding practices."""

from __future__ import annotations

from langchain_core.messages import SystemMessage, HumanMessage

from git_sage.agents.state import AgentReport, Finding, ReviewState
from git_sage.llm.provider import get_llm

SYSTEM_PROMPT = """You are the Security Agent in a code review pipeline. Your role is to detect:

1. **Hardcoded secrets** — API keys, passwords, tokens, private keys in code
2. **Injection vulnerabilities** — SQL injection, command injection, XSS, template injection
3. **Authentication/Authorization flaws** — missing auth checks, insecure session handling
4. **Cryptographic issues** — weak hashing (MD5/SHA1 for passwords), insecure random, hardcoded IVs
5. **Insecure data handling** — sensitive data in logs, unencrypted storage, unsafe deserialization
6. **Dependency risks** — known vulnerable import patterns
7. **Path traversal** — unsanitized file paths from user input
8. **SSRF** — unvalidated URLs in server-side requests

## Rules
- Only analyze the CHANGED lines (lines with + prefix in the diff)
- Security issues are almost always "critical" or "warning" — use "info" sparingly
- Be precise about the vulnerability type and its potential impact
- Suggest the secure alternative, not just "fix it"
- Rate your confidence honestly (0.0 to 1.0)
- Do NOT flag style or logic issues

## Output Format
For each finding, provide:
- severity: "critical" (exploitable vulnerability), "warning" (potential risk), "info" (best practice suggestion)
- A clear message describing the vulnerability
- A specific, secure code suggestion
- The relevant code snippet

If no security issues are found, return an empty findings list and "pass" status."""


def security_agent_node(state: ReviewState) -> dict:
    """Run the Security Agent on the diff and return findings."""
    llm = get_llm()
    structured_llm = llm.with_structured_output(AgentReport)

    diff_text = state["diff_text"]

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"Review this diff for security vulnerabilities:\n\n```diff\n{diff_text}\n```"
        ),
    ]

    try:
        report: AgentReport = structured_llm.invoke(messages)
        report.agent_name = "security"
        for finding in report.findings:
            finding.agent = "security"
            finding.category = "security"
    except Exception as e:
        report = AgentReport(
            agent_name="security",
            findings=[],
            summary=f"Security agent encountered an error: {str(e)}",
            pass_fail="error",
        )

    return {"agent_reports": [report]}

"""Fix Agent — Generates safe code patches to resolve detected issues."""

from __future__ import annotations

import json

from langchain_core.messages import SystemMessage, HumanMessage

from git_sage.agents.state import Finding, FixPatch, ReviewState
from git_sage.llm.provider import get_llm

SYSTEM_PROMPT = """You are the Fix Agent in a code review pipeline. Your role is to generate
safe, minimal code patches that fix issues found by other agents.

## Rules
- Generate the SMALLEST possible fix — don't refactor unrelated code
- Each fix must include the EXACT original code to find and replace
- Only fix critical and warning severity issues
- Explain what each fix does in plain English
- If you're not confident a fix is safe, say so in the description
- NEVER introduce new bugs or change behavior beyond the fix
- Preserve code style and formatting of the original

## Output Format
For each finding, return a FixPatch with:
- file: the file path
- original: the exact original code to find (must match verbatim)
- replacement: the corrected code
- description: what the fix does
- finding_index: which finding this fixes (0-indexed)

If a finding cannot be safely fixed automatically, skip it and explain why."""


def fix_agent_node(findings: list[Finding], diff_text: str, settings) -> list[dict]:
    """Generate fix patches for the given findings."""
    llm = get_llm()

    findings_text = ""
    for i, finding in enumerate(findings):
        findings_text += f"\n--- Finding {i} ---\n"
        if isinstance(finding, Finding):
            findings_text += json.dumps(finding.model_dump(), indent=2, default=str)
        else:
            findings_text += json.dumps(finding, indent=2, default=str)
        findings_text += "\n"

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Generate fixes for these findings:\n{findings_text}\n\n"
                f"Original diff:\n```diff\n{diff_text}\n```"
            )
        ),
    ]

    try:
        # Try structured output first
        structured_llm = llm.with_structured_output(
            FixPatch,
            method="json_mode" if hasattr(llm, "with_structured_output") else None,
        )
        # For multiple patches, we invoke the LLM and parse
        response = llm.invoke(messages)
        content = response.content if hasattr(response, "content") else str(response)

        # Parse the response into patch dicts
        patches = _parse_fix_response(content, findings)
        return patches

    except Exception as e:
        return []


def _parse_fix_response(content: str, findings: list[Finding]) -> list[dict]:
    """Parse the LLM response into patch dicts.

    Attempts to extract JSON from the response, falls back to
    basic text parsing if JSON extraction fails.
    """
    import re

    patches = []

    # Try to find JSON blocks in the response
    json_pattern = r"```json\s*(.*?)\s*```"
    json_matches = re.findall(json_pattern, content, re.DOTALL)

    if json_matches:
        for match in json_matches:
            try:
                data = json.loads(match)
                if isinstance(data, list):
                    patches.extend(data)
                elif isinstance(data, dict):
                    patches.append(data)
            except json.JSONDecodeError:
                continue

    # If no JSON found, try to parse the entire response as JSON
    if not patches:
        try:
            data = json.loads(content)
            if isinstance(data, list):
                patches = data
            elif isinstance(data, dict):
                patches = [data]
        except json.JSONDecodeError:
            pass

    return patches

"""LangGraph pipeline — the main orchestration graph for git-sage.

Supports multiple pipelines:
  - review: parallel agent fan-out → chair agent → verdict
  - commit: diff → commit message generation
  - explain: commit details → plain English explanation
  - blame: error + log → commit identification
  - changelog: commit log → categorized release notes
  - fix: findings → patch generation
"""

from __future__ import annotations

from typing import Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.types import Send

from git_sage.agents.state import (
    AgentReport,
    Finding,
    FixPatch,
    ReviewState,
    Verdict,
)
from git_sage.agents.bug_agent import bug_agent_node
from git_sage.agents.security_agent import security_agent_node
from git_sage.agents.style_agent import style_agent_node
from git_sage.agents.complexity_agent import complexity_agent_node
from git_sage.agents.chair_agent import chair_agent_node
from git_sage.config.settings import Settings
from git_sage.llm.provider import get_llm


# ── Agent node registry ────────────────────────────────────────

AGENT_NODES = {
    "bug": bug_agent_node,
    "security": security_agent_node,
    "style": style_agent_node,
    "complexity": complexity_agent_node,
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REVIEW PIPELINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _route_to_agents(state: ReviewState):
    """Fan-out: send state to each enabled agent in parallel."""
    agent_list = state.get("agent_list", ["bug", "security", "style", "complexity"])
    return [Send(f"{agent}_agent", state) for agent in agent_list if agent in AGENT_NODES]


def _build_review_graph(agent_list: list[str]) -> StateGraph:
    """Build the LangGraph review pipeline with dynamic agent fan-out."""
    graph = StateGraph(ReviewState)

    # Add agent nodes (only enabled ones)
    for agent_name in agent_list:
        if agent_name in AGENT_NODES:
            graph.add_node(f"{agent_name}_agent", AGENT_NODES[agent_name])

    # Add chair node
    graph.add_node("chair_agent", chair_agent_node)

    # Entry: fan-out to all agents
    graph.set_conditional_entry_point(_route_to_agents)

    # All agents → chair
    agent_node_names = [f"{a}_agent" for a in agent_list if a in AGENT_NODES]
    for node_name in agent_node_names:
        graph.add_edge(node_name, "chair_agent")

    graph.add_edge("chair_agent", END)

    return graph


def run_review_pipeline(
    diff_text: str,
    diff_chunks: list[dict],
    agent_list: list[str],
    settings: Settings,
) -> Optional[Verdict]:
    """Execute the full review pipeline and return the verdict."""
    graph = _build_review_graph(agent_list)
    compiled = graph.compile()

    initial_state: ReviewState = {
        "diff_text": diff_text,
        "diff_chunks": diff_chunks,
        "file_context": {},
        "agent_list": agent_list,
        "agent_reports": [],
        "verdict": None,
        "fix_patches": [],
        "commit_message": "",
        "error": None,
    }

    try:
        result = compiled.invoke(initial_state)
        return result.get("verdict")
    except Exception as e:
        # Return an error verdict
        return Verdict(
            overall_status="error",
            critical_count=0,
            warning_count=0,
            info_count=0,
            summary=f"Pipeline error: {str(e)}",
            findings=[],
            commit_allowed=False,
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMIT MESSAGE PIPELINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COMMIT_SYSTEM_PROMPT = """You are a commit message generator. Generate a clear, semantic commit
message from the provided diff.

## Style: {style}
- **conventional**: Use Conventional Commits format (e.g., "feat(auth): add login validation")
  Types: feat, fix, refactor, docs, style, test, perf, ci, build, chore
- **descriptive**: Write a clear, descriptive message (e.g., "Add input validation to login form")
- **emoji**: Use gitmoji (e.g., "✨ Add input validation to login form")

## Rules
- Subject line: max {max_length} characters
- First line is the subject (imperative mood: "Add", not "Added" or "Adds")
- Optionally add a body (blank line after subject) for complex changes
- Focus on WHAT changed and WHY, not HOW
- Be specific — avoid vague messages like "fix bug" or "update code"
{prefix_instruction}

Return ONLY the commit message text — no explanations or markdown."""


def run_commit_pipeline(
    diff_text: str,
    style: str = "conventional",
    prefix: Optional[str] = None,
    settings: Optional[Settings] = None,
) -> str:
    """Generate a semantic commit message from the diff."""
    llm = get_llm()

    prefix_instruction = ""
    if prefix:
        prefix_instruction = f"\n- Start the message with this prefix: {prefix}"

    max_length = settings.commit.max_length if settings else 72

    system = COMMIT_SYSTEM_PROMPT.format(
        style=style,
        max_length=max_length,
        prefix_instruction=prefix_instruction,
    )

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=f"Generate a commit message for this diff:\n\n```diff\n{diff_text}\n```"),
    ]

    response = llm.invoke(messages)
    return response.content.strip().strip("`").strip()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EXPLAIN PIPELINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXPLAIN_SYSTEM_PROMPT = """You are a commit explainer. Explain the given commit in plain English.

## Rules
- Start with a one-sentence summary of what the commit does
- List the key changes made
- Explain WHY the change was likely made (infer from context)
- Use simple, non-technical language where possible
- If verbose mode is on, include deeper analysis of the motivation and potential impact
{verbose_instruction}

Do NOT use markdown headers. Use bullet points and plain text."""


def run_explain_pipeline(
    commit_info: dict,
    verbose: bool = False,
    settings: Optional[Settings] = None,
) -> str:
    """Generate a plain-English explanation of a commit."""
    llm = get_llm()

    verbose_instruction = ""
    if verbose:
        verbose_instruction = "\n- Include: motivation analysis, potential impact, and related patterns"

    system = EXPLAIN_SYSTEM_PROMPT.format(verbose_instruction=verbose_instruction)

    commit_text = (
        f"SHA: {commit_info['sha']}\n"
        f"Author: {commit_info['author']}\n"
        f"Date: {commit_info['date']}\n"
        f"Message: {commit_info['subject']}\n"
        f"Body: {commit_info.get('body', '')}\n"
        f"Files: {', '.join(commit_info.get('files_changed', []))}\n\n"
        f"Diff:\n```diff\n{commit_info['diff'][:5000]}\n```"
    )

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=f"Explain this commit:\n\n{commit_text}"),
    ]

    response = llm.invoke(messages)
    return response.content.strip()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BLAME PIPELINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BLAME_SYSTEM_PROMPT = """You are an AI blame analyzer. Given an error message and recent commit
history with diffs, identify which commit most likely introduced the error.

## Rules
- Analyze each commit's diff to find code changes that could cause the error
- Rank the top 1-3 most likely commits
- Explain your reasoning for each candidate
- Consider: type errors, removed code, changed APIs, new edge cases
- If you can't identify the culprit, say so honestly
{fix_instruction}

Format your response as:
1. **Most likely commit**: [SHA] — [reason]
2. **Second candidate**: [SHA] — [reason] (if applicable)

Then provide a brief analysis of what went wrong."""


def run_blame_pipeline(
    error_message: str,
    log_data: list[dict],
    include_fix: bool = False,
    settings: Optional[Settings] = None,
) -> str:
    """Trace an error to the most likely responsible commit."""
    llm = get_llm()

    fix_instruction = ""
    if include_fix:
        fix_instruction = "\n- After identifying the culprit, suggest a specific code fix"

    system = BLAME_SYSTEM_PROMPT.format(fix_instruction=fix_instruction)

    import json

    log_text = json.dumps(log_data[:10], indent=2, default=str)  # Limit to 10 commits

    messages = [
        SystemMessage(content=system),
        HumanMessage(
            content=(
                f"Error message: {error_message}\n\n"
                f"Recent commits:\n{log_text}"
            )
        ),
    ]

    response = llm.invoke(messages)
    return response.content.strip()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CHANGELOG PIPELINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CHANGELOG_SYSTEM_PROMPT = """You are a changelog generator. From a list of commits, generate
categorized release notes.

## Format: {format}
- **markdown**: Standard markdown with headers and bullet points
- **keep-a-changelog**: Follow https://keepachangelog.com format
- **json**: Structured JSON with categories and entries

## Categories
Group commits into these categories:
- ✨ Added — new features
- 🐛 Fixed — bug fixes
- ♻️ Changed — changes to existing functionality
- 🗑️ Removed — removed features
- ⚡ Performance — performance improvements
- 📚 Documentation — documentation changes
- 🔧 Other — anything that doesn't fit above

## Rules
- Rewrite commit messages into user-friendly descriptions
- Combine related commits into single entries where appropriate
- Skip merge commits and trivial changes (typo fixes, formatting)
- Include the commit SHA (short) in parentheses after each entry
- Order categories by importance (Added > Fixed > Changed > ...)

Return ONLY the changelog content."""


def run_changelog_pipeline(
    log_data: list[dict],
    output_format: str = "markdown",
    settings: Optional[Settings] = None,
) -> str:
    """Generate categorized release notes from commit history."""
    llm = get_llm()

    import json

    system = CHANGELOG_SYSTEM_PROMPT.format(format=output_format)

    commits_text = json.dumps(
        [{"sha": c["short_sha"], "message": c["message"], "author": c.get("author", "")}
         for c in log_data],
        indent=2,
    )

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=f"Generate a changelog from these commits:\n\n{commits_text}"),
    ]

    response = llm.invoke(messages)
    return response.content.strip()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIX PIPELINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_fix_pipeline(
    findings: list[Finding],
    diff_text: str,
    settings: Optional[Settings] = None,
) -> list[dict]:
    """Generate fix patches for the given findings."""
    from git_sage.agents.fix_agent import fix_agent_node

    return fix_agent_node(findings, diff_text, settings)

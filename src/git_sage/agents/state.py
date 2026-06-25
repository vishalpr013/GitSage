"""State schemas and Pydantic models for the agent pipeline.

Defines the shared state that flows through the LangGraph pipeline,
as well as structured output models for each agent.
"""

from __future__ import annotations

import operator
from typing import Annotated, Optional

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


# ── Structured output models ────────────────────────────────────

class Finding(BaseModel):
    """A single issue found by a review agent."""

    agent: str = Field(description="Name of the agent that found this issue (e.g., 'bug', 'security')")
    severity: str = Field(description="Issue severity: 'critical', 'warning', or 'info'")
    category: str = Field(description="Issue category: 'bug', 'security', 'style', or 'complexity'")
    file: str = Field(description="Affected file path")
    line_start: int = Field(description="Start line number of the issue")
    line_end: int = Field(description="End line number of the issue")
    message: str = Field(description="Human-readable description of the issue")
    suggestion: str = Field(description="Recommended fix or improvement")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    code_snippet: str = Field(default="", description="Relevant code snippet if available")


class AgentReport(BaseModel):
    """Output from a single review agent."""

    agent_name: str = Field(description="Name of the agent")
    findings: list[Finding] = Field(default_factory=list, description="List of findings")
    summary: str = Field(description="Brief summary of the agent's assessment")
    pass_fail: str = Field(description="Overall result: 'pass', 'fail', or 'warn'")


class Verdict(BaseModel):
    """Final aggregated verdict from the Chair Agent."""

    overall_status: str = Field(description="Overall result: 'pass', 'fail', or 'warn'")
    critical_count: int = Field(default=0)
    warning_count: int = Field(default=0)
    info_count: int = Field(default=0)
    summary: str = Field(description="Executive summary of the review")
    findings: list[Finding] = Field(default_factory=list, description="All findings, sorted by severity")
    commit_allowed: bool = Field(description="Whether the code is safe to commit")


class FixPatch(BaseModel):
    """A generated fix patch for a finding."""

    file: str = Field(description="File to patch")
    original: str = Field(description="Original code to find")
    replacement: str = Field(description="Replacement code")
    description: str = Field(description="What the fix does")
    finding_index: int = Field(description="Index of the finding this fixes")
    diff_preview: str = Field(default="", description="Unified diff preview of the change")


# ── LangGraph State ─────────────────────────────────────────────

class ReviewState(TypedDict):
    """Shared state for the review pipeline.

    The agent_reports field uses operator.add as a reducer so that
    parallel agents can safely append their reports without overwriting
    each other.
    """

    diff_text: str
    diff_chunks: list[dict]
    file_context: dict[str, str]
    agent_list: list[str]
    agent_reports: Annotated[list[AgentReport], operator.add]
    verdict: Optional[Verdict]
    fix_patches: list[FixPatch]
    commit_message: str
    error: Optional[str]

"""git-sage settings — Pydantic-based configuration with hierarchy.

Config priority (lowest → highest):
  1. Built-in defaults (this file)
  2. Global config (~/.config/git-sage/config.toml)
  3. Project config (.gitsage.toml in repo root)
  4. Environment variables (GITSAGE_*)
  5. CLI flags (handled at the command level)
"""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from dotenv import load_dotenv


# ── Load .env file ──────────────────────────────────────────────
load_dotenv()


# ── Sub-models ──────────────────────────────────────────────────

class LLMSettings(BaseModel):
    """LLM provider configuration."""

    provider: str = Field(default="gemini", description="LLM provider: gemini")
    model: str = Field(
        default="gemini-2.0-flash",
        description="Model name to use.",
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key. Prefer env var GEMINI_API_KEY.",
    )
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, gt=0)


class AgentConfig(BaseModel):
    """Per-agent toggle and settings."""

    enabled: bool = True
    severity_threshold: str = Field(
        default="info",
        description="Minimum severity to report: critical, warning, info.",
    )


class AgentsSettings(BaseModel):
    """Agent pipeline configuration."""

    enabled: list[str] = Field(
        default=["bug", "security", "style", "complexity"],
        description="List of enabled agents.",
    )
    parallel: bool = Field(default=True, description="Run agents in parallel.")
    bug: AgentConfig = AgentConfig()
    security: AgentConfig = AgentConfig()
    style: AgentConfig = AgentConfig()
    complexity: AgentConfig = AgentConfig()


class ReviewSettings(BaseModel):
    """Review command settings."""

    max_diff_lines: int = Field(default=2000, description="Warn if diff exceeds this.")
    auto_fix: bool = Field(default=False, description="Auto-fix without --fix flag.")
    show_cost_estimate: bool = Field(default=True)


class CommitSettings(BaseModel):
    """Commit message generation settings."""

    style: str = Field(default="conventional", description="conventional | descriptive | emoji")
    max_length: int = Field(default=72, description="Max subject line length.")


class ChangelogSettings(BaseModel):
    """Changelog generation settings."""

    categories: list[str] = Field(
        default=["feat", "fix", "refactor", "docs", "perf", "test"],
    )
    format: str = Field(default="keep-a-changelog")


class OutputSettings(BaseModel):
    """Terminal output settings."""

    color: bool = True
    verbose: bool = False


# ── Main settings model ────────────────────────────────────────

class Settings(BaseModel):
    """Root configuration for git-sage."""

    llm: LLMSettings = LLMSettings()
    agents: AgentsSettings = AgentsSettings()
    review: ReviewSettings = ReviewSettings()
    commit: CommitSettings = CommitSettings()
    changelog: ChangelogSettings = ChangelogSettings()
    output: OutputSettings = OutputSettings()


# ── Config loading helpers ──────────────────────────────────────

def _find_project_config() -> Optional[Path]:
    """Walk up from cwd to find .gitsage.toml."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        config_file = parent / ".gitsage.toml"
        if config_file.exists():
            return config_file
    return None


def _find_global_config() -> Optional[Path]:
    """Find global config at ~/.config/git-sage/config.toml."""
    if sys.platform == "win32":
        config_dir = Path(os.environ.get("APPDATA", Path.home())) / "git-sage"
    else:
        config_dir = Path.home() / ".config" / "git-sage"

    config_file = config_dir / "config.toml"
    return config_file if config_file.exists() else None


def _load_toml(path: Path) -> dict:
    """Load a TOML file and return as dict."""
    try:
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib  # type: ignore[no-redef]

        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}


def _merge_dicts(base: dict, override: dict) -> dict:
    """Deep-merge override into base."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def get_config_path() -> str:
    """Return the path to the active config file."""
    project = _find_project_config()
    if project:
        return str(project)
    global_config = _find_global_config()
    if global_config:
        return str(global_config)
    return "(no config file — using defaults)"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and merge settings from all sources.

    Priority: defaults → global TOML → project TOML → env vars.
    """
    config_data: dict = {}

    # 1. Global config
    global_config = _find_global_config()
    if global_config:
        config_data = _merge_dicts(config_data, _load_toml(global_config))

    # 2. Project config
    project_config = _find_project_config()
    if project_config:
        config_data = _merge_dicts(config_data, _load_toml(project_config))

    # 3. Build settings from merged TOML
    settings = Settings(**config_data) if config_data else Settings()

    # 4. Override with environment variables
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        settings.llm.api_key = gemini_key
        settings.llm.provider = "gemini"

    return settings

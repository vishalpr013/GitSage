"""Tests for the configuration system."""

import pytest

from git_sage.config.settings import Settings, LLMSettings, AgentsSettings


class TestSettings:
    """Tests for Settings model."""

    def test_default_settings(self):
        """Should create settings with sensible defaults."""
        settings = Settings()
        assert settings.llm.provider == "gemini"
        assert settings.llm.model == "gemini-2.0-flash"
        assert settings.llm.temperature == 0.1
        assert "bug" in settings.agents.enabled
        assert "security" in settings.agents.enabled

    def test_llm_settings_override(self):
        """Should allow overriding LLM settings."""
        settings = Settings(
            llm=LLMSettings(model="gemini-2.5-pro", temperature=0.5)
        )
        assert settings.llm.model == "gemini-2.5-pro"
        assert settings.llm.temperature == 0.5

    def test_agent_toggle(self):
        """Should allow disabling agents."""
        settings = Settings(
            agents=AgentsSettings(enabled=["bug", "security"])
        )
        assert "style" not in settings.agents.enabled
        assert "bug" in settings.agents.enabled

    def test_temperature_bounds(self):
        """Should enforce temperature bounds."""
        with pytest.raises(Exception):
            LLMSettings(temperature=3.0)

    def test_commit_style_default(self):
        """Should default to conventional commit style."""
        settings = Settings()
        assert settings.commit.style == "conventional"

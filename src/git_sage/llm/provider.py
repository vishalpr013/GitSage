"""LLM provider factory — initializes the chat model based on settings.

Currently supports Gemini only. Designed for easy extension to other providers.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from git_sage.config.settings import Settings


class LLMProviderError(Exception):
    """Raised when LLM provider cannot be initialized."""


@lru_cache(maxsize=1)
def get_llm(settings: Settings | None = None) -> BaseChatModel:
    """Create and return the configured LLM instance.

    Uses Gemini via langchain-google-genai. The model and API key
    are read from settings (which pulls from .env / config files).
    """
    if settings is None:
        from git_sage.config.settings import get_settings
        settings = settings or get_settings()

    provider = settings.llm.provider.lower()

    if provider == "gemini":
        return _create_gemini(settings)
    else:
        raise LLMProviderError(
            f"Unknown LLM provider: '{provider}'. Currently only 'gemini' is supported."
        )


def _create_gemini(settings: Settings) -> BaseChatModel:
    """Initialize Google Gemini via langchain-google-genai."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        raise LLMProviderError(
            "langchain-google-genai is not installed. "
            "Run: pip install langchain-google-genai"
        )

    api_key = settings.llm.api_key
    if not api_key:
        raise LLMProviderError(
            "Gemini API key not found. Set GEMINI_API_KEY in your .env file "
            "or run: git-sage config set llm.api_key <your-key>\n"
            "Get a key at: https://aistudio.google.com/apikey"
        )

    return ChatGoogleGenerativeAI(
        model=settings.llm.model,
        google_api_key=api_key,
        temperature=settings.llm.temperature,
        max_output_tokens=settings.llm.max_tokens,
    )

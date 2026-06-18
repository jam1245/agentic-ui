"""Shared LLM model configuration for the ADK agents.

The agents are Google ADK `LlmAgent`s, but the model is the **internal Genesis** LLM
reached over its OpenAI-compatible chat-completions endpoint via LiteLLM — NOT a Google
cloud model. This is what lets us keep the ADK framework (orchestration, sub-agents, tool
calling) while every token is served by Genesis. No Google API key is ever used.

Mirrors the pattern from the adk-project. Configure entirely via env (.env):

    LLM_MODEL       LiteLLM model string, e.g. "openai/gpt-oss-120b" (provider/model)
    LLM_API_BASE    OpenAI-compatible base URL (defaults to GENESIS_BASE_URL / the LM platform)
    LLM_API_KEY     bearer token for Genesis
    LLM_SSL_VERIFY  "false" to skip TLS verification on internal endpoints (default false)
"""
from __future__ import annotations

import os

from google.adk.models.lite_llm import LiteLlm

DEFAULT_BASE_URL = "https://api.ai.us.lmco.com/v1"


def get_model() -> LiteLlm:
    """Build a LiteLlm model bound to the internal Genesis endpoint."""
    model_name = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    kwargs: dict = {}

    api_base = os.getenv("LLM_API_BASE") or os.getenv("GENESIS_BASE_URL") or DEFAULT_BASE_URL
    if api_base:
        kwargs["api_base"] = api_base

    api_key = os.getenv("LLM_API_KEY")
    if api_key:
        kwargs["api_key"] = api_key

    # Internal endpoints often use self-signed certs; default to NOT verifying.
    if os.getenv("LLM_SSL_VERIFY", "false").lower() in ("false", "0", "no"):
        kwargs["ssl_verify"] = False

    return LiteLlm(model=model_name, **kwargs)

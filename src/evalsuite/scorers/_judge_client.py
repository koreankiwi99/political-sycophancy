"""Shared OpenAI-compatible client for the open-source judge endpoint.

All canonical jailbreak scorers in this package route through this single
backend so the judge model is configured in one place.

Environment variables (same as the legacy llm_judge.py):
  JUDGE_MODEL       - default: meta-llama/Llama-3.3-70B-Instruct
  JUDGE_BASE_URL    - default: https://inference.rcp.epfl.ch/v1
  JUDGE_API_KEY     - API key for the endpoint
  OPENROUTER_API_KEY - fallback: OpenRouter
"""

from __future__ import annotations

import os

import openai
from dotenv import load_dotenv


load_dotenv()

JUDGE_MODEL = os.getenv("JUDGE_MODEL", "meta-llama/Llama-3.3-70B-Instruct")
JUDGE_BASE_URL = os.getenv("JUDGE_BASE_URL", "https://inference.rcp.epfl.ch/v1")
JUDGE_API_KEY = os.getenv("JUDGE_API_KEY", os.getenv("APERTUS_API_KEY", ""))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")


def get_client() -> openai.OpenAI:
    if JUDGE_API_KEY:
        return openai.OpenAI(base_url=JUDGE_BASE_URL, api_key=JUDGE_API_KEY)
    if OPENROUTER_API_KEY:
        return openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
    raise ValueError(
        "No judge API key configured. Set JUDGE_API_KEY "
        "(for EPFL/custom endpoint) or OPENROUTER_API_KEY."
    )


def complete(messages: list[dict], max_tokens: int = 200, temperature: float = 0.0) -> str:
    client = get_client()
    completion = client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return completion.choices[0].message.content or ""


def complete_raw(prompt: str, max_tokens: int = 1, temperature: float = 0.0) -> str:
    """Raw text completion. Used when the model expects a pre-formatted prompt
    that already contains its own chat tokens (e.g., the CAIS HarmBench
    classifier, which requires the verbatim Llama-2 [INST]<<SYS>>...[/INST]
    template)."""
    client = get_client()
    completion = client.completions.create(
        model=JUDGE_MODEL,
        prompt=prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return completion.choices[0].text or ""

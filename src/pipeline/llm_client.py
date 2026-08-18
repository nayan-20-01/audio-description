import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

import httpx

from config.settings import GROQ_API_KEY, GEMINI_API_KEY

logger = logging.getLogger("llm_client")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"
GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)
MAX_RETRIES_PER_PROVIDER = 2
REQUEST_TIMEOUT_SECONDS = 15

SYSTEM_PROMPT = (
    "You convert a LaTeX math expression into clear spoken English, as "
    "if reading it aloud to a student who cannot see the board. Do not "
    "use LaTeX syntax, symbols, or markup in your answer. If the LaTeX "
    "contains a matrix or multiple rows separated by \\\\, treat each "
    "row as a separate equation and describe them as separate sentences "
    "in the same top-to-bottom order they appear — do not merge them or "
    "reorder them. Keep each sentence short. Do not add commentary, "
    "only the spoken description."
)


@dataclass
class LLMResult:
    text: str
    provider: str


class LLMClientError(Exception):
    pass


class _RateLimited(Exception):
    def __init__(self, provider: str):
        self.provider = provider


class _MissingAPIKey(Exception):
    def __init__(self, key_name: str):
        self.key_name = key_name


async def _call_groq(client: httpx.AsyncClient, latex: str) -> str:
    if not GROQ_API_KEY:
        raise LLMClientError("GROQ_API_KEY is not set — add it to your .env file")
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": latex},
        ],
        "temperature": 0.3,
        "max_tokens": 150,
    }
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    response = await client.post(GROQ_API_URL, json=payload, headers=headers,
                                  timeout=REQUEST_TIMEOUT_SECONDS)
    if response.status_code == 429:
        raise _RateLimited("groq")
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


async def _call_gemini(client: httpx.AsyncClient, latex: str) -> str:
    if not GEMINI_API_KEY:
        raise LLMClientError("GEMINI_API_KEY is not set — add it to your .env file")
    payload = {
        "contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\n\nLaTeX: {latex}"}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 150},
    }
    url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
    response = await client.post(url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
    if response.status_code == 429:
        raise _RateLimited("gemini")
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


async def _with_retries(fn, client, latex, provider_name: str) -> Optional[str]:
    for attempt in range(1, MAX_RETRIES_PER_PROVIDER + 1):
        try:
            return await fn(client, latex)
        except LLMClientError as exc:
            logger.error("%s: %s", provider_name, exc)
            return None
        except _RateLimited:
            logger.warning("%s rate limited, failing over", provider_name)
            return None
        except httpx.TimeoutException:
            if attempt == MAX_RETRIES_PER_PROVIDER:
                return None
            await asyncio.sleep(1.5 * attempt)
        except httpx.HTTPStatusError as exc:
            logger.error("%s HTTP error: %s", provider_name, exc)
            return None
    return None


async def latex_to_speech_text(latex: str) -> LLMResult:
    async with httpx.AsyncClient() as client:
        text = await _with_retries(_call_groq, client, latex, "groq")
        if text:
            return LLMResult(text=text, provider="groq")
        text = await _with_retries(_call_gemini, client, latex, "gemini")
        if text:
            return LLMResult(text=text, provider="gemini")
    raise LLMClientError(f"Both providers failed for: {latex[:60]!r}")


async def batch_latex_to_speech_text(latex_list: list[str]) -> list[Optional[LLMResult]]:
    async def _safe_call(latex: str) -> Optional[LLMResult]:
        try:
            return await latex_to_speech_text(latex)
        except LLMClientError as exc:
            logger.error("Segment skipped: %s", exc)
            return None

    return await asyncio.gather(*[_safe_call(latex) for latex in latex_list])

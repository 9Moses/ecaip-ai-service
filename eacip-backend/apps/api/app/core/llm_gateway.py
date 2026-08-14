import logging
import os

import litellm
import time

from app.core.config import get_settings
from collections.abc import AsyncIterator

from app.core.metrics import llm_call_duration_seconds, llm_call_total

logger = logging.getLogger("llm_gateway")
settings = get_settings()

# LiteLLM reads provider credentials from environment variables at call time.
os.environ.setdefault("GEMINI_API_KEY", settings.gemini_api_key)
os.environ.setdefault("GROQ_API_KEY", settings.groq_api_key)
os.environ.setdefault("CEREBRAS_API_KEY", settings.cerebras_api_key)


class LLMGatewayError(Exception):
    """Raised when every provider in the fallback chain has failed."""


async def complete(system_prompt: str, user_prompt: str, purpose: str = "unspecified") -> str:
    """
    Calls the first working provider in the configured fallback chain.
    Returns the raw text response. Callers needing structured output
    are responsible for their own parsing/validation (see Part 2).
    """
    primary_model, *fallback_models = settings.llm_model_fallback_chain
    start_time = time.monotonic()

    try:
        response = await litellm.acompletion(
            model=primary_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            fallbacks=fallback_models,
            timeout=settings.llm_request_timeout_seconds,
        )
    except Exception as exc:
        llm_call_total.labels(provider="unknown", purpose=purpose, status="failure").inc()
        logger.exception("All LLM providers in the fallback chain failed")
        raise LLMGatewayError(str(exc)) from exc

    duration = time.monotonic() - start_time
    provider = response.model.split("/")[0] if "/" in response.model else response.model
    llm_call_duration_seconds.labels(provider=provider, purpose=purpose).observe(duration)
    llm_call_total.labels(provider=provider, purpose=purpose, status="success").inc()

    content = response.choices[0].message.content
    logger.info("LLM call succeeded via model=%s (%.2fs)", response.model, duration)
    return content or ""


async def stream_complete(
    system_prompt: str,
    user_prompt: str,
) -> AsyncIterator[str]:
    """
    Same provider fallback chain as complete(),
    but yields text chunks as they arrive.
    """
    primary_model, *fallback_models = settings.llm_model_fallback_chain

    try:
        response_stream = await litellm.acompletion(
            model=primary_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            fallbacks=fallback_models,
            timeout=settings.llm_request_timeout_seconds,
            stream=True,
        )
        async for chunk in response_stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as exc:  # noqa: BLE001
        logger.exception("Streaming LLM call failed")
        raise LLMGatewayError(str(exc)) from exc

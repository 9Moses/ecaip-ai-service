import logging
import os

import litellm

from app.core.config import get_settings
from collections.abc import AsyncIterator

logger = logging.getLogger("llm_gateway")
settings = get_settings()

# LiteLLM reads provider credentials from environment variables at call time.
os.environ.setdefault("GEMINI_API_KEY", settings.gemini_api_key)
os.environ.setdefault("GROQ_API_KEY", settings.groq_api_key)
os.environ.setdefault("CEREBRAS_API_KEY", settings.cerebras_api_key)


class LLMGatewayError(Exception):
    """Raised when every provider in the fallback chain has failed."""


async def complete(system_prompt: str, user_prompt: str) -> str:
    """
    Calls the first working provider in the configured fallback chain.
    Returns the raw text response. Callers needing structured output
    are responsible for their own parsing/validation (see Part 2).
    """
    primary_model, *fallback_models = settings.llm_model_fallback_chain

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
        logger.exception("All LLM providers in the fallback chain failed")
        raise LLMGatewayError(str(exc)) from exc

    content = response.choices[0].message.content
    logger.info("LLM call succeeded via model=%s", response.model)
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

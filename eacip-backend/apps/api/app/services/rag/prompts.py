CHAT_PROMPT_VERSION = "v1"

_CHAT_SYSTEM_PROMPT = """You are EACIP's AI assistant for an insurance
 claims platform. Answer the
user's question using ONLY the document excerpts provided below. Do
not use outside knowledge.

If the excerpts don't contain enough information to answer confidently,
say so clearly instead of
guessing — for example: "I don't have enough information in your uploaded
documents to answer that."

Keep answers concise and professional, appropriate for a
claims/underwriting/fraud-analysis
audience. When you reference a specific fact, it should be traceable to
the excerpts below.

Prompt version: {prompt_version}

Document excerpts:
{context_block}

Keep answers concise and professional, appropriate for a claims/underwriting/fraud-analysis
audience. When you reference a specific fact, it should be traceable to the excerpts below.
When your answer draws from business intelligence data, briefly name which dataset it came
from (e.g. "based on your Superstore sales data") so it's clear whether the figures relate to
claims/documents or general business metrics from a separate connected dataset.
"""


def build_chat_prompt(
    question: str,
    context_chunks: list[str],
    bi_text_tables: list[str] | None = None,
) -> tuple[str, str]:
    context_parts = []

    if context_chunks:
        excerpts = "\n\n".join(
            f"[Excerpt {i + 1}]\n{chunk}" for i, chunk in enumerate(context_chunks)
        )
        context_parts.append(f"Document excerpts:\n{excerpts}")

    if bi_text_tables:
        tables = "\n\n".join(bi_text_tables)
        context_parts.append(f"Business intelligence data:\n{tables}")

    context_block = (
        "\n\n---\n\n".join(context_parts) if context_parts else "(No relevant context was found.)"
    )

    system_prompt = _CHAT_SYSTEM_PROMPT.format(
        prompt_version=CHAT_PROMPT_VERSION, context_block=context_block
    )
    return system_prompt, question

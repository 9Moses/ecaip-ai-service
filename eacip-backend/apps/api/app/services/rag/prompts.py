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
"""


def build_chat_prompt(question: str, context_chunks: list[str]) -> tuple[str, str]:
    if not context_chunks:
        context_block = "(No relevant document excerpts were found.)"
    else:
        context_block = "\n\n".join(
            f"[Excerpt {i + 1}]\n{chunk}" for i, chunk in enumerate(context_chunks)
        )

    system_prompt = _CHAT_SYSTEM_PROMPT.format(
        prompt_version=CHAT_PROMPT_VERSION, context_block=context_block
    )
    return system_prompt, question

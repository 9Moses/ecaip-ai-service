from dataclasses import dataclass

from app.core.config import get_settings

settings = get_settings()


@dataclass
class Chunk:
    text: str
    chunk_index: int


def _approx_token_count(text: str) -> int:
    # A word-count-based approximation
    # (~0.75 tokens per word for English)  is good
    # enough for chunk-sizing purposes and avoids
    # adding a tokenizer dependency
    # just for this. Not used anywhere that requires
    # exact token accounting.
    return int(len(text.split()) / 0.75)


def chunk_text(raw_text: str) -> list[Chunk]:
    paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    chunks: list[Chunk] = []
    current_paragraphs: list[str] = []
    current_tokens = 0

    def flush_chunk() -> None:
        if current_paragraphs:
            chunks.append(Chunk(text="\n\n".join(current_paragraphs), chunk_index=len(chunks)))

    for paragraph in paragraphs:
        paragraph_tokens = _approx_token_count(paragraph)

        # A single paragraph larger than the target on its own:
        # split it by sentence
        # as a fallback, rather than producing one oversized chunk.
        if paragraph_tokens > settings.chunk_target_tokens:
            flush_chunk()
            current_paragraphs = []
            current_tokens = 0
            chunks.extend(_split_oversized_paragraph(paragraph, len(chunks)))
            continue

        if current_tokens + paragraph_tokens > settings.chunk_target_tokens and current_paragraphs:
            flush_chunk()
            # Overlap: carry the last paragraph forward into the next
            # chunk for context continuity
            overlap_paragraphs = (
                current_paragraphs[-1:]
                if _approx_token_count(current_paragraphs[-1]) <= settings.chunk_overlap_tokens
                else []
            )
            current_paragraphs = overlap_paragraphs
            current_tokens = sum(_approx_token_count(p) for p in current_paragraphs)

        current_paragraphs.append(paragraph)
        current_tokens += paragraph_tokens

    flush_chunk()
    return chunks


def _split_oversized_paragraph(paragraph: str, start_index: int) -> list[Chunk]:
    sentences = paragraph.replace("\n", " ").split(". ")
    result: list[Chunk] = []
    current: list[str] = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = _approx_token_count(sentence)
        if current_tokens + sentence_tokens > get_settings().chunk_target_tokens and current:
            result.append(
                Chunk(text=". ".join(current) + ".", chunk_index=start_index + len(result))
            )
            current = []
            current_tokens = 0
        current.append(sentence)
        current_tokens += sentence_tokens

    if current:
        result.append(Chunk(text=". ".join(current), chunk_index=start_index + len(result)))

    return result

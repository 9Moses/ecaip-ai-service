import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db, async_session_factory
from app.core.security import get_current_user
from app.core.llm_gateway import stream_complete
from app.models.chat import ChatMessage, ChatSession
from app.models.user import User
from app.schemas.chat import ChatMessageResponse, ChatSessionResponse, SendMessageRequest
from app.services.rag.context import assemble_context
from app.services.rag.prompts import build_chat_prompt
from app.services.bi.formatting import format_as_text_table, to_chart_data

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatSessionResponse:
    session = ChatSession(user_id=user.id)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return ChatSessionResponse.model_validate(session)


@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ChatSessionResponse]:
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.created_at.desc())
    )
    return [ChatSessionResponse.model_validate(s) for s in result.scalars().all()]


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
async def get_messages(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ChatMessageResponse]:
    session = await db.scalar(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user.id)
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    return [ChatMessageResponse.model_validate(m) for m in result.scalars().all()]


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: uuid.UUID,
    payload: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    session = await db.scalar(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user.id)
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    user_message = ChatMessage(session_id=session_id, role="user", content=payload.content)
    db.add(user_message)
    await db.commit()

    context = await assemble_context(payload.content, user.id, db)

    bi_text_tables = [format_as_text_table(r) for r in context.bi_results]
    system_prompt, user_prompt = build_chat_prompt(
        payload.content, [c.text for c in context.chunks], bi_text_tables
    )

    sources = [
        {
            "document_id": c.document_id,
            "chunk_index": c.chunk_index,
            "relevance_score": round(c.score, 3),
        }
        for c in context.chunks
    ]
    chart_data = [to_chart_data(r) for r in context.bi_results]

    async def event_stream() -> AsyncIterator[str]:
        full_response_parts: list[str] = []

        if context.notice:
            notice_event = json.dumps({"type": "notice", "content": context.notice})
            yield f"data: {notice_event}\n\n"

        try:
            async for delta in stream_complete(system_prompt, user_prompt):
                full_response_parts.append(delta)
                yield f"data: {json.dumps({'type': 'delta', 'content': delta})}\n\n"
        except Exception:  # noqa: BLE001
            error_text = """
            I'm having trouble reaching the AI service right now.
            Please try again shortly.
            """
            full_response_parts.append(error_text)
            yield f"data: {json.dumps({'type': 'delta', 'content': error_text})}\n\n"

        final_content = "".join(full_response_parts)

        # Persist the assistant's full message + sources using a fresh session,
        # since the request-scoped `db` session may be in a state we don't want
        # to keep writing to after streaming a long-running response.
        async with async_session_factory() as persist_db:
            assistant_message = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=final_content,
                sources=sources,
                chart_data=chart_data,
            )
            persist_db.add(assistant_message)
            await persist_db.commit()

        done_payload = {"type": "done", "sources": sources, "chart_data": chart_data}
        yield f"data: {json.dumps(done_payload)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

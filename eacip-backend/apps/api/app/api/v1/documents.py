import hashlib
import uuid

import magic
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, UTC

from app.core.db import get_db
from app.core.security import get_current_user
from app.core.storage import upload_file
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.core.queue import publish_extraction_job
from app.schemas.document import DocumentExtractionResponse
from app.models.document_extraction import DocumentExtraction
from app.schemas.ai_extraction import AIExtractionResponse, ConfirmExtractionRequest

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/tiff": "tiff",
}


def _detect_document_type(filename: str) -> str:
    lowered = filename.lower()
    if "claim" in lowered:
        return "claim_form"
    if "invoice" in lowered:
        return "invoice"
    if "medical" in lowered or "report" in lowered:
        return "medical_report"
    if "policy" in lowered:
        return "policy"
    return "other"


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> DocumentResponse:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    mime_type = magic.from_buffer(content, mime=True)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsuppored file type: {mime_type}. Allowed: PDF, JPEG, PNG, TIFF.",
        )

    file_hash = hashlib.sha256(content).hexdigest()

    existing = await db.scalar(
        select(Document).where(Document.owner_id == user.id, Document.file_hash == file_hash)
    )
    if existing:
        if existing.status in ("uploaded", "failed"):
            try:
                await publish_extraction_job(existing.id)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to queue extraction job for existing document.",
                ) from e
        return DocumentResponse.model_validate(existing)

    extension = ALLOWED_MIME_TYPES[mime_type]
    document_id = uuid.uuid4()
    storage_path = f"{user.id}/{document_id}.{extension}"

    try:
        upload_file(storage_path, content)
    except Exception as e:
        print(f"Error uploading file to storage: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to upload file to storage. Please try again.",
        ) from e

    document = Document(
        id=document_id,
        owner_id=user.id,
        file_name=file.filename or f"document.{extension}",
        file_hash=file_hash,
        mime_type=mime_type,
        document_type=_detect_document_type(file.filename or ""),
        storage_path=storage_path,
        status="uploaded",
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    try:
        await publish_extraction_job(document.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Failed to queue extraction job. The document is processing "
                "but extraction hasn't started."
            ),
        ) from e

    return DocumentResponse.model_validate(document)


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> list[DocumentResponse]:
    result = await db.execute(
        select(Document).where(Document.owner_id == user.id).order_by(Document.created_at.desc())
    )
    return [DocumentResponse.model_validate(d) for d in result.scalars().all()]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DocumentResponse:
    document = await db.scalar(
        select(Document).where(Document.id == document_id, Document.owner_id == user.id)
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentResponse.model_validate(document)


@router.get("/{document_id}/extraction", response_model=DocumentExtractionResponse)
async def get_document_extraction(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DocumentExtractionResponse:
    try:
        document = await db.scalar(
            select(Document).where(Document.id == document_id, Document.owner_id == user.id)
        )
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

        return DocumentExtractionResponse.model_validate(document)

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch document extraction.",
        ) from exc


@router.get("/{document_id}/ai-extraction", response_model=AIExtractionResponse)
async def get_ai_extraction(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIExtractionResponse:
    document = await db.scalar(
        select(Document).where(Document.id == document_id, Document.owner_id == user.id)
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    extraction = await db.scalar(
        select(DocumentExtraction).where(DocumentExtraction.document_id == document_id)
    )
    if extraction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI extraction has not started yet for this document",
        )
    return AIExtractionResponse.model_validate(extraction)


@router.post("/{document_id}/ai-extraction/confirm", response_model=AIExtractionResponse)
async def confirm_ai_extraction(
    document_id: uuid.UUID,
    payload: ConfirmExtractionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIExtractionResponse:
    document = await db.scalar(
        select(Document).where(Document.id == document_id, Document.owner_id == user.id)
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    extraction = await db.scalar(
        select(DocumentExtraction).where(DocumentExtraction.document_id == document_id)
    )
    if extraction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No AI extraction found to confirm"
        )

    extraction.extracted_fields = payload.extracted_fields
    extraction.confirmed_by = user.id
    extraction.confirmed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(extraction)

    return AIExtractionResponse.model_validate(extraction)

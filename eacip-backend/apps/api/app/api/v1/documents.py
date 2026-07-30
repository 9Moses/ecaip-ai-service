from fastapi import APIRouter

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

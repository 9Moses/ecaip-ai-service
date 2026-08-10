import pytest
from unittest.mock import patch

from app.services.rag.router import QueryCategory, classify_query

pytestmark = pytest.mark.anyio


@patch("app.services.rag.router.complete")
async def test_document_question_routes_to_document(mock_complete):
    mock_complete.return_value = "document"
    decision = await classify_query("What is the claim number on this claim form?")
    assert decision.category == QueryCategory.DOCUMENT


@patch("app.services.rag.router.complete")
async def test_bi_question_routes_to_bi(mock_complete):
    mock_complete.return_value = "bi"
    decision = await classify_query("What is our average claims turnaround time this quarter?")
    assert decision.category == QueryCategory.BI

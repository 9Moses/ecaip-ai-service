import pytest

from app.services.rag.router import QueryCategory, classify_query

pytestmark = pytest.mark.anyio


async def test_document_question_routes_to_document():
    decision = await classify_query("What is the claim number on this claim form?")
    assert decision.category == QueryCategory.DOCUMENT


async def test_bi_question_routes_to_bi():
    decision = await classify_query("What is our average claims turnaround time this quarter?")
    assert decision.category == QueryCategory.BI

import random

from app.services.bi.base import BIBridge, BIQueryResult

_SAMPLE_CLAIM_TYPES = ["Auto", "Property", "Liability", "Workers Comp", "Health"]


class MockTableauBridge(BIBridge):
    """
    Returns synthetic but plausible claims-mix data, clearly labeled as mock.
    Used automatically whenever no real Tableau connection is configured.
    """

    async def query(self, natural_language_question: str) -> BIQueryResult:
        rows = [
            [claim_type, random.randint(20, 500), round(random.uniform(0.05, 0.35), 2)]
            for claim_type in _SAMPLE_CLAIM_TYPES
        ]
        return BIQueryResult(
            columns=["Claim Type", "Volume", "Fraud Flag Rate"],
            rows=rows,
            source_label="Tableau (MOCK DATA — no live connection configured)",
            is_mock_data=True,
        )

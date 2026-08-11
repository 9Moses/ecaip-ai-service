import random

from app.services.bi.base import BIBridge, BIQueryResult

_SAMPLE_REGIONS = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]


class MockPowerBIBridge(BIBridge):
    """
    Returns synthetic but plausible claims-operations data, clearly labeled as mock.
    Used automatically whenever no real Power BI connection is configured — see
    app/services/bi/factory.py for the selection logic.
    """

    async def query(self, natural_language_question: str) -> BIQueryResult:
        rows = [
            [region, round(random.uniform(3.5, 9.0), 1), random.randint(40, 300)]
            for region in _SAMPLE_REGIONS
        ]
        return BIQueryResult(
            columns=["Region", "Avg Turnaround (days)", "Claims Volume"],
            rows=rows,
            source_label="Power BI (MOCK DATA — no live connection configured)",
            is_mock_data=True,
        )

from abc import ABC, abstractmethod
from dataclasses import dataclass


from typing import Any


@dataclass
class BIQueryResult:
    columns: list[str]
    rows: list[list[Any]]
    source_label: str
    """Human-readable label shown in citations, e.g. 'Power BI: Claims Ops dataset'."""
    is_mock_data: bool = False


class BIBridge(ABC):
    @abstractmethod
    async def query(self, natural_language_question: str) -> BIQueryResult:
        """Executes a query against the BI system and returns tabular results."""
        raise NotImplementedError

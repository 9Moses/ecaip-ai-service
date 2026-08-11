from typing import Any

from app.services.bi.base import BIQueryResult


def format_as_text_table(result: BIQueryResult) -> str:
    header = " | ".join(result.columns)
    separator = " | ".join("---" for _ in result.columns)
    rows = "\n".join(" | ".join(str(cell) for cell in row) for row in result.rows)
    mock_notice = " (MOCK DATA)" if result.is_mock_data else ""
    return f"Source: {result.source_label}{mock_notice}\n{header}\n{separator}\n{rows}"


def to_chart_data(result: BIQueryResult) -> dict[str, Any]:
    return {
        "source_label": result.source_label,
        "is_mock_data": result.is_mock_data,
        "columns": result.columns,
        "rows": result.rows,
        "dashboard_url": result.dashboard_url,
    }

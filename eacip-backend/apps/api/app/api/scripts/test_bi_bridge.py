import asyncio

from app.core.db import async_session_factory
from app.services.bi.factory import get_power_bi_bridge
from app.services.bi.factory import get_tableau_bridge


async def main() -> None:
    async with async_session_factory() as db:
        power_bi_bridge = await get_power_bi_bridge(db)
        power_bi_result = await power_bi_bridge.query("Average turnaround by region?")
        print(
            f"[Power BI] Source: {power_bi_result.source_label}, "
            f"mock={power_bi_result.is_mock_data}"
        )
        tableau_bridge = await get_tableau_bridge(db)
        tableau_result = await tableau_bridge.query("Claims volume and fraud rate by type?")
        print(
            f"[Tableau] Source: {tableau_result.source_label}, mock={tableau_result.is_mock_data}"
        )
        for row in tableau_result.rows:
            print(row)


if __name__ == "__main__":
    asyncio.run(main())

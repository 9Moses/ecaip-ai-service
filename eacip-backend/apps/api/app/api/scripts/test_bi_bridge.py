import asyncio

from app.core.db import async_session_factory
from app.services.bi.factory import get_power_bi_bridge


async def main() -> None:
    async with async_session_factory() as db:
        bridge = await get_power_bi_bridge(db)
        result = await bridge.query("What's our average claims turnaround time by region?")

        print(f"Source: {result.source_label}")
        print(f"Mock data: {result.is_mock_data}")
        print(f"Columns: {result.columns}")
        for row in result.rows:
            print(row)


if __name__ == "__main__":
    asyncio.run(main())

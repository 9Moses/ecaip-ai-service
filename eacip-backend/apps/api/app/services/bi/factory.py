from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bi_connection import BIConnection
from app.services.bi.base import BIBridge
from app.services.bi.mock_power_bi import MockPowerBIBridge
from app.services.bi.power_bi import PowerBIBridge
from app.services.bi.mock_tableau import MockTableauBridge
from app.services.bi.tableau import TableauBridge


async def get_power_bi_bridge(db: AsyncSession) -> BIBridge:
    connection = await db.scalar(
        select(BIConnection).where(
            BIConnection.provider == "power_bi",
            BIConnection.is_active == True,  # noqa: E712
        )
    )
    if connection is None:
        return MockPowerBIBridge()

    return PowerBIBridge.from_encrypted_config(connection.config, connection.credentials_encrypted)


async def get_tableau_bridge(db: AsyncSession) -> BIBridge:
    connection = await db.scalar(
        select(BIConnection).where(
            BIConnection.provider == "tableau",
            BIConnection.is_active == True,  # noqa: E712
        )
    )
    if connection is None:
        return MockTableauBridge()

    return TableauBridge.from_encrypted_config(connection.config, connection.credentials_encrypted)

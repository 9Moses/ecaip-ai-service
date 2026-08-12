import os
import asyncio
from dotenv import load_dotenv

from app.core.crypto import encrypt_credentials
from app.core.db import async_session_factory
from app.models.bi_connection import BIConnection

load_dotenv(override=True)


async def main() -> None:
    token_secret = os.getenv("TABLEAU_TOKEN_SECRET")
    if token_secret is None:
        raise ValueError("TABLEAU_TOKEN_SECRET environment variable is missing")
    credentials_encrypted = encrypt_credentials(token_secret)

    config = {
        "server_url": os.getenv("TABLEAU_SERVER"),
        "site_id": os.getenv("TABLEAU_SITE"),
        "pat_name": os.getenv("TABLEAU_TOKEN_NAME"),
        "datasource_luid": os.getenv("TABLEAU_DATASOURCE_LUID"),
    }

    async with async_session_factory() as db:
        connection = BIConnection(
            provider="tableau",
            credentials_encrypted=credentials_encrypted,
            config=config,
        )
        db.add(connection)
        await db.commit()
        await db.refresh(connection)

        print("✅ BIConnection saved to the database:")
        print(f"ID: {connection.id}")
        print(f"Provider: {connection.provider}")
        print(f"Server URL: {connection.config.get('server_url')}")
        print(f"Site ID: {connection.config.get('site_id')}")


if __name__ == "__main__":
    asyncio.run(main())

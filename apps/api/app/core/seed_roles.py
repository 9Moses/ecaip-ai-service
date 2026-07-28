import asyncio

from app.core.db import async_session_factory
from app.models.role import Role

ROLE_DEFINITIONS: list[dict] = [
    {
        "name": "Super Admin",
        "permissions": {"scope": "org_wide", "manage_integrations": True, "manage_users": True},
    },
    {
        "name": "Admin",
        "permissions": {"scope": "org_wide", "manage_integrations": False, "manage_users": True},
    },
    {
        "name": "Claims Manager",
        "permissions": {"scope": "claims_department", "manage_claims": True, "view_fraud_queue": True},
    },
    {
        "name": "Underwriter",
        "permissions": {"scope": "underwriting", "view_policy_documents": True, "view_claims_history": True},
    },
    {
        "name": "Fraud Analyst",
        "permissions": {"scope": "siu", "view_fraud_queue": True, "manage_fraud_flags": True},
    },
    {
        "name": "BI Analyst",
        "permissions": {"scope": "reporting", "query_bi_datasets": True, "upload_documents": False},
    },
    {
        "name": "Employee",
        "permissions": {"scope": "self", "upload_documents": True, "query_own_data": True},
    },
]



async def seed_roles() -> None:
    async with async_session_factory() as session:
        from sqlalchemy import select

        for definition in ROLE_DEFINITIONS:
            existing = await session.scalar(select(Role).where(Role.name == definition["name"]))
            if existing:
                continue
            session.add(Role(**definition))
        await session.commit()
        print(f"Seeded {len(ROLE_DEFINITIONS)} roles (existing one skipped)")


if __name__ == "__main__":
    asyncio.run(seed_roles())
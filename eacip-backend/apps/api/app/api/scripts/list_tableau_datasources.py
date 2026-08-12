import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()


async def main() -> None:
    server = os.getenv("TABLEAU_SERVER")
    site = os.getenv("TABLEAU_SITE")
    pat_name = os.getenv("TABLEAU_TOKEN_NAME")
    pat_secret = os.getenv("TABLEAU_TOKEN_SECRET")

    async with httpx.AsyncClient() as client:
        signin = await client.post(
            f"{server}/api/3.21/auth/signin",
            json={
                "credentials": {
                    "personalAccessTokenName": pat_name,
                    "personalAccessTokenSecret": pat_secret,
                    "site": {"contentUrl": site},
                }
            },
            headers={"Accept": "application/json"},
        )
        signin.raise_for_status()
        token = signin.json()["credentials"]["token"]

        resp = await client.post(
            f"{server}/api/metadata/graphql",
            headers={"X-Tableau-Auth": token, "Content-Type": "application/json"},
            json={"query": """
                    query {
                        publishedDatasources {
                            name
                            luid
                        }
                    }
                """},
        )
        resp.raise_for_status()
        data = resp.json()["data"]["publishedDatasources"]

        print(f"Found {len(data)} published data source(s):\n")
        for ds in data:
            print(f"  name: {ds['name']}")
            print(f"  luid: {ds['luid']}\n")


if __name__ == "__main__":
    asyncio.run(main())

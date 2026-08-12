import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv(override=True)


async def main() -> None:
    server = os.getenv("TABLEAU_SERVER")
    site = os.getenv("TABLEAU_SITE")
    pat_name = os.getenv("TABLEAU_TOKEN_NAME")
    pat_secret = os.getenv("TABLEAU_TOKEN_SECRET")
    luid = os.getenv("TABLEAU_DATASOURCE_LUID")

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
            json={
                "query": """
                    query($luid: String!) {
                        publishedDatasources(filter: {luid: $luid}) {
                            name
                            fields { name }
                        }
                    }
                """,
                "variables": {"luid": luid},
            },
        )
        resp.raise_for_status()
        result = resp.json()

        datasources = result.get("data", {}).get("publishedDatasources", [])
        if not datasources:
            print(f"No data source found for LUID: {luid}")
            print(f"Full response: {result}")
            return

        ds = datasources[0]
        print(f"Data source: {ds['name']}\n")
        print("Fields:")
        for field in ds["fields"]:
            print(f"  - {field['name']}")


if __name__ == "__main__":
    asyncio.run(main())

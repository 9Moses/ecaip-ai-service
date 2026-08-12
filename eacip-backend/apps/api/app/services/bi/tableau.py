import httpx

from app.core.crypto import decrypt_credentials
from app.services.bi.base import BIBridge, BIQueryResult

TABLEAU_API_VERSION = "3.21"


class TableauBridge(BIBridge):
    def __init__(
        self, server_url: str, site_id: str, pat_name: str, pat_secret: str, datasource_luid: str
    ):
        self.server_url = server_url.rstrip("/")
        self.site_id = site_id
        self.pat_name = pat_name
        self.pat_secret = pat_secret
        self.datasource_luid = datasource_luid

    async def _sign_in(self, client: httpx.AsyncClient) -> tuple[str, str]:
        """Returns (auth_token, site_luid)."""
        response = await client.post(
            f"{self.server_url}/api/{TABLEAU_API_VERSION}/auth/signin",
            json={
                "credentials": {
                    "personalAccessTokenName": self.pat_name,
                    "personalAccessTokenSecret": self.pat_secret,
                    "site": {"contentUrl": self.site_id},
                }
            },
            headers={"Accept": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()["credentials"]
        return data["token"], data["site"]["id"]

    async def query(self, natural_language_question: str) -> BIQueryResult:
        # Same MVP scoping decision as the Power BI Bridge (Part 1): this runs one
        # fixed, safe, pre-defined query shape against the configured data source
        # rather than attempting to translate arbitrary natural language into a
        # VizQL query spec. See Part 1's PowerBIBridge for the full reasoning —
        # the same trade-off applies here for the same reasons.
        async with httpx.AsyncClient() as client:
            auth_token, site_luid = await self._sign_in(client)

            query_response = await client.post(
                f"{self.server_url}/api/v1/vizql-data-service/query-datasource",
                headers={"X-Tableau-Auth": auth_token, "Content-Type": "application/json"},
                json={
                    "datasource": {"datasourceLuid": self.datasource_luid},
                    "query": {
                        "fields": [
                            {"fieldCaption": "Claim Type"},
                            {"fieldCaption": "Claims Volume", "function": "SUM"},
                            {"fieldCaption": "Fraud Flag Rate", "function": "AVG"},
                        ],
                    },
                },
                timeout=30,
            )
            query_response.raise_for_status()
            result_json = query_response.json()

            await client.post(
                f"{self.server_url}/api/{TABLEAU_API_VERSION}/auth/signout",
                headers={"X-Tableau-Auth": auth_token},
                timeout=10,
            )

        data_rows = result_json.get("data", [])
        columns = list(data_rows[0].keys()) if data_rows else []
        rows = [[row.get(col) for col in columns] for row in data_rows]

        dashboard_url = (
            f"{self.server_url}/#/site/{self.site_id}/datasources"
            + f"/{self.datasource_luid}/connections"
        )

        return BIQueryResult(
            columns=columns,
            rows=rows,
            source_label="Tableau (live data source)",
            dashboard_url=dashboard_url,
            is_mock_data=False,
        )

    @classmethod
    def from_encrypted_config(
        cls, config: dict[str, str], encrypted_pat_secret: bytes
    ) -> "TableauBridge":
        return cls(
            server_url=config["server_url"],
            site_id=config["site_id"],
            pat_name=config["pat_name"],
            pat_secret=decrypt_credentials(encrypted_pat_secret),
            datasource_luid=config["datasource_luid"],
        )

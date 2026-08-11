import httpx
import msal
from typing import Any

from app.core.crypto import decrypt_credentials
from app.services.bi.base import BIBridge, BIQueryResult

POWER_BI_SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]
POWER_BI_API_BASE = "https://api.powerbi.com/v1.0/myorg"


class PowerBIBridge(BIBridge):
    def __init__(
        self, tenant_id: str, client_id: str, client_secret: str, workspace_id: str, dataset_id: str
    ):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.workspace_id = workspace_id
        self.dataset_id = dataset_id

    def _get_access_token(self) -> str:
        app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
        )
        result = app.acquire_token_for_client(scopes=POWER_BI_SCOPE)
        if "access_token" not in result:
            raise RuntimeError(f"Power BI auth failed: {result.get('error_description', result)}")
        return str(result["access_token"])

    async def query(self, natural_language_question: str) -> BIQueryResult:
        # NOTE: translating a natural-language question into an actual DAX query is a
        # non-trivial problem in its own right. This MVP implementation runs a fixed,
        # safe summary query against the configured dataset rather than attempting
        # LLM-generated DAX (which risks malformed or overly expensive queries against
        # a real production dataset). Extending this to LLM-generated DAX, scoped to a
        # reviewed allow-list of safe query patterns, is a well-scoped future
        # enhancement — not something to do unreviewed against live BI data.
        dax_query = (
            "EVALUATE SUMMARIZECOLUMNS("
            "'Claims'[Region], "
            "\"Avg Turnaround\", AVERAGE('Claims'[TurnaroundDays]), "
            "\"Claim Count\", COUNTROWS('Claims'))"
        )

        token = self._get_access_token()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{POWER_BI_API_BASE}/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={
                    "queries": [{"query": dax_query}],
                    "serializerSettings": {"includeNulls": True},
                },
                timeout=30,
            )
            response.raise_for_status()
            result_json = response.json()

        table = result_json["results"][0]["tables"][0]
        rows_raw = table.get("rows", [])
        columns = list(rows_raw[0].keys()) if rows_raw else []
        rows = [[row.get(col) for col in columns] for row in rows_raw]

        return BIQueryResult(
            columns=columns,
            rows=rows,
            source_label="Power BI (live dataset)",
            is_mock_data=False,
        )

    @classmethod
    def from_encrypted_config(
        cls, config: dict[str, Any], encrypted_client_secret: bytes
    ) -> "PowerBIBridge":
        return cls(
            tenant_id=config["tenant_id"],
            client_id=config["client_id"],
            client_secret=decrypt_credentials(encrypted_client_secret),
            workspace_id=config["workspace_id"],
            dataset_id=config["dataset_id"],
        )

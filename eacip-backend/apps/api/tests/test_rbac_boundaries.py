import pytest

pytestmark = pytest.mark.anyio


class TestFraudQueueRBAC:
    async def test_employee_blocked_from_list(self, api_client, employee_token):
        resp = await api_client.get(
            "/api/v1/fraud/flags", headers={"Authorization": f"Bearer {employee_token}"}
        )
        assert resp.status_code == 403

    async def test_fraud_analyst_allowed_to_list(self, api_client, fraud_analyst_token):
        resp = await api_client.get(
            "/api/v1/fraud/flags", headers={"Authorization": f"Bearer {fraud_analyst_token}"}
        )
        assert resp.status_code == 200

    async def test_claims_manager_can_read_but_not_write(self, api_client, claims_manager_token):
        list_resp = await api_client.get(
            "/api/v1/fraud/flags", headers={"Authorization": f"Bearer {claims_manager_token}"}
        )
        assert list_resp.status_code == 200

        # A Claims Manager should never be able to PATCH a flag, even a nonexistent one —
        # the 403 must come before any existence check, or a Claims Manager could probe
        # for valid flag IDs via a 404-vs-403 timing/response difference.
        patch_resp = await api_client.patch(
            "/api/v1/fraud/flags/00000000-0000-0000-0000-000000000000",
            json={"status": "cleared"},
            headers={"Authorization": f"Bearer {claims_manager_token}"},
        )
        assert patch_resp.status_code == 403


class TestAdminEndpointsRBAC:
    async def test_employee_blocked_from_user_list(self, api_client, employee_token):
        resp = await api_client.get(
            "/api/v1/users", headers={"Authorization": f"Bearer {employee_token}"}
        )
        assert resp.status_code == 403

    async def test_admin_allowed_user_list(self, api_client, admin_token):
        resp = await api_client.get(
            "/api/v1/users", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert resp.status_code == 200

    async def test_employee_blocked_from_audit_logs(self, api_client, employee_token):
        resp = await api_client.get(
            "/api/v1/admin/audit-logs", headers={"Authorization": f"Bearer {employee_token}"}
        )
        assert resp.status_code == 403

    async def test_fraud_analyst_blocked_from_audit_logs(self, api_client, fraud_analyst_token):
        # Fraud Analyst has elevated access to fraud data specifically, but that
        # shouldn't imply general Admin-level access to unrelated resources.
        resp = await api_client.get(
            "/api/v1/admin/audit-logs", headers={"Authorization": f"Bearer {fraud_analyst_token}"}
        )
        assert resp.status_code == 403


class TestDocumentOwnershipScoping:
    async def test_user_cannot_view_another_users_document(
        self, api_client, employee_token, fraud_analyst_token
    ):
        # Upload as one user
        files = {"file": ("test.pdf", b"%PDF-1.4 fake content", "application/pdf")}
        upload_resp = await api_client.post(
            "/api/v1/documents", files=files, headers={"Authorization": f"Bearer {employee_token}"}
        )
        document_id = upload_resp.json()["id"]

        # Attempt to view it as a different user entirely
        view_resp = await api_client.get(
            f"/api/v1/documents/{document_id}",
            headers={"Authorization": f"Bearer {fraud_analyst_token}"},
        )
        assert view_resp.status_code == 404
        # 404, not 403: doc 07's ownership scoping should behave as if the document
        # doesn't exist at all for a non-owner, not confirm its existence via a 403.


class TestUnauthenticatedAccess:
    @pytest.mark.parametrize(
        "method,path",
        [
            ("GET", "/api/v1/documents"),
            ("GET", "/api/v1/chat/sessions"),
            ("GET", "/api/v1/fraud/flags"),
            ("GET", "/api/v1/admin/audit-logs"),
        ],
    )
    async def test_protected_endpoints_reject_missing_token(self, api_client, method, path):
        resp = await api_client.request(method, path)
        assert resp.status_code == 401

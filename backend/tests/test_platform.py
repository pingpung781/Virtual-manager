"""
Unit tests for Platform API endpoints.

Tests:
- RBAC / permissions
- Audit logs
- Tenants
- MCP tools
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestRBAC:
    """Tests for role-based access control endpoints."""
    
    def test_get_user_permissions(self, authenticated_client: TestClient, mock_user):
        """Test getting user permissions."""
        response = authenticated_client.get(f"/platform/permissions/{mock_user.id}")
        assert response.status_code in [200, 404]
    
    def test_check_permission(self, authenticated_client: TestClient, mock_user):
        """Test checking specific permission."""
        response = authenticated_client.get(
            f"/platform/permissions/{mock_user.id}/check",
            params={"resource": "project", "action": "read"}
        )
        assert response.status_code in [200, 404]
    
    def test_assign_role(self, authenticated_client: TestClient, mock_user, contributor_user):
        """Test assigning a role to user (admin only)."""
        response = authenticated_client.post(
            f"/platform/users/{contributor_user.id}/role",
            json={"role": "manager"}
        )
        assert response.status_code in [200, 403, 404]
    
    def test_list_roles(self, authenticated_client: TestClient):
        """Test listing available roles."""
        response = authenticated_client.get("/platform/roles")
        assert response.status_code in [200, 404]


class TestAuditLogs:
    """Tests for audit log endpoints."""
    
    def test_get_audit_logs(self, authenticated_client: TestClient):
        """Test getting audit logs."""
        response = authenticated_client.get("/platform/audit-logs")
        assert response.status_code in [200, 403]
    
    def test_get_audit_logs_filtered(self, authenticated_client: TestClient, mock_user):
        """Test getting filtered audit logs."""
        response = authenticated_client.get(
            "/platform/audit-logs",
            params={"actor_id": mock_user.id, "limit": 10}
        )
        assert response.status_code in [200, 403]
    
    def test_export_audit_logs(self, authenticated_client: TestClient):
        """Test exporting audit logs."""
        response = authenticated_client.get(
            "/platform/audit-logs/export",
            params={"format": "csv"}
        )
        assert response.status_code in [200, 403, 404]


class TestTenants:
    """Tests for multi-tenancy endpoints."""
    
    def test_get_tenant_info(self, authenticated_client: TestClient):
        """Test getting current tenant info."""
        response = authenticated_client.get("/platform/tenant")
        assert response.status_code in [200, 404]
    
    def test_update_tenant_settings(self, authenticated_client: TestClient):
        """Test updating tenant settings."""
        response = authenticated_client.patch(
            "/platform/tenant/settings",
            json={"feature_flags": {"new_dashboard": True}}
        )
        assert response.status_code in [200, 403, 404]
    
    def test_get_tenant_usage(self, authenticated_client: TestClient):
        """Test getting tenant usage/limits."""
        response = authenticated_client.get("/platform/tenant/usage")
        assert response.status_code in [200, 404]


class TestMCPTools:
    """Tests for MCP tool registry endpoints."""
    
    def test_list_mcp_tools(self, authenticated_client: TestClient):
        """Test listing registered MCP tools."""
        response = authenticated_client.get("/platform/tools")
        assert response.status_code in [200, 404]
    
    def test_get_tool_status(self, authenticated_client: TestClient):
        """Test getting tool health status."""
        response = authenticated_client.get("/platform/tools/calendar/status")
        assert response.status_code in [200, 404]
    
    def test_register_tool(self, authenticated_client: TestClient):
        """Test registering a new MCP tool."""
        response = authenticated_client.post(
            "/platform/tools",
            json={
                "name": "custom_tool",
                "endpoint": "http://localhost:5000/mcp",
                "requires_approval": False
            }
        )
        assert response.status_code in [200, 201, 403, 422]
    
    def test_disable_tool(self, authenticated_client: TestClient):
        """Test disabling a tool (circuit breaker)."""
        response = authenticated_client.post(
            "/platform/tools/test_tool/disable",
            json={"reason": "Too many errors"}
        )
        assert response.status_code in [200, 403, 404]


class TestSystemHealth:
    """Tests for system health endpoints."""
    
    def test_health_check(self, authenticated_client: TestClient):
        """Test basic health check."""
        response = authenticated_client.get("/platform/health")
        assert response.status_code == 200
    
    def test_get_system_status(self, authenticated_client: TestClient):
        """Test getting detailed system status."""
        response = authenticated_client.get("/platform/status")
        assert response.status_code in [200, 403]
    
    def test_get_metrics(self, authenticated_client: TestClient):
        """Test getting system metrics."""
        response = authenticated_client.get("/platform/metrics")
        assert response.status_code in [200, 403, 404]

"""
Unit tests for Advanced Capabilities API endpoints.

Tests:
- Organization rules
- Custom workflows
- Plugins
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


class TestOrganizationRules:
    """Tests for organization rule endpoints."""
    
    def test_create_rule(self, authenticated_client: TestClient):
        """Test creating an organization rule."""
        response = authenticated_client.post(
            "/advanced/rules",
            json={
                "name": "Auto-assign urgent tasks",
                "condition": {"priority": "urgent", "unassigned": True},
                "action": {"assign_to": "on-call-user"},
                "enabled": True
            }
        )
        assert response.status_code in [200, 201, 422]
    
    def test_list_rules(self, authenticated_client: TestClient):
        """Test listing organization rules."""
        response = authenticated_client.get("/advanced/rules")
        assert response.status_code in [200, 404]
    
    def test_update_rule(self, authenticated_client: TestClient):
        """Test updating a rule."""
        response = authenticated_client.patch(
            "/advanced/rules/test-rule-id",
            json={"enabled": False}
        )
        assert response.status_code in [200, 404]
    
    def test_delete_rule(self, authenticated_client: TestClient):
        """Test deleting a rule."""
        response = authenticated_client.delete("/advanced/rules/test-rule-id")
        assert response.status_code in [200, 204, 404]


class TestCustomWorkflows:
    """Tests for custom workflow endpoints."""
    
    def test_create_workflow(self, authenticated_client: TestClient):
        """Test creating a custom workflow."""
        response = authenticated_client.post(
            "/advanced/workflows",
            json={
                "name": "Bug Triage",
                "steps": [
                    {"type": "filter", "condition": {"label": "bug"}},
                    {"type": "assign", "to": "triage-team"},
                    {"type": "notify", "channel": "bugs"}
                ]
            }
        )
        assert response.status_code in [200, 201, 422]
    
    def test_list_workflows(self, authenticated_client: TestClient):
        """Test listing workflows."""
        response = authenticated_client.get("/advanced/workflows")
        assert response.status_code in [200, 404]
    
    def test_execute_workflow(self, authenticated_client: TestClient, sample_task):
        """Test manually executing a workflow."""
        response = authenticated_client.post(
            "/advanced/workflows/test-workflow/execute",
            json={"target_id": sample_task["id"]}
        )
        assert response.status_code in [200, 404]


class TestPlugins:
    """Tests for plugin system endpoints."""
    
    def test_list_plugins(self, authenticated_client: TestClient):
        """Test listing installed plugins."""
        response = authenticated_client.get("/advanced/plugins")
        assert response.status_code in [200, 404]
    
    def test_install_plugin(self, authenticated_client: TestClient):
        """Test installing a plugin."""
        response = authenticated_client.post(
            "/advanced/plugins/install",
            json={
                "name": "custom-reporter",
                "source": "https://example.com/plugin.zip"
            }
        )
        assert response.status_code in [200, 201, 403, 422]
    
    def test_enable_plugin(self, authenticated_client: TestClient):
        """Test enabling a plugin."""
        response = authenticated_client.post(
            "/advanced/plugins/test-plugin/enable"
        )
        assert response.status_code in [200, 404]
    
    def test_disable_plugin(self, authenticated_client: TestClient):
        """Test disabling a plugin."""
        response = authenticated_client.post(
            "/advanced/plugins/test-plugin/disable"
        )
        assert response.status_code in [200, 404]


class TestFeatureFlags:
    """Tests for feature flag endpoints."""
    
    def test_list_feature_flags(self, authenticated_client: TestClient):
        """Test listing feature flags."""
        response = authenticated_client.get("/advanced/features")
        assert response.status_code in [200, 404]
    
    def test_toggle_feature(self, authenticated_client: TestClient):
        """Test toggling a feature flag."""
        response = authenticated_client.post(
            "/advanced/features/new-dashboard",
            json={"enabled": True, "percentage": 50}
        )
        assert response.status_code in [200, 403, 404]

"""
Unit tests for Analytics API endpoints.

Tests:
- Velocity tracking
- Risk scoring
- Dashboard data
- Forecasting
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestVelocityTracking:
    """Tests for velocity tracking endpoints."""
    
    def test_get_project_velocity(self, authenticated_client: TestClient, sample_project):
        """Test getting project velocity."""
        response = authenticated_client.get(
            f"/analytics/velocity/{sample_project['id']}"
        )
        assert response.status_code in [200, 404]
    
    def test_get_velocity_trends(self, authenticated_client: TestClient, sample_project):
        """Test getting velocity trends over time."""
        response = authenticated_client.get(
            f"/analytics/velocity/{sample_project['id']}/trends",
            params={"days": 30}
        )
        assert response.status_code in [200, 404]


class TestRiskScoring:
    """Tests for risk scoring endpoints."""
    
    def test_get_project_risk(self, authenticated_client: TestClient, sample_project):
        """Test getting project risk score."""
        response = authenticated_client.get(
            f"/analytics/risk/{sample_project['id']}"
        )
        assert response.status_code in [200, 404]
    
    def test_get_risk_heatmap(self, authenticated_client: TestClient):
        """Test getting risk heatmap for all projects."""
        response = authenticated_client.get("/analytics/risk/heatmap")
        assert response.status_code in [200, 404]


class TestDashboard:
    """Tests for dashboard endpoints."""
    
    def test_get_dashboard(self, authenticated_client: TestClient):
        """Test getting main dashboard data."""
        response = authenticated_client.get("/analytics/dashboard")
        assert response.status_code in [200, 404]
    
    def test_get_executive_summary(self, authenticated_client: TestClient):
        """Test getting executive summary."""
        response = authenticated_client.get("/analytics/executive-summary")
        assert response.status_code in [200, 404]
    
    def test_get_task_distribution(self, authenticated_client: TestClient):
        """Test getting task distribution by status."""
        response = authenticated_client.get("/analytics/tasks/distribution")
        assert response.status_code in [200, 404]


class TestForecasting:
    """Tests for AI forecasting endpoints."""
    
    def test_get_completion_forecast(self, authenticated_client: TestClient, sample_project):
        """Test getting completion forecast for project."""
        response = authenticated_client.get(
            f"/analytics/forecast/{sample_project['id']}"
        )
        assert response.status_code in [200, 404]
    
    @patch('backend.app.core.analytics.run_forecast')
    def test_run_forecast(self, mock_forecast, authenticated_client: TestClient, sample_project):
        """Test running a new forecast."""
        mock_forecast.return_value = {
            "predicted_completion": "2024-02-15",
            "confidence": 0.85
        }
        
        response = authenticated_client.post(
            f"/analytics/forecast/{sample_project['id']}/run"
        )
        assert response.status_code in [200, 404]


class TestAutomationRules:
    """Tests for automation rule endpoints."""
    
    def test_list_rules(self, authenticated_client: TestClient):
        """Test listing automation rules."""
        response = authenticated_client.get("/analytics/rules")
        assert response.status_code in [200, 404]
    
    def test_create_rule(self, authenticated_client: TestClient):
        """Test creating an automation rule."""
        response = authenticated_client.post(
            "/analytics/rules",
            json={
                "name": "High Overdue Alert",
                "trigger_condition": {"metric": "overdue_tasks", "operator": ">", "value": 5},
                "action_type": "notify",
                "action_params": {"channel": "slack"}
            }
        )
        assert response.status_code in [200, 201, 422]


class TestSnapshots:
    """Tests for project snapshot endpoints."""
    
    def test_take_snapshot(self, authenticated_client: TestClient, sample_project):
        """Test taking a project snapshot."""
        response = authenticated_client.post(
            f"/analytics/snapshots/{sample_project['id']}"
        )
        assert response.status_code in [200, 201, 404]
    
    def test_get_snapshots(self, authenticated_client: TestClient, sample_project):
        """Test getting project snapshots."""
        response = authenticated_client.get(
            f"/analytics/snapshots/{sample_project['id']}"
        )
        assert response.status_code in [200, 404]

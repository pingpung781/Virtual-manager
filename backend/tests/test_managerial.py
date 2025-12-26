"""
Unit tests for Managerial API endpoints.

Tests:
- Approval workflow (pending, decide, submit)
- Risk assessment
- Strategy endpoints (goals, alignment)
- Communication (standup)
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestApprovalEndpoints:
    """Tests for approval workflow endpoints."""
    
    def test_get_pending_approvals_empty(self, authenticated_client: TestClient):
        """Test getting pending approvals when none exist."""
        response = authenticated_client.get("/managerial/approvals/pending")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "approvals" in data
        assert data["count"] == 0
    
    def test_get_pending_count(self, authenticated_client: TestClient):
        """Test getting pending approval count."""
        response = authenticated_client.get("/managerial/approvals/count")
        assert response.status_code == 200
        data = response.json()
        assert "pending_count" in data
        assert "has_pending" in data
    
    def test_submit_low_risk_action(self, authenticated_client: TestClient):
        """Test submitting a low-risk action (auto-approved)."""
        response = authenticated_client.post(
            "/managerial/submit-action",
            json={
                "action_type": "create_task",
                "action_summary": "Create a new task",
                "payload": {"name": "Test Task"},
                "agent_name": "test"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "auto_approved"
        assert "risk_assessment" in data
    
    def test_submit_high_risk_action(self, authenticated_client: TestClient, db, mock_user):
        """Test submitting a high-risk action (requires approval)."""
        response = authenticated_client.post(
            "/managerial/submit-action",
            json={
                "action_type": "delete_project",
                "action_summary": "Delete old project",
                "payload": {"project_id": "xyz"},
                "agent_name": "test"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending_approval"
        assert data["risk_assessment"]["adjusted_score"] >= 50
    
    def test_assess_risk(self, authenticated_client: TestClient):
        """Test risk assessment endpoint."""
        response = authenticated_client.post(
            "/managerial/assess-risk",
            params={"action_type": "delete_repo"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["adjusted_score"] == 100
        assert data["requires_approval"] == True
        assert data["risk_level"] == "critical"
    
    def test_decide_approval_not_found(self, authenticated_client: TestClient):
        """Test deciding on non-existent approval."""
        response = authenticated_client.post(
            "/managerial/approvals/nonexistent-id/decide",
            json={"decision": "approved"}
        )
        assert response.status_code == 404


class TestStrategyEndpoints:
    """Tests for strategy/goal endpoints."""
    
    @patch('backend.app.agents.strategy.StrategyAgent')
    def test_create_goal(self, mock_agent, authenticated_client: TestClient):
        """Test creating a goal from text."""
        mock_instance = MagicMock()
        mock_instance.create_goal_from_text.return_value = {
            "goal_id": "test-goal-id",
            "name": "Increase Revenue",
            "kr_count": 3
        }
        mock_agent.return_value = mock_instance
        
        response = authenticated_client.post(
            "/managerial/goals",
            json={"text": "Increase revenue by 20% this quarter"}
        )
        assert response.status_code == 200
    
    @patch('backend.app.agents.strategy.StrategyAgent')
    def test_get_goal_alignment(self, mock_agent, authenticated_client: TestClient, sample_goal):
        """Test getting goal alignment."""
        mock_instance = MagicMock()
        mock_instance.get_goal_alignment.return_value = {
            "goal_id": sample_goal["id"],
            "aligned_projects": [],
            "unaligned_projects": []
        }
        mock_agent.return_value = mock_instance
        
        response = authenticated_client.get(f"/managerial/goals/{sample_goal['id']}/alignment")
        assert response.status_code == 200


class TestRiskEndpoints:
    """Tests for project risk endpoints."""
    
    @patch('backend.app.agents.risk.RiskAgent')
    def test_analyze_project_risk(self, mock_agent, authenticated_client: TestClient, sample_project):
        """Test analyzing project risk."""
        mock_instance = MagicMock()
        mock_instance.assess_project_risk.return_value = {
            "project_id": sample_project["id"],
            "risk_score": 45,
            "risk_level": "medium"
        }
        mock_agent.return_value = mock_instance
        
        response = authenticated_client.post(
            f"/managerial/analyze/risk/{sample_project['id']}"
        )
        assert response.status_code == 200
    
    @patch('backend.app.agents.risk.RiskAgent')
    def test_get_project_risks(self, mock_agent, authenticated_client: TestClient, sample_project):
        """Test getting project risks."""
        mock_instance = MagicMock()
        mock_instance.get_project_risks.return_value = {"risks": []}
        mock_agent.return_value = mock_instance
        
        response = authenticated_client.get(f"/managerial/risks/{sample_project['id']}")
        assert response.status_code == 200


class TestStandupEndpoints:
    """Tests for standup/communication endpoints."""
    
    def test_get_daily_standup(self, authenticated_client: TestClient):
        """Test getting daily standup summary."""
        response = authenticated_client.get("/managerial/standup")
        assert response.status_code == 200
        data = response.json()
        assert "date" in data

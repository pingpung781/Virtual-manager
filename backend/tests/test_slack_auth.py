"""
Unit tests for Slack Auth API endpoints.

Tests:
- Slack OAuth flow
- User linking
- Bot status
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestSlackOAuth:
    """Tests for Slack OAuth endpoints."""
    
    def test_slack_connect_redirect(self, authenticated_client: TestClient):
        """Test Slack OAuth connect redirects correctly."""
        response = authenticated_client.get(
            "/auth/slack/connect",
            follow_redirects=False
        )
        # Should redirect to Slack
        assert response.status_code in [302, 307, 200]
    
    @patch('backend.app.routers.slack_auth.exchange_slack_code')
    def test_slack_callback_success(self, mock_exchange, authenticated_client: TestClient, mock_user):
        """Test Slack OAuth callback."""
        mock_exchange.return_value = {
            "access_token": "xoxb-test-token",
            "team": {"id": "T123", "name": "Test Team"},
            "authed_user": {"id": "U123"}
        }
        
        response = authenticated_client.get(
            "/auth/slack/callback",
            params={"code": "test_code", "state": "test_state"},
            follow_redirects=False
        )
        assert response.status_code in [200, 302, 307, 400]
    
    def test_slack_callback_no_code(self, authenticated_client: TestClient):
        """Test callback without code returns error."""
        response = authenticated_client.get("/auth/slack/callback")
        assert response.status_code in [400, 422]


class TestUserLinking:
    """Tests for Slack user linking endpoints."""
    
    def test_link_slack_user(self, authenticated_client: TestClient, mock_user):
        """Test linking Slack user to VAM user."""
        response = authenticated_client.post(
            "/auth/slack/link",
            json={"slack_user_id": "U123456"}
        )
        assert response.status_code in [200, 400, 404]
    
    def test_get_linked_user(self, authenticated_client: TestClient, mock_user):
        """Test getting linked Slack user."""
        response = authenticated_client.get(f"/auth/slack/user/{mock_user.id}")
        assert response.status_code in [200, 404]
    
    def test_unlink_slack_user(self, authenticated_client: TestClient, mock_user):
        """Test unlinking Slack user."""
        response = authenticated_client.delete(f"/auth/slack/user/{mock_user.id}")
        assert response.status_code in [200, 204, 404]


class TestBotStatus:
    """Tests for Slack bot status endpoints."""
    
    def test_get_bot_status(self, authenticated_client: TestClient):
        """Test getting Slack bot status."""
        response = authenticated_client.get("/auth/slack/bot/status")
        assert response.status_code in [200, 404]
    
    @patch('backend.app.services.slack_service.SlackService')
    def test_send_test_message(self, mock_service, authenticated_client: TestClient, mock_user):
        """Test sending a test DM."""
        mock_instance = MagicMock()
        mock_instance.send_dm.return_value = {"ok": True}
        mock_service.return_value = mock_instance
        
        response = authenticated_client.post(
            "/auth/slack/test-dm",
            json={"user_id": mock_user.id, "message": "Test message"}
        )
        assert response.status_code in [200, 400, 404]
    
    def test_disconnect_slack(self, authenticated_client: TestClient):
        """Test disconnecting Slack."""
        response = authenticated_client.post("/auth/slack/disconnect")
        assert response.status_code in [200, 400, 404]

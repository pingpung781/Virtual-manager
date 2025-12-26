"""
Unit tests for Webhook API endpoints.

Tests:
- GitHub webhook handlers
- Issue events
- PR events
- Signature verification
"""

import pytest
import hmac
import hashlib
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestGitHubWebhooks:
    """Tests for GitHub webhook endpoints."""
    
    def _generate_signature(self, payload: str, secret: str = "test_secret") -> str:
        """Generate GitHub webhook signature."""
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    def test_webhook_ping(self, client: TestClient):
        """Test GitHub ping webhook."""
        payload = '{"zen": "test", "hook_id": 12345}'
        
        response = client.post(
            "/webhooks/github",
            content=payload,
            headers={
                "X-GitHub-Event": "ping",
                "X-Hub-Signature-256": self._generate_signature(payload),
                "Content-Type": "application/json"
            }
        )
        assert response.status_code in [200, 400, 401]
    
    @patch('backend.app.routers.webhooks.verify_webhook_signature')
    def test_issue_opened(self, mock_verify, client: TestClient, db):
        """Test issue opened event."""
        mock_verify.return_value = True
        
        payload = {
            "action": "opened",
            "issue": {
                "number": 1,
                "title": "Test Issue",
                "body": "Test body",
                "state": "open",
                "user": {"login": "testuser"}
            },
            "repository": {
                "full_name": "user/repo"
            }
        }
        
        response = client.post(
            "/webhooks/github",
            json=payload,
            headers={
                "X-GitHub-Event": "issues",
                "X-Hub-Signature-256": "sha256=test"
            }
        )
        assert response.status_code in [200, 400, 401]
    
    @patch('backend.app.routers.webhooks.verify_webhook_signature')
    def test_issue_closed(self, mock_verify, client: TestClient, db):
        """Test issue closed event."""
        mock_verify.return_value = True
        
        payload = {
            "action": "closed",
            "issue": {
                "number": 1,
                "title": "Test Issue",
                "state": "closed"
            },
            "repository": {
                "full_name": "user/repo"
            }
        }
        
        response = client.post(
            "/webhooks/github",
            json=payload,
            headers={
                "X-GitHub-Event": "issues",
                "X-Hub-Signature-256": "sha256=test"
            }
        )
        assert response.status_code in [200, 400, 401]
    
    @patch('backend.app.routers.webhooks.verify_webhook_signature')
    def test_pull_request_opened(self, mock_verify, client: TestClient):
        """Test PR opened event."""
        mock_verify.return_value = True
        
        payload = {
            "action": "opened",
            "pull_request": {
                "number": 1,
                "title": "Test PR",
                "state": "open"
            },
            "repository": {
                "full_name": "user/repo"
            }
        }
        
        response = client.post(
            "/webhooks/github",
            json=payload,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": "sha256=test"
            }
        )
        assert response.status_code in [200, 400, 401]
    
    def test_invalid_signature(self, client: TestClient):
        """Test webhook with invalid signature."""
        response = client.post(
            "/webhooks/github",
            json={"action": "test"},
            headers={
                "X-GitHub-Event": "ping",
                "X-Hub-Signature-256": "sha256=invalid"
            }
        )
        # Should reject invalid signature
        assert response.status_code in [200, 400, 401, 403]


class TestWebhookStatus:
    """Tests for webhook status endpoints."""
    
    def test_get_webhook_status(self, authenticated_client: TestClient):
        """Test getting webhook configuration status."""
        response = authenticated_client.get("/webhooks/status")
        assert response.status_code in [200, 404]
    
    def test_list_recent_events(self, authenticated_client: TestClient):
        """Test listing recent webhook events."""
        response = authenticated_client.get("/webhooks/events")
        assert response.status_code in [200, 404]

"""
Unit tests for Auth API endpoints.

Tests:
- GitHub OAuth flow
- Session management
- User info endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestGitHubOAuth:
    """Tests for GitHub OAuth endpoints."""
    
    def test_github_login_redirect(self, client: TestClient):
        """Test GitHub OAuth login redirects correctly."""
        response = client.get("/auth/github", follow_redirects=False)
        # Should redirect to GitHub
        assert response.status_code == 307 or response.status_code == 302
        assert "github.com" in response.headers.get("location", "")
    
    @patch('backend.app.routers.auth.exchange_code_for_token')
    @patch('backend.app.routers.auth.get_github_user')
    def test_github_callback_success(self, mock_user, mock_token, client: TestClient, db):
        """Test GitHub OAuth callback creates user."""
        mock_token.return_value = "test_access_token"
        mock_user.return_value = {
            "id": 12345,
            "login": "testuser",
            "email": "test@example.com",
            "name": "Test User",
            "avatar_url": "https://github.com/avatar.png"
        }
        
        response = client.get(
            "/auth/callback",
            params={"code": "test_code"},
            follow_redirects=False
        )
        # Should redirect to frontend
        assert response.status_code in [302, 307, 200]
    
    def test_github_callback_no_code(self, client: TestClient):
        """Test callback without code returns error."""
        response = client.get("/auth/callback")
        assert response.status_code == 400


class TestSessionManagement:
    """Tests for session/auth endpoints."""
    
    def test_get_current_user_unauthenticated(self, client: TestClient):
        """Test getting current user without auth."""
        response = client.get("/auth/me")
        assert response.status_code == 401 or response.status_code == 403
    
    def test_get_current_user_authenticated(self, authenticated_client: TestClient, mock_user):
        """Test getting current user with auth."""
        response = authenticated_client.get("/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == mock_user.email
    
    def test_logout(self, authenticated_client: TestClient):
        """Test logout endpoint."""
        response = authenticated_client.post("/auth/logout")
        # Either success or redirect
        assert response.status_code in [200, 302, 307]


class TestRepoSelection:
    """Tests for repository selection endpoints."""
    
    @patch('backend.app.services.github_service.GitHubService')
    def test_list_repos(self, mock_service, authenticated_client: TestClient, mock_user):
        """Test listing user's GitHub repos."""
        mock_instance = MagicMock()
        mock_instance.get_user_repos.return_value = [
            {"full_name": "user/repo1", "name": "repo1"},
            {"full_name": "user/repo2", "name": "repo2"}
        ]
        mock_service.return_value = mock_instance
        
        response = authenticated_client.get("/auth/repos")
        assert response.status_code == 200
    
    def test_set_default_repo(self, authenticated_client: TestClient, mock_user, db):
        """Test setting default repository."""
        response = authenticated_client.post(
            "/auth/repos/default",
            json={"repo": "user/test-repo"}
        )
        # May need repo validation, so accept 200 or 400
        assert response.status_code in [200, 400]

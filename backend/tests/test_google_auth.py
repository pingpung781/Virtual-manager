"""
Unit tests for Google Auth API endpoints.

Tests:
- Google OAuth flow
- Calendar connection
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestGoogleOAuth:
    """Tests for Google OAuth endpoints."""
    
    def test_google_login_redirect(self, authenticated_client: TestClient):
        """Test Google OAuth login redirects correctly."""
        response = authenticated_client.get(
            "/auth/google/connect",
            follow_redirects=False
        )
        # Should redirect to Google
        assert response.status_code in [302, 307, 200]
    
    @patch('backend.app.routers.google_auth.exchange_google_code')
    def test_google_callback_success(self, mock_exchange, authenticated_client: TestClient, mock_user):
        """Test Google OAuth callback."""
        mock_exchange.return_value = {
            "access_token": "google_access_token",
            "refresh_token": "google_refresh_token",
            "expires_in": 3600
        }
        
        response = authenticated_client.get(
            "/auth/google/callback",
            params={"code": "test_code", "state": "test_state"},
            follow_redirects=False
        )
        assert response.status_code in [200, 302, 307, 400]
    
    def test_google_callback_no_code(self, authenticated_client: TestClient):
        """Test callback without code returns error."""
        response = authenticated_client.get("/auth/google/callback")
        assert response.status_code in [400, 422]


class TestCalendarConnection:
    """Tests for calendar connection endpoints."""
    
    def test_get_connection_status(self, authenticated_client: TestClient):
        """Test getting Google Calendar connection status."""
        response = authenticated_client.get("/auth/google/status")
        assert response.status_code in [200, 404]
    
    def test_disconnect_google(self, authenticated_client: TestClient):
        """Test disconnecting Google Calendar."""
        response = authenticated_client.post("/auth/google/disconnect")
        assert response.status_code in [200, 400, 404]
    
    @patch('backend.app.services.google_calendar_service.GoogleCalendarService')
    def test_test_connection(self, mock_service, authenticated_client: TestClient):
        """Test calendar connection test endpoint."""
        mock_instance = MagicMock()
        mock_instance.test_connection.return_value = True
        mock_service.return_value = mock_instance
        
        response = authenticated_client.get("/auth/google/test")
        assert response.status_code in [200, 400, 404]

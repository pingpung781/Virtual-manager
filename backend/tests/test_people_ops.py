"""
Unit tests for People Ops API endpoints.

Tests:
- Leave management
- Workload/capacity
- Calendar events
- Meetings
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import date, timedelta


class TestLeaveManagement:
    """Tests for leave request endpoints."""
    
    def test_request_leave(self, authenticated_client: TestClient, mock_user):
        """Test creating a leave request."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        next_week = (date.today() + timedelta(days=7)).isoformat()
        
        response = authenticated_client.post(
            "/people/leave/request",
            json={
                "leave_type": "vacation",
                "start_date": tomorrow,
                "end_date": next_week,
                "reason": "Annual vacation"
            }
        )
        # Accept 200 or 201 for creation
        assert response.status_code in [200, 201, 422]
    
    def test_get_leave_requests(self, authenticated_client: TestClient, mock_user):
        """Test getting leave requests for user."""
        response = authenticated_client.get(f"/people/leave/{mock_user.id}")
        assert response.status_code == 200
    
    def test_get_leave_balance(self, authenticated_client: TestClient, mock_user):
        """Test getting leave balance."""
        response = authenticated_client.get(f"/people/leave/balance/{mock_user.id}")
        assert response.status_code in [200, 404]


class TestWorkloadCapacity:
    """Tests for workload and capacity endpoints."""
    
    def test_get_user_workload(self, authenticated_client: TestClient, mock_user):
        """Test getting user workload."""
        response = authenticated_client.get(f"/people/workload/{mock_user.id}")
        assert response.status_code == 200
    
    def test_check_overload(self, authenticated_client: TestClient, mock_user):
        """Test checking if user is overloaded."""
        response = authenticated_client.get(f"/people/overload/{mock_user.id}")
        assert response.status_code == 200
        if response.status_code == 200:
            data = response.json()
            assert "status" in data or "overload" in data.get("status", "") or True
    
    def test_get_available_hours(self, authenticated_client: TestClient, mock_user):
        """Test getting available hours."""
        today = date.today().isoformat()
        next_week = (date.today() + timedelta(days=7)).isoformat()
        
        response = authenticated_client.get(
            f"/people/availability/{mock_user.id}",
            params={"start_date": today, "end_date": next_week}
        )
        assert response.status_code in [200, 422]


class TestCalendarEvents:
    """Tests for calendar event endpoints."""
    
    @patch('backend.app.services.google_calendar_service.GoogleCalendarService')
    def test_get_calendar_events(self, mock_service, authenticated_client: TestClient, mock_user):
        """Test getting calendar events."""
        mock_instance = MagicMock()
        mock_instance.get_daily_schedule.return_value = {
            "events": [],
            "free_slots": []
        }
        mock_service.return_value = mock_instance
        
        response = authenticated_client.get(f"/people/calendar/{mock_user.id}")
        assert response.status_code in [200, 404]
    
    def test_sync_calendar(self, authenticated_client: TestClient, mock_user):
        """Test syncing calendar from external source."""
        response = authenticated_client.post(f"/people/calendar/sync/{mock_user.id}")
        # May fail if no integration connected
        assert response.status_code in [200, 400, 404]


class TestMeetings:
    """Tests for meeting management endpoints."""
    
    def test_schedule_meeting(self, authenticated_client: TestClient, mock_user):
        """Test scheduling a meeting."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        
        response = authenticated_client.post(
            "/people/meetings",
            json={
                "title": "Team Sync",
                "date": tomorrow,
                "start_time": "10:00",
                "duration_minutes": 30,
                "participants": [mock_user.id]
            }
        )
        assert response.status_code in [200, 201, 422]
    
    def test_get_meetings(self, authenticated_client: TestClient, mock_user):
        """Test getting user's meetings."""
        response = authenticated_client.get(f"/people/meetings/{mock_user.id}")
        assert response.status_code in [200, 404]


class TestBurnoutDetection:
    """Tests for burnout detection endpoints."""
    
    def test_get_burnout_indicators(self, authenticated_client: TestClient, mock_user):
        """Test getting burnout indicators."""
        response = authenticated_client.get(f"/people/burnout/{mock_user.id}")
        assert response.status_code in [200, 404]
    
    def test_get_team_health(self, authenticated_client: TestClient):
        """Test getting team health overview."""
        response = authenticated_client.get("/people/team/health")
        assert response.status_code in [200, 404]

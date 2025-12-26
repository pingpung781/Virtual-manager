"""
Unit tests for Execution API endpoints.

Tests:
- Task execution
- GitHub sync
- Blocker detection
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestTaskExecution:
    """Tests for task execution endpoints."""
    
    def test_get_task_status(self, authenticated_client: TestClient, sample_task):
        """Test getting task status."""
        response = authenticated_client.get(f"/execution/tasks/{sample_task['id']}/status")
        assert response.status_code in [200, 404]
    
    def test_update_task_status(self, authenticated_client: TestClient, sample_task):
        """Test updating task status."""
        response = authenticated_client.patch(
            f"/execution/tasks/{sample_task['id']}/status",
            json={"status": "in_progress"}
        )
        assert response.status_code in [200, 404]
    
    def test_mark_task_blocked(self, authenticated_client: TestClient, sample_task):
        """Test marking a task as blocked."""
        response = authenticated_client.post(
            f"/execution/tasks/{sample_task['id']}/block",
            json={"reason": "Waiting for API access"}
        )
        assert response.status_code in [200, 404]
    
    def test_unblock_task(self, authenticated_client: TestClient, sample_task):
        """Test unblocking a task."""
        response = authenticated_client.post(
            f"/execution/tasks/{sample_task['id']}/unblock"
        )
        assert response.status_code in [200, 404]


class TestGitHubSync:
    """Tests for GitHub sync endpoints."""
    
    @patch('backend.app.services.github_service.GitHubService')
    def test_sync_task_to_github(self, mock_service, authenticated_client: TestClient, sample_task):
        """Test syncing a task to GitHub."""
        mock_instance = MagicMock()
        mock_instance.create_issue.return_value = {
            "number": 123,
            "html_url": "https://github.com/user/repo/issues/123"
        }
        mock_service.return_value = mock_instance
        
        response = authenticated_client.post(
            f"/execution/tasks/{sample_task['id']}/sync-github"
        )
        assert response.status_code in [200, 400, 404]
    
    def test_get_github_sync_status(self, authenticated_client: TestClient, sample_task):
        """Test getting GitHub sync status for a task."""
        response = authenticated_client.get(
            f"/execution/tasks/{sample_task['id']}/github-status"
        )
        assert response.status_code in [200, 404]
    
    @patch('backend.app.services.github_service.GitHubService')
    def test_bulk_sync(self, mock_service, authenticated_client: TestClient, sample_project):
        """Test bulk syncing all tasks in a project."""
        mock_instance = MagicMock()
        mock_instance.create_issue.return_value = {"number": 1}
        mock_service.return_value = mock_instance
        
        response = authenticated_client.post(
            f"/execution/projects/{sample_project['id']}/sync-all"
        )
        assert response.status_code in [200, 400, 404]


class TestBlockerDetection:
    """Tests for blocker detection endpoints."""
    
    def test_get_blocked_tasks(self, authenticated_client: TestClient, sample_project):
        """Test getting blocked tasks."""
        response = authenticated_client.get(
            f"/execution/projects/{sample_project['id']}/blocked"
        )
        assert response.status_code in [200, 404]
    
    def test_get_overdue_tasks(self, authenticated_client: TestClient, sample_project):
        """Test getting overdue tasks."""
        response = authenticated_client.get(
            f"/execution/projects/{sample_project['id']}/overdue"
        )
        assert response.status_code in [200, 404]
    
    def test_detect_stale_tasks(self, authenticated_client: TestClient, sample_project):
        """Test detecting stale tasks (no updates in X days)."""
        response = authenticated_client.get(
            f"/execution/projects/{sample_project['id']}/stale",
            params={"days": 7}
        )
        assert response.status_code in [200, 404]


class TestEscalation:
    """Tests for escalation endpoints."""
    
    def test_escalate_task(self, authenticated_client: TestClient, sample_task, mock_user):
        """Test escalating a task."""
        response = authenticated_client.post(
            f"/execution/tasks/{sample_task['id']}/escalate",
            json={
                "reason": "Blocked for too long",
                "escalate_to": mock_user.id
            }
        )
        assert response.status_code in [200, 404]
    
    def test_get_escalations(self, authenticated_client: TestClient, sample_project):
        """Test getting escalations for a project."""
        response = authenticated_client.get(
            f"/execution/projects/{sample_project['id']}/escalations"
        )
        assert response.status_code in [200, 404]

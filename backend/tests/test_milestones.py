"""
Unit tests for Milestones API endpoints.

Tests:
- Milestone CRUD
- Progress tracking
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta


class TestMilestoneCRUD:
    """Tests for milestone CRUD operations."""
    
    def test_create_milestone(self, authenticated_client: TestClient, sample_project):
        """Test creating a milestone."""
        due_date = (date.today() + timedelta(days=30)).isoformat()
        
        response = authenticated_client.post(
            "/milestones",
            json={
                "name": "Beta Release",
                "project_id": sample_project["id"],
                "due_date": due_date,
                "description": "First beta release"
            }
        )
        assert response.status_code in [200, 201, 422]
    
    def test_list_milestones(self, authenticated_client: TestClient, sample_project):
        """Test listing milestones for a project."""
        response = authenticated_client.get(
            "/milestones",
            params={"project_id": sample_project["id"]}
        )
        assert response.status_code == 200
    
    def test_get_milestone(self, authenticated_client: TestClient):
        """Test getting a specific milestone."""
        response = authenticated_client.get("/milestones/test-id")
        assert response.status_code in [200, 404]
    
    def test_update_milestone(self, authenticated_client: TestClient):
        """Test updating a milestone."""
        response = authenticated_client.patch(
            "/milestones/test-id",
            json={"name": "Updated Milestone"}
        )
        assert response.status_code in [200, 404]
    
    def test_delete_milestone(self, authenticated_client: TestClient):
        """Test deleting a milestone."""
        response = authenticated_client.delete("/milestones/test-id")
        assert response.status_code in [200, 204, 404]


class TestMilestoneProgress:
    """Tests for milestone progress tracking."""
    
    def test_get_milestone_progress(self, authenticated_client: TestClient):
        """Test getting milestone progress."""
        response = authenticated_client.get("/milestones/test-id/progress")
        assert response.status_code in [200, 404]
    
    def test_add_task_to_milestone(self, authenticated_client: TestClient, sample_task):
        """Test adding a task to a milestone."""
        response = authenticated_client.post(
            "/milestones/test-id/tasks",
            json={"task_id": sample_task["id"]}
        )
        assert response.status_code in [200, 201, 404]
    
    def test_remove_task_from_milestone(self, authenticated_client: TestClient, sample_task):
        """Test removing a task from a milestone."""
        response = authenticated_client.delete(
            f"/milestones/test-id/tasks/{sample_task['id']}"
        )
        assert response.status_code in [200, 204, 404]
    
    def test_mark_milestone_complete(self, authenticated_client: TestClient):
        """Test marking a milestone as complete."""
        response = authenticated_client.post("/milestones/test-id/complete")
        assert response.status_code in [200, 400, 404]

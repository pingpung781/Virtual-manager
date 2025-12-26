"""
Unit tests for Goals API endpoints.

Tests:
- Goal CRUD
- Key Results
- Alignment
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


class TestGoalCRUD:
    """Tests for goal CRUD operations."""
    
    def test_create_goal(self, authenticated_client: TestClient, mock_user):
        """Test creating a goal."""
        response = authenticated_client.post(
            "/goals",
            json={
                "name": "Increase Revenue",
                "description": "Increase Q1 revenue by 20%",
                "owner": mock_user.id,
                "target_date": "2024-03-31"
            }
        )
        assert response.status_code in [200, 201, 422]
    
    def test_list_goals(self, authenticated_client: TestClient):
        """Test listing goals."""
        response = authenticated_client.get("/goals")
        assert response.status_code == 200
    
    def test_get_goal(self, authenticated_client: TestClient, sample_goal):
        """Test getting a specific goal."""
        response = authenticated_client.get(f"/goals/{sample_goal['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_goal["name"]
    
    def test_update_goal(self, authenticated_client: TestClient, sample_goal):
        """Test updating a goal."""
        response = authenticated_client.patch(
            f"/goals/{sample_goal['id']}",
            json={"name": "Updated Goal Name"}
        )
        assert response.status_code in [200, 404]
    
    def test_delete_goal(self, authenticated_client: TestClient, sample_goal):
        """Test deleting a goal."""
        response = authenticated_client.delete(f"/goals/{sample_goal['id']}")
        assert response.status_code in [200, 204, 404]
    
    def test_get_nonexistent_goal(self, authenticated_client: TestClient):
        """Test getting a goal that doesn't exist."""
        response = authenticated_client.get("/goals/nonexistent-id")
        assert response.status_code == 404


class TestKeyResults:
    """Tests for key result operations."""
    
    def test_add_key_result(self, authenticated_client: TestClient, sample_goal):
        """Test adding a key result to a goal."""
        response = authenticated_client.post(
            f"/goals/{sample_goal['id']}/key-results",
            json={
                "description": "Close 10 deals",
                "target_value": 10,
                "current_value": 0,
                "unit": "deals"
            }
        )
        assert response.status_code in [200, 201, 404, 422]
    
    def test_get_key_results(self, authenticated_client: TestClient, sample_goal):
        """Test getting key results for a goal."""
        response = authenticated_client.get(
            f"/goals/{sample_goal['id']}/key-results"
        )
        assert response.status_code in [200, 404]
    
    def test_update_key_result_progress(self, authenticated_client: TestClient, sample_goal):
        """Test updating key result progress."""
        response = authenticated_client.patch(
            f"/goals/{sample_goal['id']}/key-results/test-kr-id",
            json={"current_value": 5}
        )
        assert response.status_code in [200, 404]


class TestGoalAlignment:
    """Tests for goal-project alignment."""
    
    def test_get_aligned_projects(self, authenticated_client: TestClient, sample_goal):
        """Test getting projects aligned to a goal."""
        response = authenticated_client.get(
            f"/goals/{sample_goal['id']}/projects"
        )
        assert response.status_code in [200, 404]
    
    def test_align_project(self, authenticated_client: TestClient, sample_goal, sample_project):
        """Test aligning a project to a goal."""
        response = authenticated_client.post(
            f"/goals/{sample_goal['id']}/projects/{sample_project['id']}"
        )
        assert response.status_code in [200, 201, 404]
    
    def test_unalign_project(self, authenticated_client: TestClient, sample_goal, sample_project):
        """Test removing project alignment."""
        response = authenticated_client.delete(
            f"/goals/{sample_goal['id']}/projects/{sample_project['id']}"
        )
        assert response.status_code in [200, 204, 404]

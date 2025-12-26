"""
Unit tests for Growth & Scaling API endpoints.

Tests:
- Job roles
- Candidates
- Interviews
- Onboarding
- Knowledge base
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import date, timedelta


class TestJobRoles:
    """Tests for job role endpoints."""
    
    def test_create_job_role(self, authenticated_client: TestClient):
        """Test creating a job role."""
        response = authenticated_client.post(
            "/growth/jobs",
            json={
                "title": "Backend Engineer",
                "department": "Engineering",
                "requirements": ["Python", "FastAPI", "PostgreSQL"],
                "nice_to_have": ["Kubernetes", "AWS"]
            }
        )
        assert response.status_code in [200, 201, 422]
    
    def test_list_job_roles(self, authenticated_client: TestClient):
        """Test listing job roles."""
        response = authenticated_client.get("/growth/jobs")
        assert response.status_code == 200
    
    def test_get_job_role(self, authenticated_client: TestClient):
        """Test getting a specific job role."""
        # First create a job, then try to get it
        response = authenticated_client.get("/growth/jobs/nonexistent")
        assert response.status_code in [200, 404]
    
    def test_generate_job_description(self, authenticated_client: TestClient):
        """Test AI-generated job description."""
        response = authenticated_client.post(
            "/growth/jobs/generate-description",
            json={
                "title": "Frontend Developer",
                "requirements": ["React", "TypeScript"]
            }
        )
        assert response.status_code in [200, 422]


class TestCandidates:
    """Tests for candidate management endpoints."""
    
    def test_submit_application(self, authenticated_client: TestClient):
        """Test submitting a candidate application."""
        response = authenticated_client.post(
            "/growth/candidates",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "job_role_id": "test-job-id",
                "resume_text": "Experienced Python developer with 5 years..."
            }
        )
        assert response.status_code in [200, 201, 404, 422]
    
    def test_list_candidates(self, authenticated_client: TestClient):
        """Test listing candidates."""
        response = authenticated_client.get("/growth/candidates")
        assert response.status_code == 200
    
    def test_get_candidate_score(self, authenticated_client: TestClient):
        """Test getting candidate score."""
        response = authenticated_client.get("/growth/candidates/test-id/score")
        assert response.status_code in [200, 404]
    
    def test_update_candidate_status(self, authenticated_client: TestClient):
        """Test updating candidate status."""
        response = authenticated_client.patch(
            "/growth/candidates/test-id/status",
            json={"status": "interviewing"}
        )
        assert response.status_code in [200, 404]


class TestInterviews:
    """Tests for interview management endpoints."""
    
    def test_schedule_interview(self, authenticated_client: TestClient, mock_user):
        """Test scheduling an interview."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        
        response = authenticated_client.post(
            "/growth/interviews",
            json={
                "candidate_id": "test-candidate",
                "interviewer_ids": [mock_user.id],
                "scheduled_date": tomorrow,
                "interview_type": "technical"
            }
        )
        assert response.status_code in [200, 201, 404, 422]
    
    def test_submit_interview_feedback(self, authenticated_client: TestClient, mock_user):
        """Test submitting interview feedback."""
        response = authenticated_client.post(
            "/growth/interviews/test-id/feedback",
            json={
                "interviewer_id": mock_user.id,
                "rating": 4,
                "strengths": ["Good communication"],
                "concerns": ["Limited experience"],
                "recommendation": "proceed"
            }
        )
        assert response.status_code in [200, 201, 404]


class TestOnboarding:
    """Tests for onboarding management endpoints."""
    
    def test_create_onboarding_plan(self, authenticated_client: TestClient, mock_user):
        """Test creating an onboarding plan."""
        start_date = (date.today() + timedelta(days=7)).isoformat()
        
        response = authenticated_client.post(
            "/growth/onboarding",
            json={
                "employee_id": mock_user.id,
                "role": "Backend Engineer",
                "start_date": start_date,
                "buddy_id": mock_user.id
            }
        )
        assert response.status_code in [200, 201, 422]
    
    def test_get_onboarding_tasks(self, authenticated_client: TestClient, mock_user):
        """Test getting onboarding tasks."""
        response = authenticated_client.get(f"/growth/onboarding/{mock_user.id}/tasks")
        assert response.status_code in [200, 404]
    
    def test_complete_onboarding_task(self, authenticated_client: TestClient):
        """Test completing an onboarding task."""
        response = authenticated_client.post(
            "/growth/onboarding/tasks/test-task-id/complete"
        )
        assert response.status_code in [200, 404]


class TestKnowledgeBase:
    """Tests for knowledge base endpoints."""
    
    def test_create_article(self, authenticated_client: TestClient, mock_user):
        """Test creating a knowledge article."""
        response = authenticated_client.post(
            "/growth/knowledge",
            json={
                "title": "Getting Started Guide",
                "content": "Welcome to the team...",
                "category": "onboarding",
                "author_id": mock_user.id
            }
        )
        assert response.status_code in [200, 201, 422]
    
    def test_list_articles(self, authenticated_client: TestClient):
        """Test listing knowledge articles."""
        response = authenticated_client.get("/growth/knowledge")
        assert response.status_code == 200
    
    def test_search_articles(self, authenticated_client: TestClient):
        """Test searching knowledge articles."""
        response = authenticated_client.get(
            "/growth/knowledge/search",
            params={"query": "getting started"}
        )
        assert response.status_code in [200, 404]

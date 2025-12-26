"""
Pytest fixtures for VAM API testing.

Provides shared fixtures for:
- FastAPI TestClient
- Mock database session
- Mock authenticated user
- Authorization headers
"""

import pytest
import uuid
from datetime import datetime
from typing import Generator, Dict, Any
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Import the FastAPI app
import sys
sys.path.insert(0, str(__file__).replace('\\tests\\conftest.py', '').replace('/tests/conftest.py', ''))

from backend.app.main import app
from backend.app.core.database import Base, get_db
from backend.app.models import User, UserRole


# ==================== DATABASE FIXTURES ====================

# In-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ==================== USER FIXTURES ====================

@pytest.fixture
def mock_user(db: Session) -> User:
    """Create a mock authenticated user."""
    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        name="Test User",
        hashed_password="hashed_password_placeholder",
        role=UserRole.ADMIN,
        github_username="testuser",
        github_id="12345",
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def contributor_user(db: Session) -> User:
    """Create a contributor-level user."""
    user = User(
        id=str(uuid.uuid4()),
        email="contributor@example.com",
        name="Contributor User",
        hashed_password="hashed",
        role=UserRole.CONTRIBUTOR,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ==================== CLIENT FIXTURES ====================

@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a TestClient with database dependency override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(mock_user: User) -> Dict[str, str]:
    """Generate authorization headers for authenticated requests."""
    # In real app, this would be a JWT token
    # For testing, we mock the auth dependency
    return {"Authorization": f"Bearer test_token_{mock_user.id}"}


@pytest.fixture
def authenticated_client(client: TestClient, mock_user: User) -> TestClient:
    """Client with mocked authentication."""
    # Mock the get_current_user dependency
    from backend.app.routers.auth import get_current_user
    
    def mock_get_current_user():
        return mock_user
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    return client


# ==================== MOCK FIXTURES ====================

@pytest.fixture
def mock_github_service():
    """Mock GitHub service for testing."""
    with patch('backend.app.services.github_service.GitHubService') as mock:
        instance = MagicMock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_slack_service():
    """Mock Slack service for testing."""
    with patch('backend.app.services.slack_service.SlackService') as mock:
        instance = MagicMock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_calendar_service():
    """Mock Google Calendar service for testing."""
    with patch('backend.app.services.google_calendar_service.GoogleCalendarService') as mock:
        instance = MagicMock()
        mock.return_value = instance
        yield instance


# ==================== DATA FIXTURES ====================

@pytest.fixture
def sample_project(db: Session, mock_user: User) -> Dict[str, Any]:
    """Create a sample project for testing."""
    from backend.app.models import Project, ProjectStatus
    
    project = Project(
        id=str(uuid.uuid4()),
        name="Test Project",
        description="A test project for unit testing",
        status=ProjectStatus.ACTIVE,
        owner=mock_user.id,
        created_at=datetime.utcnow()
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return {
        "id": project.id,
        "name": project.name,
        "status": project.status.value
    }


@pytest.fixture
def sample_task(db: Session, mock_user: User, sample_project: Dict) -> Dict[str, Any]:
    """Create a sample task for testing."""
    from backend.app.models import Task, TaskStatus, TaskPriority
    
    task = Task(
        id=str(uuid.uuid4()),
        name="Test Task",
        description="A test task",
        status=TaskStatus.NOT_STARTED,
        priority=TaskPriority.MEDIUM,
        project_id=sample_project["id"],
        owner=mock_user.id,
        created_at=datetime.utcnow()
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {
        "id": task.id,
        "name": task.name,
        "status": task.status.value
    }


@pytest.fixture
def sample_goal(db: Session, mock_user: User) -> Dict[str, Any]:
    """Create a sample goal for testing."""
    from backend.app.models import Goal, GoalStatus
    
    goal = Goal(
        id=str(uuid.uuid4()),
        name="Test Goal",
        description="Increase productivity by 20%",
        status=GoalStatus.ACTIVE,
        owner=mock_user.id,
        created_at=datetime.utcnow()
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return {
        "id": goal.id,
        "name": goal.name
    }

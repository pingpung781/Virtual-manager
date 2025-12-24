from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text, Integer, Boolean, Table
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from backend.app.core.database import Base

# ==================== ENUMS ====================

class TaskStatus(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskPriority(enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ProjectHealth(enum.Enum):
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    DELAYED = "delayed"

class GoalStatus(enum.Enum):
    ACTIVE = "active"
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    OFF_TRACK = "off_track"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class EscalationStatus(enum.Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

# ==================== ASSOCIATION TABLES ====================

# Milestone-Task many-to-many relationship
milestone_tasks = Table(
    'milestone_tasks',
    Base.metadata,
    Column('milestone_id', String, ForeignKey('milestones.id'), primary_key=True),
    Column('task_id', String, ForeignKey('tasks.id'), primary_key=True)
)

# ==================== MODELS ====================

class Goal(Base):
    """
    Strategic goals for alignment tracking.
    Maps to: Strategy & Business Planning requirements.
    """
    __tablename__ = "goals"
    
    id = Column(String, primary_key=True)
    objective = Column(Text, nullable=False)
    kpis = Column(Text)  # JSON array of KPIs/success metrics
    owner = Column(String)
    time_horizon = Column(String)  # quarterly, monthly, yearly
    is_measurable = Column(Boolean, default=False)
    missing_criteria = Column(Text)  # What's missing if not measurable
    progress_percentage = Column(Integer, default=0)
    status = Column(Enum(GoalStatus), default=GoalStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    linked_tasks = relationship("GoalTaskLink", back_populates="goal", cascade="all, delete-orphan")


class GoalTaskLink(Base):
    """
    Links goals to tasks for alignment tracking.
    Enables scope creep detection.
    """
    __tablename__ = "goal_task_links"
    
    id = Column(String, primary_key=True)
    goal_id = Column(String, ForeignKey("goals.id"), nullable=False)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    goal = relationship("Goal", back_populates="linked_tasks")
    task = relationship("Task", back_populates="goal_links")


class Project(Base):
    """Project entity with health tracking."""
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    objective = Column(Text)
    owner = Column(String, nullable=False)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    health = Column(Enum(ProjectHealth), default=ProjectHealth.ON_TRACK)
    health_reason = Column(Text)  # Explanation for health status
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="project", cascade="all, delete-orphan")


class Task(Base):
    """Task entity with full tracking capabilities."""
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    milestone_id = Column(String, ForeignKey("milestones.id"), nullable=True)
    owner = Column(String, nullable=False)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    status = Column(Enum(TaskStatus), default=TaskStatus.NOT_STARTED)
    deadline = Column(DateTime)
    estimated_hours = Column(Integer)
    actual_hours = Column(Integer)
    is_escalated = Column(Boolean, default=False)
    escalation_count = Column(Integer, default=0)
    last_update_at = Column(DateTime, default=datetime.utcnow)  # For tracking staleness
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    project = relationship("Project", back_populates="tasks")
    milestone = relationship("Milestone", back_populates="linked_tasks")
    dependencies = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.task_id",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    history = relationship("TaskHistory", back_populates="task", cascade="all, delete-orphan")
    goal_links = relationship("GoalTaskLink", back_populates="task", cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="task", cascade="all, delete-orphan")


class TaskDependency(Base):
    """Task dependency for DAG management."""
    __tablename__ = "task_dependencies"
    
    id = Column(String, primary_key=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    depends_on_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    task = relationship("Task", foreign_keys=[task_id], back_populates="dependencies")
    depends_on = relationship("Task", foreign_keys=[depends_on_id])


class TaskHistory(Base):
    """Audit trail for all task changes."""
    __tablename__ = "task_history"
    
    id = Column(String, primary_key=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    action = Column(String, nullable=False)  # created, updated, status_changed, reassigned, escalated
    field_changed = Column(String)
    old_value = Column(Text)
    new_value = Column(Text)
    trigger = Column(String)  # user, system, agent
    reason = Column(Text)
    
    task = relationship("Task", back_populates="history")


class Milestone(Base):
    """Project milestones with task linkage."""
    __tablename__ = "milestones"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    target_date = Column(DateTime)
    completion_percentage = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = relationship("Project", back_populates="milestones")
    linked_tasks = relationship("Task", back_populates="milestone")


class Escalation(Base):
    """Escalation records for overdue/blocked tasks."""
    __tablename__ = "escalations"
    
    id = Column(String, primary_key=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    reason = Column(Text, nullable=False)
    escalated_to = Column(String, nullable=False)  # manager, project_owner, etc.
    escalation_type = Column(String)  # overdue, blocked, no_update
    status = Column(Enum(EscalationStatus), default=EscalationStatus.OPEN)
    suggested_action = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    
    task = relationship("Task", back_populates="escalations")
    project = relationship("Project", back_populates="escalations")


class AgentActivity(Base):
    """Log of all agent decisions and actions."""
    __tablename__ = "agent_activities"
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    agent_name = Column(String, nullable=False)
    activity_type = Column(String, nullable=False)  # decision, action, notification, escalation
    message = Column(Text, nullable=False)
    related_task_id = Column(String, ForeignKey("tasks.id"))
    related_project_id = Column(String, ForeignKey("projects.id"))
    metadata = Column(Text)  # JSON string for additional context


class Holiday(Base):
    """Holiday/Leave calendar for deadline validation."""
    __tablename__ = "holidays"
    
    id = Column(String, primary_key=True)
    date = Column(DateTime, nullable=False)
    name = Column(String, nullable=False)
    type = Column(String)  # public_holiday, company_holiday
    applies_to = Column(String)  # all, or specific user
    created_at = Column(DateTime, default=datetime.utcnow)


class UserLeave(Base):
    """User leave records for workload planning."""
    __tablename__ = "user_leaves"
    
    id = Column(String, primary_key=True)
    user = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    leave_type = Column(String)  # vacation, sick, personal
    status = Column(String, default="approved")  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)


class DailyUpdate(Base):
    """Daily progress updates from task owners."""
    __tablename__ = "daily_updates"
    
    id = Column(String, primary_key=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    user = Column(String, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    progress_notes = Column(Text)
    hours_worked = Column(Integer, default=0)
    blockers = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
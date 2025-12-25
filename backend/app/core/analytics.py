"""
Analytics Engine - Core calculations for predictive analytics.

Provides:
- Velocity calculation from historical data
- Risk scoring model with weighted factors
- Trend analysis utilities
- Project snapshot capture
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models import (
    Task, TaskStatus, TaskPriority, Project, ProjectSnapshot, 
    Employee, UserLeave, Holiday
)


def calculate_velocity(
    db: Session,
    project_id: str,
    days: int = 30
) -> Dict[str, Any]:
    """
    Calculate task completion velocity for a project.
    
    Steps:
    1. Fetch last N days of task completions
    2. Calculate average tasks completed per week
    3. Project completion date based on remaining backlog
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Get completed tasks in period
    completed = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == TaskStatus.COMPLETED,
        Task.completed_at >= cutoff
    ).all()
    
    # Get remaining tasks
    remaining = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status.in_([TaskStatus.NOT_STARTED, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED])
    ).count()
    
    weeks = days / 7
    velocity_per_week = len(completed) / weeks if weeks > 0 else 0
    
    # Project completion
    if velocity_per_week > 0 and remaining > 0:
        weeks_to_complete = remaining / velocity_per_week
        projected_date = datetime.utcnow() + timedelta(weeks=weeks_to_complete)
    else:
        projected_date = None
        weeks_to_complete = float('inf') if remaining > 0 else 0
    
    # Calculate trend from snapshots
    trend = "stable"
    try:
        snapshots = db.query(ProjectSnapshot).filter(
            ProjectSnapshot.project_id == project_id
        ).order_by(ProjectSnapshot.snapshot_date.desc()).limit(4).all()
        
        if len(snapshots) >= 2:
            recent_velocity = snapshots[0].tasks_completed_this_period or 0
            older_velocity = snapshots[-1].tasks_completed_this_period or 0
            if recent_velocity > older_velocity * 1.2:
                trend = "increasing"
            elif recent_velocity < older_velocity * 0.8:
                trend = "decreasing"
    except:
        pass  # Snapshots table might not exist yet
    
    return {
        "project_id": project_id,
        "period_days": days,
        "tasks_completed": len(completed),
        "velocity_per_week": round(velocity_per_week, 2),
        "remaining_tasks": remaining,
        "weeks_to_complete": round(weeks_to_complete, 1) if weeks_to_complete != float('inf') else "unknown",
        "projected_completion": projected_date.isoformat() if projected_date else None,
        "trend": trend
    }


def compute_risk_score(
    db: Session,
    project_id: str
) -> Dict[str, Any]:
    """
    Compute risk score using weighted factors.
    
    Algorithm:
    - Overdue tasks: weight 5
    - Blocked tasks: weight 3
    - Team load > 90%: weight 10
    - Deadline proximity: weight 5
    
    Returns: Risk Level (LOW, MEDIUM, HIGH, CRITICAL)
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return {"error": "Project not found"}
    
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    
    if not tasks:
        return {
            "project_id": project_id,
            "project_name": project.name,
            "risk_score": 0,
            "risk_level": "low",
            "factors": []
        }
    
    score = 0
    factors = []
    
    # Overdue tasks (weight: 5 per task)
    overdue = sum(
        1 for t in tasks 
        if t.deadline and t.deadline < datetime.utcnow() 
        and t.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]
    )
    if overdue > 0:
        score += overdue * 5
        factors.append(f"{overdue} overdue tasks (+{overdue * 5})")
    
    # Blocked tasks (weight: 3 per task)
    blocked = sum(1 for t in tasks if t.status == TaskStatus.BLOCKED)
    if blocked > 0:
        score += blocked * 3
        factors.append(f"{blocked} blocked tasks (+{blocked * 3})")
    
    # Team load check
    owners = set(t.owner for t in tasks if t.owner)
    high_load_count = 0
    for owner in owners:
        owner_tasks = [t for t in tasks if t.owner == owner and t.status in [TaskStatus.IN_PROGRESS, TaskStatus.NOT_STARTED]]
        estimated_hours = sum(t.estimated_hours or 4 for t in owner_tasks)
        if estimated_hours > 36:  # > 90% of 40h week
            high_load_count += 1
    
    if high_load_count > 0:
        score += high_load_count * 10
        factors.append(f"{high_load_count} team members overloaded (+{high_load_count * 10})")
    
    # Deadline proximity for project
    if project.end_date:
        days_until = (project.end_date - datetime.utcnow()).days
        if days_until < 0:
            score += 20
            factors.append("Project overdue (+20)")
        elif days_until < 7:
            score += 15
            factors.append("Project due within a week (+15)")
        elif days_until < 14:
            score += 5
            factors.append("Project due within 2 weeks (+5)")
    
    # Determine level
    if score >= 50:
        level = "critical"
    elif score >= 30:
        level = "high"
    elif score >= 15:
        level = "medium"
    else:
        level = "low"
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "risk_score": min(score, 100),
        "risk_level": level,
        "factors": factors,
        "recommendation": _get_risk_recommendation(level, factors)
    }


def _get_risk_recommendation(level: str, factors: List[str]) -> str:
    """Generate recommendation based on risk level."""
    if level == "critical":
        return "Immediate intervention required. Consider escalation and replanning."
    elif level == "high":
        return "Prioritize blocker resolution and redistribute workload."
    elif level == "medium":
        return "Monitor closely. Address blockers proactively."
    else:
        return "Project on track. Continue normal operations."


def take_project_snapshot(db: Session, project_id: str) -> Dict[str, Any]:
    """Take a snapshot of current project state for historical tracking."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return {"error": "Project not found"}
    
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
    blocked = sum(1 for t in tasks if t.status == TaskStatus.BLOCKED)
    overdue = sum(
        1 for t in tasks 
        if t.deadline and t.deadline < datetime.utcnow()
        and t.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]
    )
    
    # Get risk score
    risk = compute_risk_score(db, project_id)
    
    # Calculate tasks completed in last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    tasks_this_period = sum(
        1 for t in tasks 
        if t.status == TaskStatus.COMPLETED 
        and t.completed_at and t.completed_at >= week_ago
    )
    
    snapshot = ProjectSnapshot(
        id=str(uuid.uuid4()),
        project_id=project_id,
        snapshot_date=datetime.utcnow(),
        completion_percentage=int((completed / total * 100) if total > 0 else 0),
        total_tasks=total,
        completed_tasks=completed,
        blocked_task_count=blocked,
        overdue_task_count=overdue,
        risk_score=risk.get("risk_score", 0),
        tasks_completed_this_period=tasks_this_period
    )
    
    db.add(snapshot)
    db.commit()
    
    return {
        "snapshot_id": snapshot.id,
        "project_id": project_id,
        "snapshot_date": snapshot.snapshot_date.isoformat(),
        "metrics": {
            "completion": snapshot.completion_percentage,
            "blocked": blocked,
            "overdue": overdue,
            "risk_score": snapshot.risk_score,
            "velocity_this_period": tasks_this_period
        }
    }

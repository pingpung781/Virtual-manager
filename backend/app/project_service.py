from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid
from backend.app.core.logging import logger
from backend.app.models import (
    Project, Task, Milestone, TaskStatus, TaskPriority, 
    ProjectHealth, TaskDependency, AgentActivity
)


class ProjectService:
    """
    Service for Project & Program Management.
    Implements: Project health tracking, DAG management, dynamic replanning.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_project(
        self,
        name: str,
        owner: str,
        objective: Optional[str] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        end_date: Optional[datetime] = None
    ) -> Project:
        """Create a new project."""
        project_id = str(uuid.uuid4())
        project = Project(
            id=project_id,
            name=name,
            owner=owner,
            objective=objective,
            priority=priority,
            end_date=end_date
        )
        self.db.add(project)
        
        self._log_activity(
            agent_name="ProjectManager",
            activity_type="action",
            message=f"Created project '{name}' owned by {owner}",
            related_project_id=project_id
        )
        
        self.db.commit()
        self.db.refresh(project)
        return project
    
    def calculate_health(self, project_id: str) -> Dict[str, Any]:
        """
        Calculate project health from:
        - Task completion rate
        - Blockers count
        - Deadline variance
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        tasks = self.db.query(Task).filter(Task.project_id == project_id).all()
        
        if not tasks:
            return {
                "health": ProjectHealth.ON_TRACK,
                "reason": "No tasks in project",
                "metrics": {}
            }
        
        total_tasks = len(tasks)
        completed = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
        blocked = len([t for t in tasks if t.status == TaskStatus.BLOCKED])
        
        # Check overdue tasks
        now = datetime.utcnow()
        overdue = len([t for t in tasks if t.deadline and t.deadline < now 
                       and t.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]])
        
        completion_rate = (completed / total_tasks) * 100 if total_tasks > 0 else 0
        blocker_rate = (blocked / total_tasks) * 100 if total_tasks > 0 else 0
        overdue_rate = (overdue / total_tasks) * 100 if total_tasks > 0 else 0
        
        # Calculate expected progress based on timeline
        expected_progress = 0
        if project.start_date and project.end_date:
            total_duration = (project.end_date - project.start_date).days
            elapsed = (now - project.start_date).days
            if total_duration > 0:
                expected_progress = min(100, (elapsed / total_duration) * 100)
        
        # Determine health status
        health = ProjectHealth.ON_TRACK
        reason = "Project is progressing normally"
        
        if overdue_rate > 20 or blocker_rate > 30:
            health = ProjectHealth.DELAYED
            reason = f"High overdue ({overdue_rate:.1f}%) or blocker rate ({blocker_rate:.1f}%)"
        elif overdue_rate > 10 or blocker_rate > 15 or (expected_progress - completion_rate) > 20:
            health = ProjectHealth.AT_RISK
            reason = f"Behind schedule or elevated blockers"
        
        # Update project health
        project.health = health
        project.health_reason = reason
        self.db.commit()
        
        return {
            "health": health.value,
            "reason": reason,
            "metrics": {
                "total_tasks": total_tasks,
                "completed_tasks": completed,
                "blocked_tasks": blocked,
                "overdue_tasks": overdue,
                "completion_rate": round(completion_rate, 1),
                "expected_progress": round(expected_progress, 1)
            }
        }
    
    def get_dependency_graph(self, project_id: str) -> Dict[str, Any]:
        """
        Get the task dependency graph (DAG) for a project.
        Returns nodes (tasks) and edges (dependencies).
        """
        tasks = self.db.query(Task).filter(Task.project_id == project_id).all()
        
        nodes = []
        edges = []
        
        for task in tasks:
            nodes.append({
                "id": task.id,
                "name": task.name,
                "status": task.status.value,
                "priority": task.priority.value,
                "owner": task.owner
            })
            
            for dep in task.dependencies:
                edges.append({
                    "from": task.id,
                    "to": dep.depends_on_id
                })
        
        return {
            "project_id": project_id,
            "nodes": nodes,
            "edges": edges,
            "task_count": len(nodes),
            "dependency_count": len(edges)
        }
    
    def suggest_replan(self, project_id: str, trigger_reason: str) -> Dict[str, Any]:
        """
        Suggest replanning when critical task is delayed or resource unavailable.
        Returns trade-off analysis and recommended actions.
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        tasks = self.db.query(Task).filter(
            Task.project_id == project_id,
            Task.status.not_in([TaskStatus.COMPLETED, TaskStatus.CANCELLED])
        ).all()
        
        blocked_tasks = [t for t in tasks if t.status == TaskStatus.BLOCKED]
        critical_tasks = [t for t in tasks if t.priority == TaskPriority.CRITICAL]
        overdue_tasks = [t for t in tasks if t.deadline and t.deadline < datetime.utcnow()]
        
        suggestions = []
        
        # Suggest unblocking actions
        for task in blocked_tasks:
            suggestions.append({
                "type": "unblock",
                "task_id": task.id,
                "task_name": task.name,
                "action": f"Review dependencies for '{task.name}' and escalate if needed"
            })
        
        # Suggest deadline extensions for overdue
        for task in overdue_tasks:
            if task not in blocked_tasks:
                suggestions.append({
                    "type": "reschedule",
                    "task_id": task.id,
                    "task_name": task.name,
                    "action": f"Extend deadline for '{task.name}' or reassign to available resource"
                })
        
        # Flag critical tasks at risk
        for task in critical_tasks:
            if task.status in [TaskStatus.BLOCKED, TaskStatus.NOT_STARTED]:
                suggestions.append({
                    "type": "prioritize",
                    "task_id": task.id,
                    "task_name": task.name,
                    "action": f"Critical task '{task.name}' needs immediate attention"
                })
        
        self._log_activity(
            agent_name="PlanningAgent",
            activity_type="decision",
            message=f"Replan triggered: {trigger_reason}. Generated {len(suggestions)} suggestions.",
            related_project_id=project_id
        )
        
        return {
            "trigger": trigger_reason,
            "project_id": project_id,
            "project_name": project.name,
            "suggestions": suggestions,
            "requires_approval": len(critical_tasks) > 0
        }
    
    def _log_activity(
        self,
        agent_name: str,
        activity_type: str,
        message: str,
        related_task_id: Optional[str] = None,
        related_project_id: Optional[str] = None
    ):
        activity = AgentActivity(
            id=str(uuid.uuid4()),
            agent_name=agent_name,
            activity_type=activity_type,
            message=message,
            related_task_id=related_task_id,
            related_project_id=related_project_id
        )
        self.db.add(activity)

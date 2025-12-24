from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid
from backend.app.core.logging import logger
from backend.app.models import (
    Milestone, Task, TaskStatus, AgentActivity
)


class MilestoneService:
    """
    Service for Milestone management.
    Implements: Milestone CRUD, progress tracking, task linkage.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_milestone(
        self,
        project_id: str,
        name: str,
        description: Optional[str] = None,
        target_date: Optional[datetime] = None
    ) -> Milestone:
        """Create a new milestone."""
        milestone_id = str(uuid.uuid4())
        milestone = Milestone(
            id=milestone_id,
            project_id=project_id,
            name=name,
            description=description,
            target_date=target_date
        )
        self.db.add(milestone)
        
        self._log_activity(
            agent_name="ProjectManager",
            activity_type="action",
            message=f"Created milestone '{name}' for project"
        )
        
        self.db.commit()
        self.db.refresh(milestone)
        return milestone
    
    def link_tasks(self, milestone_id: str, task_ids: List[str]) -> Dict[str, Any]:
        """Link tasks to a milestone."""
        milestone = self.db.query(Milestone).filter(Milestone.id == milestone_id).first()
        if not milestone:
            raise ValueError(f"Milestone {milestone_id} not found")
        
        linked_count = 0
        for task_id in task_ids:
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.milestone_id = milestone_id
                linked_count += 1
        
        self.db.commit()
        
        # Update milestone progress
        self.update_progress(milestone_id)
        
        return {
            "milestone_id": milestone_id,
            "tasks_linked": linked_count
        }
    
    def unlink_task(self, task_id: str) -> bool:
        """Remove a task from its milestone."""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if task and task.milestone_id:
            old_milestone_id = task.milestone_id
            task.milestone_id = None
            self.db.commit()
            
            # Update the old milestone's progress
            self.update_progress(old_milestone_id)
            return True
        return False
    
    def update_progress(self, milestone_id: str) -> Milestone:
        """
        Recalculate milestone completion percentage based on linked tasks.
        """
        milestone = self.db.query(Milestone).filter(Milestone.id == milestone_id).first()
        if not milestone:
            raise ValueError(f"Milestone {milestone_id} not found")
        
        tasks = self.db.query(Task).filter(Task.milestone_id == milestone_id).all()
        
        if not tasks:
            milestone.completion_percentage = 0
        else:
            completed = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
            milestone.completion_percentage = int((completed / len(tasks)) * 100)
        
        # Check if milestone is complete
        if milestone.completion_percentage == 100 and not milestone.is_completed:
            milestone.is_completed = True
            milestone.completed_at = datetime.utcnow()
            
            self._log_activity(
                agent_name="ProjectManager",
                activity_type="notification",
                message=f"Milestone '{milestone.name}' completed!"
            )
        
        milestone.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(milestone)
        
        return milestone
    
    def get_milestone_status(self, milestone_id: str) -> Dict[str, Any]:
        """Get detailed milestone status."""
        milestone = self.db.query(Milestone).filter(Milestone.id == milestone_id).first()
        if not milestone:
            raise ValueError(f"Milestone {milestone_id} not found")
        
        tasks = self.db.query(Task).filter(Task.milestone_id == milestone_id).all()
        
        task_breakdown = {
            "total": len(tasks),
            "not_started": len([t for t in tasks if t.status == TaskStatus.NOT_STARTED]),
            "in_progress": len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS]),
            "blocked": len([t for t in tasks if t.status == TaskStatus.BLOCKED]),
            "completed": len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
            "cancelled": len([t for t in tasks if t.status == TaskStatus.CANCELLED])
        }
        
        # Check if at risk
        at_risk = False
        risk_reason = None
        if milestone.target_date:
            days_remaining = (milestone.target_date - datetime.utcnow()).days
            if days_remaining < 0:
                at_risk = True
                risk_reason = "Milestone is overdue"
            elif days_remaining < 7 and milestone.completion_percentage < 80:
                at_risk = True
                risk_reason = f"Only {days_remaining} days remaining with {milestone.completion_percentage}% complete"
        
        if task_breakdown["blocked"] > 0:
            at_risk = True
            risk_reason = f"{task_breakdown['blocked']} tasks are blocked"
        
        return {
            "id": milestone.id,
            "name": milestone.name,
            "target_date": milestone.target_date.isoformat() if milestone.target_date else None,
            "completion_percentage": milestone.completion_percentage,
            "is_completed": milestone.is_completed,
            "at_risk": at_risk,
            "risk_reason": risk_reason,
            "task_breakdown": task_breakdown
        }
    
    def get_project_milestones(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all milestones for a project with their status."""
        milestones = self.db.query(Milestone).filter(
            Milestone.project_id == project_id
        ).order_by(Milestone.target_date).all()
        
        return [self.get_milestone_status(m.id) for m in milestones]
    
    def _log_activity(
        self,
        agent_name: str,
        activity_type: str,
        message: str
    ):
        activity = AgentActivity(
            id=str(uuid.uuid4()),
            agent_name=agent_name,
            activity_type=activity_type,
            message=message
        )
        self.db.add(activity)

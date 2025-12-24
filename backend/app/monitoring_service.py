from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid
import json
from backend.app.core.logging import logger
from backend.app.models import (
    Task, Project, Escalation, EscalationStatus, TaskStatus, TaskPriority,
    AgentActivity, DailyUpdate, TaskHistory
)


class ExecutionMonitor:
    """
    Service for Execution Monitoring & Control.
    Implements: Daily tracking, blocker detection, escalation, reminders.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.stale_threshold_hours = 48  # Hours without update before flagging
        self.blocked_threshold_hours = 24  # Hours blocked before escalation
    
    def collect_daily_summary(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Collect daily status of all active tasks.
        """
        query = self.db.query(Task).filter(
            Task.status.in_([TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED, TaskStatus.NOT_STARTED])
        )
        
        if project_id:
            query = query.filter(Task.project_id == project_id)
        
        tasks = query.all()
        
        summary = {
            "date": datetime.utcnow().date().isoformat(),
            "total_active": len(tasks),
            "in_progress": [],
            "blocked": [],
            "not_started": [],
            "needs_attention": []
        }
        
        now = datetime.utcnow()
        
        for task in tasks:
            task_info = {
                "id": task.id,
                "name": task.name,
                "owner": task.owner,
                "priority": task.priority.value,
                "deadline": task.deadline.isoformat() if task.deadline else None,
                "last_update": task.last_update_at.isoformat() if task.last_update_at else None
            }
            
            if task.status == TaskStatus.IN_PROGRESS:
                summary["in_progress"].append(task_info)
            elif task.status == TaskStatus.BLOCKED:
                summary["blocked"].append(task_info)
            else:
                summary["not_started"].append(task_info)
            
            # Check if needs attention
            hours_since_update = (now - task.last_update_at).total_seconds() / 3600 if task.last_update_at else 999
            is_overdue = task.deadline and task.deadline < now
            
            if hours_since_update > self.stale_threshold_hours or is_overdue:
                summary["needs_attention"].append({
                    **task_info,
                    "reason": "overdue" if is_overdue else "stale"
                })
        
        return summary
    
    def detect_missing_updates(self, threshold_hours: int = 48) -> List[Dict[str, Any]]:
        """
        Find tasks with no updates beyond threshold.
        """
        cutoff = datetime.utcnow() - timedelta(hours=threshold_hours)
        
        stale_tasks = self.db.query(Task).filter(
            Task.status.in_([TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED]),
            Task.last_update_at < cutoff
        ).all()
        
        return [{
            "id": task.id,
            "name": task.name,
            "owner": task.owner,
            "project_id": task.project_id,
            "status": task.status.value,
            "last_update": task.last_update_at.isoformat() if task.last_update_at else None,
            "hours_since_update": int((datetime.utcnow() - task.last_update_at).total_seconds() / 3600) if task.last_update_at else None
        } for task in stale_tasks]
    
    def detect_blockers(self) -> List[Dict[str, Any]]:
        """
        Identify blocked tasks with analysis.
        """
        blocked_tasks = self.db.query(Task).filter(
            Task.status == TaskStatus.BLOCKED
        ).all()
        
        result = []
        for task in blocked_tasks:
            # Check how long it's been blocked
            last_status_change = self.db.query(TaskHistory).filter(
                TaskHistory.task_id == task.id,
                TaskHistory.field_changed == "status",
                TaskHistory.new_value == "blocked"
            ).order_by(TaskHistory.timestamp.desc()).first()
            
            blocked_since = last_status_change.timestamp if last_status_change else task.updated_at
            hours_blocked = (datetime.utcnow() - blocked_since).total_seconds() / 3600
            
            # Check dependencies
            blocking_tasks = []
            for dep in task.dependencies:
                dep_task = dep.depends_on
                if dep_task.status != TaskStatus.COMPLETED:
                    blocking_tasks.append({
                        "id": dep_task.id,
                        "name": dep_task.name,
                        "status": dep_task.status.value
                    })
            
            result.append({
                "id": task.id,
                "name": task.name,
                "owner": task.owner,
                "project_id": task.project_id,
                "priority": task.priority.value,
                "hours_blocked": round(hours_blocked, 1),
                "blocked_since": blocked_since.isoformat(),
                "blocking_tasks": blocking_tasks,
                "needs_escalation": hours_blocked > self.blocked_threshold_hours
            })
        
        return result
    
    def generate_weekly_summary(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate weekly progress report.
        """
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Query base
        task_query = self.db.query(Task)
        if project_id:
            task_query = task_query.filter(Task.project_id == project_id)
        
        all_tasks = task_query.all()
        
        # Completed this week
        completed_this_week = [t for t in all_tasks 
                               if t.completed_at and t.completed_at > week_ago]
        
        # Currently blocked
        blocked = [t for t in all_tasks if t.status == TaskStatus.BLOCKED]
        
        # Overdue
        now = datetime.utcnow()
        overdue = [t for t in all_tasks 
                   if t.deadline and t.deadline < now 
                   and t.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]]
        
        # Next week priorities (by deadline)
        next_week = now + timedelta(days=7)
        upcoming = [t for t in all_tasks 
                    if t.deadline and now <= t.deadline <= next_week
                    and t.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]]
        
        # Calculate velocity
        velocity = len(completed_this_week)
        
        return {
            "period": {
                "start": week_ago.date().isoformat(),
                "end": now.date().isoformat()
            },
            "completed": {
                "count": len(completed_this_week),
                "tasks": [{"id": t.id, "name": t.name, "owner": t.owner} for t in completed_this_week]
            },
            "blocked": {
                "count": len(blocked),
                "tasks": [{"id": t.id, "name": t.name, "owner": t.owner} for t in blocked]
            },
            "overdue": {
                "count": len(overdue),
                "tasks": [{"id": t.id, "name": t.name, "owner": t.owner, 
                          "deadline": t.deadline.isoformat()} for t in overdue]
            },
            "next_week_priorities": {
                "count": len(upcoming),
                "tasks": [{"id": t.id, "name": t.name, "owner": t.owner,
                          "deadline": t.deadline.isoformat(), "priority": t.priority.value} 
                         for t in sorted(upcoming, key=lambda x: (x.priority.value != "critical", x.deadline))]
            },
            "velocity": velocity,
            "health_indicators": {
                "blocked_rate": round(len(blocked) / len(all_tasks) * 100, 1) if all_tasks else 0,
                "overdue_rate": round(len(overdue) / len(all_tasks) * 100, 1) if all_tasks else 0
            }
        }
    
    def escalate_task(
        self,
        task_id: str,
        reason: str,
        escalate_to: str = "project_owner",
        suggested_action: Optional[str] = None
    ) -> Escalation:
        """
        Create an escalation for a task.
        """
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        escalation = Escalation(
            id=str(uuid.uuid4()),
            task_id=task_id,
            project_id=task.project_id,
            reason=reason,
            escalated_to=escalate_to,
            escalation_type=self._determine_escalation_type(task),
            suggested_action=suggested_action or self._suggest_action(task)
        )
        
        self.db.add(escalation)
        
        # Update task
        task.is_escalated = True
        task.escalation_count += 1
        
        # Log activity
        self._log_activity(
            agent_name="ExecutionAgent",
            activity_type="escalation",
            message=f"Escalated task '{task.name}': {reason}",
            related_task_id=task_id,
            related_project_id=task.project_id
        )
        
        self.db.commit()
        self.db.refresh(escalation)
        
        return escalation
    
    def acknowledge_escalation(self, escalation_id: str) -> Escalation:
        """Acknowledge an escalation."""
        escalation = self.db.query(Escalation).filter(Escalation.id == escalation_id).first()
        if not escalation:
            raise ValueError(f"Escalation {escalation_id} not found")
        
        escalation.status = EscalationStatus.ACKNOWLEDGED
        escalation.acknowledged_at = datetime.utcnow()
        self.db.commit()
        
        return escalation
    
    def resolve_escalation(self, escalation_id: str, resolution_notes: str) -> Escalation:
        """Resolve an escalation."""
        escalation = self.db.query(Escalation).filter(Escalation.id == escalation_id).first()
        if not escalation:
            raise ValueError(f"Escalation {escalation_id} not found")
        
        escalation.status = EscalationStatus.RESOLVED
        escalation.resolved_at = datetime.utcnow()
        escalation.resolution_notes = resolution_notes
        
        # Update task
        if escalation.task_id:
            task = self.db.query(Task).filter(Task.id == escalation.task_id).first()
            if task:
                task.is_escalated = False
        
        self.db.commit()
        
        return escalation
    
    def get_open_escalations(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all open escalations."""
        query = self.db.query(Escalation).filter(
            Escalation.status.in_([EscalationStatus.OPEN, EscalationStatus.ACKNOWLEDGED])
        )
        
        if project_id:
            query = query.filter(Escalation.project_id == project_id)
        
        escalations = query.order_by(Escalation.created_at.desc()).all()
        
        return [{
            "id": e.id,
            "task_id": e.task_id,
            "project_id": e.project_id,
            "reason": e.reason,
            "escalated_to": e.escalated_to,
            "type": e.escalation_type,
            "status": e.status.value,
            "suggested_action": e.suggested_action,
            "created_at": e.created_at.isoformat(),
            "acknowledged_at": e.acknowledged_at.isoformat() if e.acknowledged_at else None
        } for e in escalations]
    
    def record_daily_update(
        self,
        task_id: str,
        user: str,
        progress_notes: str,
        hours_worked: int = 0,
        blockers: Optional[str] = None
    ) -> DailyUpdate:
        """Record a daily progress update."""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        update = DailyUpdate(
            id=str(uuid.uuid4()),
            task_id=task_id,
            user=user,
            progress_notes=progress_notes,
            hours_worked=hours_worked,
            blockers=blockers
        )
        
        self.db.add(update)
        
        # Update task's last_update_at
        task.last_update_at = datetime.utcnow()
        if hours_worked:
            task.actual_hours = (task.actual_hours or 0) + hours_worked
        
        self.db.commit()
        self.db.refresh(update)
        
        return update
    
    def _determine_escalation_type(self, task: Task) -> str:
        """Determine the type of escalation based on task state."""
        if task.status == TaskStatus.BLOCKED:
            return "blocked"
        elif task.deadline and task.deadline < datetime.utcnow():
            return "overdue"
        else:
            return "no_update"
    
    def _suggest_action(self, task: Task) -> str:
        """Generate suggested action for escalation."""
        if task.status == TaskStatus.BLOCKED:
            return f"Review blocking dependencies and unblock or reassign '{task.name}'"
        elif task.deadline and task.deadline < datetime.utcnow():
            return f"Extend deadline or add resources to complete '{task.name}'"
        else:
            return f"Contact {task.owner} for status update on '{task.name}'"
    
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

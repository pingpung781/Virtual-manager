from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid
import json
from backend.app.core.logging import logger
from backend.app.models import (
    Goal, GoalTaskLink, Task, TaskStatus, GoalStatus, AgentActivity
)


class GoalService:
    """
    Service for Goal/Strategy management.
    Implements: Goal tracking, task alignment, scope creep detection.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_goal(
        self,
        objective: str,
        kpis: List[str],
        owner: Optional[str] = None,
        time_horizon: str = "quarterly",
        is_measurable: bool = True,
        missing_criteria: Optional[str] = None
    ) -> Goal:
        """Create a new strategic goal."""
        goal_id = str(uuid.uuid4())
        goal = Goal(
            id=goal_id,
            objective=objective,
            kpis=json.dumps(kpis),
            owner=owner,
            time_horizon=time_horizon,
            is_measurable=is_measurable,
            missing_criteria=missing_criteria
        )
        self.db.add(goal)
        
        self._log_activity(
            agent_name="ManagerialAgent",
            activity_type="action",
            message=f"Created strategic goal: '{objective[:50]}...'"
        )
        
        self.db.commit()
        self.db.refresh(goal)
        return goal
    
    def link_task_to_goal(self, goal_id: str, task_id: str) -> GoalTaskLink:
        """Link a task to a goal for alignment tracking."""
        # Validate both exist
        goal = self.db.query(Goal).filter(Goal.id == goal_id).first()
        task = self.db.query(Task).filter(Task.id == task_id).first()
        
        if not goal:
            raise ValueError(f"Goal {goal_id} not found")
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Check if already linked
        existing = self.db.query(GoalTaskLink).filter(
            GoalTaskLink.goal_id == goal_id,
            GoalTaskLink.task_id == task_id
        ).first()
        
        if existing:
            return existing
        
        link = GoalTaskLink(
            id=str(uuid.uuid4()),
            goal_id=goal_id,
            task_id=task_id
        )
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        
        return link
    
    def unlink_task(self, goal_id: str, task_id: str) -> bool:
        """Remove task from goal alignment."""
        link = self.db.query(GoalTaskLink).filter(
            GoalTaskLink.goal_id == goal_id,
            GoalTaskLink.task_id == task_id
        ).first()
        
        if link:
            self.db.delete(link)
            self.db.commit()
            return True
        return False
    
    def calculate_goal_progress(self, goal_id: str) -> Dict[str, Any]:
        """
        Calculate goal progress from linked task completion.
        """
        goal = self.db.query(Goal).filter(Goal.id == goal_id).first()
        if not goal:
            raise ValueError(f"Goal {goal_id} not found")
        
        links = self.db.query(GoalTaskLink).filter(GoalTaskLink.goal_id == goal_id).all()
        
        if not links:
            return {
                "goal_id": goal_id,
                "objective": goal.objective,
                "progress": 0,
                "status": goal.status.value,
                "linked_tasks": 0,
                "completed_tasks": 0
            }
        
        task_ids = [link.task_id for link in links]
        tasks = self.db.query(Task).filter(Task.id.in_(task_ids)).all()
        
        total = len(tasks)
        completed = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
        blocked = len([t for t in tasks if t.status == TaskStatus.BLOCKED])
        
        progress = int((completed / total) * 100) if total > 0 else 0
        
        # Update goal progress
        goal.progress_percentage = progress
        
        # Determine goal status
        if progress == 100:
            goal.status = GoalStatus.COMPLETED
        elif blocked > total * 0.3:  # >30% blocked
            goal.status = GoalStatus.AT_RISK
        elif progress < 50 and goal.time_horizon == "quarterly":
            # Simple heuristic - should be more sophisticated
            goal.status = GoalStatus.AT_RISK
        else:
            goal.status = GoalStatus.ON_TRACK
        
        self.db.commit()
        
        return {
            "goal_id": goal_id,
            "objective": goal.objective,
            "progress": progress,
            "status": goal.status.value,
            "linked_tasks": total,
            "completed_tasks": completed,
            "blocked_tasks": blocked
        }
    
    def detect_scope_creep(self) -> List[Dict[str, Any]]:
        """
        Identify tasks not linked to any goal (potential scope creep).
        """
        # Get all active tasks
        active_tasks = self.db.query(Task).filter(
            Task.status.not_in([TaskStatus.COMPLETED, TaskStatus.CANCELLED])
        ).all()
        
        # Get all linked task IDs
        linked_task_ids = set(
            link.task_id for link in self.db.query(GoalTaskLink).all()
        )
        
        # Find unaligned tasks
        unaligned = []
        for task in active_tasks:
            if task.id not in linked_task_ids:
                unaligned.append({
                    "id": task.id,
                    "name": task.name,
                    "project_id": task.project_id,
                    "owner": task.owner,
                    "priority": task.priority.value,
                    "created_at": task.created_at.isoformat(),
                    "recommendation": "Review and align with a goal or deprioritize"
                })
        
        if unaligned:
            self._log_activity(
                agent_name="ManagerialAgent",
                activity_type="decision",
                message=f"Scope creep detected: {len(unaligned)} tasks not aligned to any goal"
            )
        
        return unaligned
    
    def check_task_alignment(self, task_id: str) -> Dict[str, Any]:
        """Check if a specific task is aligned with goals."""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        links = self.db.query(GoalTaskLink).filter(GoalTaskLink.task_id == task_id).all()
        
        if not links:
            return {
                "task_id": task_id,
                "task_name": task.name,
                "is_aligned": False,
                "linked_goals": [],
                "recommendation": "Link to a strategic goal or review for deprioritization"
            }
        
        goals = []
        for link in links:
            goal = self.db.query(Goal).filter(Goal.id == link.goal_id).first()
            if goal:
                goals.append({
                    "id": goal.id,
                    "objective": goal.objective,
                    "status": goal.status.value
                })
        
        return {
            "task_id": task_id,
            "task_name": task.name,
            "is_aligned": True,
            "linked_goals": goals,
            "recommendation": None
        }
    
    def suggest_deprioritization(self, capacity_constraint: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Suggest tasks for deprioritization when capacity is constrained.
        Prioritizes low-impact, unaligned tasks.
        """
        # Get unaligned tasks first
        unaligned = self.detect_scope_creep()
        
        # Get low priority tasks
        low_priority = self.db.query(Task).filter(
            Task.priority.in_(["low", "medium"]),
            Task.status.not_in([TaskStatus.COMPLETED, TaskStatus.CANCELLED])
        ).all()
        
        suggestions = []
        
        # First suggest unaligned tasks
        for task_info in unaligned:
            suggestions.append({
                **task_info,
                "deprioritization_reason": "Not aligned with any strategic goal",
                "impact": "low",
                "risk": "minimal scope reduction"
            })
        
        # Then low priority aligned tasks
        unaligned_ids = {t["id"] for t in unaligned}
        for task in low_priority:
            if task.id not in unaligned_ids:
                suggestions.append({
                    "id": task.id,
                    "name": task.name,
                    "project_id": task.project_id,
                    "owner": task.owner,
                    "priority": task.priority.value,
                    "deprioritization_reason": "Low priority with flexible deadline",
                    "impact": "low",
                    "risk": "may delay dependent work"
                })
        
        # Apply capacity constraint if provided
        if capacity_constraint and len(suggestions) > capacity_constraint:
            suggestions = suggestions[:capacity_constraint]
        
        return suggestions
    
    def get_all_goals(self, include_completed: bool = False) -> List[Dict[str, Any]]:
        """Get all goals with progress."""
        query = self.db.query(Goal)
        if not include_completed:
            query = query.filter(Goal.status != GoalStatus.COMPLETED)
        
        goals = query.order_by(Goal.created_at.desc()).all()
        
        return [self.calculate_goal_progress(g.id) for g in goals]
    
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

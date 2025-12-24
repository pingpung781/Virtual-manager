"""
People Operations Agent - Resource Management and Workload Balancing.

Implements:
- Workload analysis
- Skill matching
- Leave management
- Resource recommendations
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.app.models import (
    Task, TaskStatus, TaskPriority, UserLeave, Holiday, AgentActivity
)
import uuid


class PeopleOpsAgent:
    """
    People Operations Agent for resource and workload management.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_workload(self, user: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze current workload distribution.
        
        Args:
            user: Optional specific user to analyze
        
        Returns:
            Workload analysis with recommendations
        """
        query = self.db.query(Task).filter(
            Task.status.in_([TaskStatus.IN_PROGRESS, TaskStatus.NOT_STARTED, TaskStatus.BLOCKED])
        )
        
        if user:
            query = query.filter(Task.owner == user)
            tasks = query.all()
            
            return self._analyze_user_workload(user, tasks)
        
        # Analyze all users
        tasks = query.all()
        workload_by_user = {}
        
        for task in tasks:
            if task.owner not in workload_by_user:
                workload_by_user[task.owner] = {
                    "tasks": [],
                    "total_estimated_hours": 0,
                    "critical_count": 0,
                    "blocked_count": 0
                }
            
            workload_by_user[task.owner]["tasks"].append({
                "id": task.id,
                "name": task.name,
                "priority": task.priority.value,
                "status": task.status.value,
                "deadline": task.deadline.isoformat() if task.deadline else None
            })
            workload_by_user[task.owner]["total_estimated_hours"] += task.estimated_hours or 4
            
            if task.priority == TaskPriority.CRITICAL:
                workload_by_user[task.owner]["critical_count"] += 1
            if task.status == TaskStatus.BLOCKED:
                workload_by_user[task.owner]["blocked_count"] += 1
        
        # Calculate statistics
        workloads = []
        for owner, data in workload_by_user.items():
            workloads.append({
                "user": owner,
                "task_count": len(data["tasks"]),
                "estimated_hours": data["total_estimated_hours"],
                "critical_tasks": data["critical_count"],
                "blocked_tasks": data["blocked_count"],
                "is_overloaded": data["total_estimated_hours"] > 40  # Weekly capacity
            })
        
        workloads.sort(key=lambda x: x["estimated_hours"], reverse=True)
        
        overloaded = [w for w in workloads if w["is_overloaded"]]
        underloaded = [w for w in workloads if w["estimated_hours"] < 20]
        
        recommendations = []
        if overloaded and underloaded:
            recommendations.append(
                f"Consider redistributing tasks from {overloaded[0]['user']} to {underloaded[0]['user']}"
            )
        
        return {
            "total_active_tasks": len(tasks),
            "team_members": len(workloads),
            "workload_distribution": workloads,
            "overloaded_members": [w["user"] for w in overloaded],
            "available_capacity": [w["user"] for w in underloaded],
            "recommendations": recommendations
        }
    
    def _analyze_user_workload(self, user: str, tasks: List[Task]) -> Dict[str, Any]:
        """Analyze workload for a specific user."""
        total_hours = sum(t.estimated_hours or 4 for t in tasks)
        
        by_priority = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        
        for task in tasks:
            by_priority[task.priority.value].append({
                "id": task.id,
                "name": task.name,
                "status": task.status.value,
                "deadline": task.deadline.isoformat() if task.deadline else None
            })
        
        # Check upcoming deadlines
        now = datetime.utcnow()
        week_ahead = now + timedelta(days=7)
        urgent = [t for t in tasks if t.deadline and now <= t.deadline <= week_ahead]
        
        return {
            "user": user,
            "total_tasks": len(tasks),
            "estimated_hours": total_hours,
            "capacity_used_percentage": min(100, int((total_hours / 40) * 100)),
            "by_priority": by_priority,
            "urgent_this_week": len(urgent),
            "is_overloaded": total_hours > 40,
            "recommendation": self._get_workload_recommendation(total_hours, len(tasks))
        }
    
    def _get_workload_recommendation(self, hours: int, task_count: int) -> str:
        """Generate workload recommendation."""
        if hours > 50:
            return "Severely overloaded - immediate task redistribution needed"
        elif hours > 40:
            return "At capacity - avoid adding new tasks"
        elif hours > 30:
            return "Good workload - maintaining productivity"
        elif hours > 15:
            return "Light workload - available for additional tasks"
        else:
            return "Underutilized - can take on significantly more work"
    
    def suggest_assignment(
        self,
        task_name: str,
        required_skills: Optional[List[str]] = None,
        priority: str = "medium",
        estimated_hours: int = 8
    ) -> Dict[str, Any]:
        """
        Suggest the best person to assign a task to.
        
        Args:
            task_name: Name of the task
            required_skills: Skills needed
            priority: Task priority
            estimated_hours: Estimated hours to complete
        
        Returns:
            Assignment suggestion with reasoning
        """
        # Get current workload
        workload_analysis = self.analyze_workload()
        
        candidates = []
        for member in workload_analysis["workload_distribution"]:
            # Skip overloaded members for non-critical tasks
            if member["is_overloaded"] and priority != "critical":
                continue
            
            # Calculate capacity score (lower is better)
            capacity_score = member["estimated_hours"]
            
            # Adjust for blocked tasks (prefer people with fewer blockers)
            capacity_score += member["blocked_tasks"] * 4
            
            candidates.append({
                "user": member["user"],
                "capacity_score": capacity_score,
                "current_load": member["estimated_hours"],
                "task_count": member["task_count"]
            })
        
        if not candidates:
            return {
                "task_name": task_name,
                "suggestion": None,
                "reason": "All team members are overloaded",
                "alternatives": []
            }
        
        # Sort by capacity score
        candidates.sort(key=lambda x: x["capacity_score"])
        
        best = candidates[0]
        
        return {
            "task_name": task_name,
            "suggestion": best["user"],
            "reason": f"Best available capacity ({best['current_load']}h current load)",
            "new_load": best["current_load"] + estimated_hours,
            "alternatives": [c["user"] for c in candidates[1:3]]
        }
    
    def check_availability(
        self,
        user: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Check if a user is available during a date range.
        
        Args:
            user: User to check
            start_date: Start of period
            end_date: End of period
        
        Returns:
            Availability information
        """
        # Check leaves
        leaves = self.db.query(UserLeave).filter(
            UserLeave.user == user,
            UserLeave.status == "approved",
            UserLeave.start_date <= end_date,
            UserLeave.end_date >= start_date
        ).all()
        
        # Check holidays
        holidays = self.db.query(Holiday).filter(
            Holiday.date >= start_date,
            Holiday.date <= end_date
        ).all()
        
        unavailable_dates = []
        
        for leave in leaves:
            unavailable_dates.append({
                "type": "leave",
                "start": leave.start_date.isoformat(),
                "end": leave.end_date.isoformat(),
                "reason": leave.leave_type
            })
        
        for holiday in holidays:
            unavailable_dates.append({
                "type": "holiday",
                "date": holiday.date.isoformat(),
                "name": holiday.name
            })
        
        # Calculate available days
        total_days = (end_date - start_date).days + 1
        unavailable_days = len(set(
            d["date"] if d["type"] == "holiday" else d["start"] 
            for d in unavailable_dates
        ))
        
        return {
            "user": user,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "is_available": len(unavailable_dates) == 0,
            "unavailable_periods": unavailable_dates,
            "available_days": total_days - unavailable_days,
            "total_days": total_days
        }
    
    def record_leave(
        self,
        user: str,
        start_date: datetime,
        end_date: datetime,
        leave_type: str = "vacation",
        status: str = "approved"
    ) -> UserLeave:
        """Record a user leave."""
        leave = UserLeave(
            id=str(uuid.uuid4()),
            user=user,
            start_date=start_date,
            end_date=end_date,
            leave_type=leave_type,
            status=status
        )
        self.db.add(leave)
        
        self._log_activity(
            f"Recorded {leave_type} leave for {user}: {start_date.date()} to {end_date.date()}"
        )
        
        self.db.commit()
        self.db.refresh(leave)
        return leave
    
    def get_team_calendar(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get team availability calendar."""
        # Get all leaves in period
        leaves = self.db.query(UserLeave).filter(
            UserLeave.status == "approved",
            UserLeave.start_date <= end_date,
            UserLeave.end_date >= start_date
        ).all()
        
        # Get holidays
        holidays = self.db.query(Holiday).filter(
            Holiday.date >= start_date,
            Holiday.date <= end_date
        ).all()
        
        calendar = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "holidays": [{
                "date": h.date.isoformat(),
                "name": h.name
            } for h in holidays],
            "leaves": [{
                "user": l.user,
                "start": l.start_date.isoformat(),
                "end": l.end_date.isoformat(),
                "type": l.leave_type
            } for l in leaves]
        }
        
        return calendar
    
    def _log_activity(self, message: str):
        """Log people ops activity."""
        activity = AgentActivity(
            id=str(uuid.uuid4()),
            agent_name="PeopleOpsAgent",
            activity_type="action",
            message=message
        )
        self.db.add(activity)

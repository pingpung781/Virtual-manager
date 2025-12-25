"""
Growth Logic - Core module for hiring workflows.

Handles:
- Candidate skill matching and scoring
- Automated onboarding task generation
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.models import (
    JobRole, Candidate, OnboardingPlan, OnboardingTask, Task, 
    TaskStatus, TaskPriority, Project
)


def score_candidate(
    resume_text: str,
    job_requirements: List[str]
) -> Dict[str, Any]:
    """
    Score candidate resume against job requirements.
    
    Uses keyword matching to compare candidate skills against requirements.
    Returns match score (0-100) to help prioritize screening.
    
    Future enhancement: Use pgvector for cosine similarity.
    """
    if not resume_text or not job_requirements:
        return {"score": 0, "matches": [], "missing": job_requirements or []}
    
    resume_lower = resume_text.lower()
    
    matches = []
    missing = []
    
    for req in job_requirements:
        # Check for exact or partial keyword match
        req_lower = req.lower()
        keywords = req_lower.split()
        
        # Match if any significant keyword (>2 chars) is found
        matched = any(kw in resume_lower for kw in keywords if len(kw) > 2)
        
        if matched:
            matches.append(req)
        else:
            missing.append(req)
    
    # Calculate score
    total = len(job_requirements)
    matched_count = len(matches)
    score = int((matched_count / total) * 100) if total > 0 else 0
    
    return {
        "score": score,
        "matches": matches,
        "missing": missing,
        "match_percentage": f"{matched_count}/{total} requirements",
        "recommendation": _get_score_recommendation(score)
    }


def _get_score_recommendation(score: int) -> str:
    """Get recommendation based on score."""
    if score >= 80:
        return "Strong match - prioritize for screening"
    elif score >= 60:
        return "Good match - include in screening pool"
    elif score >= 40:
        return "Partial match - review manually"
    else:
        return "Low match - consider for future roles"


def generate_onboarding_tasks(
    db: Session,
    plan_id: str,
    employee_name: str,
    role: str,
    start_date: datetime,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate standard onboarding tasks for a new hire.
    
    Creates Task objects with predefined templates:
    - Day 1: IT Setup, Team Intro
    - Day 7: First Code Commit
    - Day 30: Completion of First Project
    
    Bulk inserts into task system.
    """
    templates = [
        # Day 1 tasks
        {
            "name": "Complete IT Setup",
            "description": "Set up laptop, accounts, VPN, and required tools",
            "day": 1,
            "category": "account_setup",
            "priority": "high"
        },
        {
            "name": "Team Introduction Meeting",
            "description": "Meet with team members and understand team dynamics",
            "day": 1,
            "category": "assignment",
            "priority": "high"
        },
        {
            "name": "Review Company Policies",
            "description": "Read through employee handbook and security policies",
            "day": 1,
            "category": "documentation",
            "priority": "medium"
        },
        # Week 1 tasks
        {
            "name": "Development Environment Setup",
            "description": "Clone repositories, set up local development environment",
            "day": 3,
            "category": "tool_access",
            "priority": "high"
        },
        {
            "name": "First Code Commit",
            "description": "Make first contribution to codebase (fix or small feature)",
            "day": 7,
            "category": "assignment",
            "priority": "medium"
        },
        {
            "name": "1:1 with Manager",
            "description": "Initial sync on expectations, goals, and questions",
            "day": 7,
            "category": "assignment",
            "priority": "high"
        },
        # Month 1 tasks
        {
            "name": "Complete Core Training",
            "description": "Finish all required training modules for role",
            "day": 14,
            "category": "documentation",
            "priority": "medium"
        },
        {
            "name": "Shadow Senior Team Member",
            "description": "Pair with experienced colleague on a real task",
            "day": 14,
            "category": "assignment",
            "priority": "medium"
        },
        {
            "name": "Complete First Project/Feature",
            "description": "Deliver first end-to-end project or feature",
            "day": 30,
            "category": "assignment",
            "priority": "high"
        },
        {
            "name": "30-Day Review",
            "description": "Review progress against onboarding goals with manager",
            "day": 30,
            "category": "assignment",
            "priority": "high"
        }
    ]
    
    created_tasks = []
    onboarding_tasks = []
    
    for template in templates:
        task_deadline = start_date + timedelta(days=template["day"])
        
        # Create OnboardingTask
        ob_task = OnboardingTask(
            id=str(uuid.uuid4()),
            plan_id=plan_id,
            title=template["name"],
            description=template["description"],
            category=template["category"],
            day_due=template["day"],
            is_completed=False
        )
        db.add(ob_task)
        onboarding_tasks.append(ob_task)
        
        # Create as regular Task if project provided
        if project_id:
            task = Task(
                id=str(uuid.uuid4()),
                name=f"[Onboarding] {template['name']}",
                description=template["description"],
                project_id=project_id,
                owner=employee_name,
                priority=TaskPriority(template["priority"]),
                status=TaskStatus.NOT_STARTED,
                deadline=task_deadline,
                estimated_hours=4
            )
            db.add(task)
            created_tasks.append({
                "id": task.id,
                "name": task.name,
                "day": template["day"],
                "deadline": task_deadline.isoformat()
            })
    
    db.commit()
    
    return {
        "plan_id": plan_id,
        "onboarding_tasks_created": len(onboarding_tasks),
        "project_tasks_created": len(created_tasks),
        "tasks": created_tasks if created_tasks else [{"title": t.title, "day": t.day_due} for t in onboarding_tasks],
        "timeline": {
            "day_1": [t["name"] for t in templates if t["day"] == 1],
            "week_1": [t["name"] for t in templates if 1 < t["day"] <= 7],
            "month_1": [t["name"] for t in templates if t["day"] > 7]
        }
    }

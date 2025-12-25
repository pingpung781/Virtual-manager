"""
Growth Service - CRUD operations for hiring lifecycle.

Handles:
- Job role creation
- Application processing with scoring
- Onboarding activation
"""

import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.models import (
    JobRole, JobRoleStatus, Candidate, CandidateStage,
    OnboardingPlan, OnboardingStatus, Employee
)
from backend.app.core.growth_logic import score_candidate, generate_onboarding_tasks


def create_job_role(
    db: Session,
    title: str,
    team: str,
    responsibilities: List[str],
    required_skills: List[str],
    nice_to_have_skills: Optional[List[str]] = None,
    experience_years: int = 0,
    seniority_level: str = "mid",
    location: Optional[str] = None,
    work_mode: str = "hybrid"
) -> Dict[str, Any]:
    """Create a new job role opening."""
    role = JobRole(
        id=str(uuid.uuid4()),
        title=title,
        team=team,
        responsibilities=json.dumps(responsibilities),
        required_skills=json.dumps(required_skills),
        nice_to_have_skills=json.dumps(nice_to_have_skills or []),
        experience_years=experience_years,
        seniority_level=seniority_level,
        location=location,
        work_mode=work_mode,
        status=JobRoleStatus.DRAFT
    )
    
    db.add(role)
    db.commit()
    
    return {
        "role_id": role.id,
        "title": title,
        "status": "draft",
        "next_step": "Generate job description and approve for posting"
    }


def process_application(
    db: Session,
    job_role_id: str,
    name: str,
    email: str,
    resume_text: str,
    source: str = "website"
) -> Dict[str, Any]:
    """
    Process a candidate application.
    
    Steps:
    1. Parse resume text
    2. Calculate match score against requirements
    3. Save candidate with score
    """
    role = db.query(JobRole).filter(JobRole.id == job_role_id).first()
    if not role:
        return {"success": False, "error": "Job role not found"}
    
    # Get requirements
    requirements = []
    if role.required_skills:
        try:
            requirements = json.loads(role.required_skills)
        except:
            requirements = []
    
    # Score candidate
    scoring = score_candidate(resume_text, requirements)
    
    # Create candidate
    candidate = Candidate(
        id=str(uuid.uuid4()),
        job_role_id=job_role_id,
        name=name,
        email=email,
        stage=CandidateStage.APPLIED,
        source=source,
        skills_match_score=scoring["score"],
        notes=f"Auto-scored: {scoring['match_percentage']}"
    )
    
    db.add(candidate)
    db.commit()
    
    return {
        "success": True,
        "candidate_id": candidate.id,
        "name": name,
        "role": role.title,
        "scoring": scoring,
        "next_step": "Review candidate and update stage"
    }


def start_onboarding(
    db: Session,
    employee_id: str,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Activate onboarding for a new hire.
    
    Steps:
    1. Find employee and their onboarding plan
    2. Generate onboarding tasks
    3. Activate the plan
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        return {"success": False, "error": "Employee not found"}
    
    plan = db.query(OnboardingPlan).filter(
        OnboardingPlan.employee_id == employee_id,
        OnboardingPlan.status == OnboardingStatus.NOT_STARTED
    ).first()
    
    if not plan:
        return {"success": False, "error": "No pending onboarding plan found"}
    
    # Generate tasks
    tasks_result = generate_onboarding_tasks(
        db=db,
        plan_id=plan.id,
        employee_name=employee.name,
        role=plan.role,
        start_date=plan.start_date,
        project_id=project_id
    )
    
    # Activate plan
    plan.status = OnboardingStatus.IN_PROGRESS
    db.commit()
    
    return {
        "success": True,
        "plan_id": plan.id,
        "employee": employee.name,
        "status": "in_progress",
        "tasks": tasks_result
    }

"""
Growth & Scaling API Routes.

Provides REST API endpoints for:
- Job role management
- Candidate pipeline
- Interview scheduling
- Onboarding plans
- Knowledge base
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from backend.app.core.database import get_db
from backend.app.agents.growth_scaling import GrowthScalingAgent


router = APIRouter(prefix="/api/v1/growth", tags=["Growth & Scaling"])


# ==================== PYDANTIC SCHEMAS ====================

class RoleCreate(BaseModel):
    title: str
    team: str
    responsibilities: List[str]
    required_skills: List[str]
    nice_to_have_skills: Optional[List[str]] = None
    experience_years: int = 0
    seniority_level: str = "mid"
    location: Optional[str] = None
    work_mode: str = "hybrid"
    reports_to: Optional[str] = None
    success_criteria: Optional[List[str]] = None


class RoleApproval(BaseModel):
    approved_by: str


class CandidateCreate(BaseModel):
    job_role_id: str
    name: str
    email: str
    phone: Optional[str] = None
    resume_url: Optional[str] = None
    source: str = "website"


class StageUpdate(BaseModel):
    new_stage: str
    notes: Optional[str] = None
    approved_by: Optional[str] = None  # Required for rejections


class InterviewCreate(BaseModel):
    candidate_id: str
    interviewers: List[str]
    scheduled_time: datetime
    interview_type: str = "technical"
    duration_minutes: int = 60
    location: Optional[str] = None
    agenda: Optional[str] = None


class FeedbackSubmit(BaseModel):
    feedback: List[dict]
    strengths: List[str]
    concerns: List[str]
    recommendation: str  # strong_hire, hire, no_hire, strong_no_hire


class OnboardingPlanCreate(BaseModel):
    employee_id: str
    role: str
    start_date: datetime
    buddy_name: Optional[str] = None
    mentor_name: Optional[str] = None


class ArticleCreate(BaseModel):
    title: str
    content: str
    category: str
    author: str
    tags: Optional[List[str]] = None
    target_roles: Optional[List[str]] = None


class OutdatedFlag(BaseModel):
    reason: str


# ==================== JOB ROLE ENDPOINTS ====================

@router.post("/jobs")
def create_job_role(
    role: RoleCreate,
    db: Session = Depends(get_db)
):
    """Define role requirements for a new position."""
    agent = GrowthScalingAgent(db)
    return agent.define_role_requirements(
        title=role.title,
        team=role.team,
        responsibilities=role.responsibilities,
        required_skills=role.required_skills,
        nice_to_have_skills=role.nice_to_have_skills,
        experience_years=role.experience_years,
        seniority_level=role.seniority_level,
        location=role.location,
        work_mode=role.work_mode,
        reports_to=role.reports_to,
        success_criteria=role.success_criteria
    )


@router.get("/jobs")
def list_open_roles(db: Session = Depends(get_db)):
    """List all open job roles."""
    agent = GrowthScalingAgent(db)
    return agent.get_open_roles()


@router.get("/jobs/{role_id}")
def get_job_role(role_id: str, db: Session = Depends(get_db)):
    """Get job role details."""
    from backend.app.models import JobRole
    role = db.query(JobRole).filter(JobRole.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return {
        "id": role.id,
        "title": role.title,
        "team": role.team,
        "status": role.status.value,
        "job_description": role.job_description,
        "is_approved": role.is_approved
    }


@router.post("/jobs/{role_id}/description")
def generate_job_description(role_id: str, db: Session = Depends(get_db)):
    """Generate job description from role requirements."""
    agent = GrowthScalingAgent(db)
    result = agent.generate_job_description(role_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/jobs/{role_id}/approve")
def approve_job(
    role_id: str,
    approval: RoleApproval,
    db: Session = Depends(get_db)
):
    """Approve a job for posting (human approval required)."""
    agent = GrowthScalingAgent(db)
    result = agent.approve_job_posting(role_id, approval.approved_by)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ==================== CANDIDATE ENDPOINTS ====================

@router.post("/candidates")
def add_candidate(
    candidate: CandidateCreate,
    db: Session = Depends(get_db)
):
    """Add a new candidate to the pipeline."""
    agent = GrowthScalingAgent(db)
    result = agent.add_candidate(
        job_role_id=candidate.job_role_id,
        name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        resume_url=candidate.resume_url,
        source=candidate.source
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/candidates/pipeline")
def get_pipeline(
    job_role_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get candidate pipeline grouped by stage."""
    agent = GrowthScalingAgent(db)
    return agent.get_candidate_pipeline(job_role_id)


@router.put("/candidates/{candidate_id}/stage")
def update_stage(
    candidate_id: str,
    update: StageUpdate,
    db: Session = Depends(get_db)
):
    """Update candidate stage in the pipeline."""
    agent = GrowthScalingAgent(db)
    result = agent.update_candidate_stage(
        candidate_id=candidate_id,
        new_stage=update.new_stage,
        notes=update.notes,
        approved_by=update.approved_by
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    return result


# ==================== INTERVIEW ENDPOINTS ====================

@router.post("/interviews")
def schedule_interview(
    interview: InterviewCreate,
    db: Session = Depends(get_db)
):
    """Schedule a new interview."""
    agent = GrowthScalingAgent(db)
    result = agent.schedule_interview(
        candidate_id=interview.candidate_id,
        interviewers=interview.interviewers,
        scheduled_time=interview.scheduled_time,
        interview_type=interview.interview_type,
        duration_minutes=interview.duration_minutes,
        location=interview.location,
        agenda=interview.agenda
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/interviews")
def list_interviews(
    candidate_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List interviews."""
    from backend.app.models import Interview
    query = db.query(Interview)
    if candidate_id:
        query = query.filter(Interview.candidate_id == candidate_id)
    
    interviews = query.all()
    return [{
        "id": i.id,
        "candidate_id": i.candidate_id,
        "round": i.round_number,
        "type": i.interview_type,
        "scheduled_time": i.scheduled_time.isoformat(),
        "status": i.status.value
    } for i in interviews]


@router.post("/interviews/{interview_id}/feedback")
def submit_feedback(
    interview_id: str,
    feedback: FeedbackSubmit,
    db: Session = Depends(get_db)
):
    """Submit interview feedback."""
    agent = GrowthScalingAgent(db)
    result = agent.record_interview_feedback(
        interview_id=interview_id,
        feedback=feedback.feedback,
        strengths=feedback.strengths,
        concerns=feedback.concerns,
        recommendation=feedback.recommendation
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ==================== ONBOARDING ENDPOINTS ====================

@router.post("/onboarding")
def create_onboarding_plan(
    plan: OnboardingPlanCreate,
    db: Session = Depends(get_db)
):
    """Generate onboarding plan for a new hire."""
    agent = GrowthScalingAgent(db)
    result = agent.generate_onboarding_plan(
        employee_id=plan.employee_id,
        role=plan.role,
        start_date=plan.start_date,
        buddy_name=plan.buddy_name,
        mentor_name=plan.mentor_name
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/onboarding")
def list_onboarding_plans(db: Session = Depends(get_db)):
    """List all onboarding plans."""
    from backend.app.models import OnboardingPlan
    plans = db.query(OnboardingPlan).all()
    return [{
        "id": p.id,
        "employee_id": p.employee_id,
        "role": p.role,
        "status": p.status.value,
        "completion_percentage": p.completion_percentage
    } for p in plans]


@router.post("/onboarding/{plan_id}/tasks")
def assign_tasks(plan_id: str, db: Session = Depends(get_db)):
    """Assign standard onboarding tasks."""
    agent = GrowthScalingAgent(db)
    result = agent.assign_onboarding_tasks(plan_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/onboarding/{plan_id}/progress")
def get_progress(plan_id: str, db: Session = Depends(get_db)):
    """Get onboarding progress."""
    agent = GrowthScalingAgent(db)
    result = agent.get_onboarding_progress(plan_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ==================== KNOWLEDGE BASE ENDPOINTS ====================

@router.post("/knowledge")
def create_article(
    article: ArticleCreate,
    db: Session = Depends(get_db)
):
    """Add a new knowledge base article."""
    agent = GrowthScalingAgent(db)
    return agent.add_knowledge_article(
        title=article.title,
        content=article.content,
        category=article.category,
        author=article.author,
        tags=article.tags,
        target_roles=article.target_roles
    )


@router.get("/knowledge/search")
def search_articles(
    query: str,
    category: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Search the knowledge base."""
    agent = GrowthScalingAgent(db)
    return agent.search_knowledge_base(query, category, limit)


@router.get("/knowledge/role/{role}")
def get_role_docs(role: str, db: Session = Depends(get_db)):
    """Get curated documentation for a role."""
    agent = GrowthScalingAgent(db)
    return agent.get_role_documentation(role)


@router.post("/knowledge/{article_id}/outdated")
def flag_outdated(
    article_id: str,
    flag: OutdatedFlag,
    db: Session = Depends(get_db)
):
    """Flag an article as outdated."""
    agent = GrowthScalingAgent(db)
    result = agent.flag_outdated_article(article_id, flag.reason)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

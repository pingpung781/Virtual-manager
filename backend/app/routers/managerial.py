from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from backend.app.core.database import get_db
from backend.app.agents.strategy import StrategyAgent
from backend.app.agents.risk import RiskAgent

router = APIRouter(prefix="/managerial", tags=["managerial-intelligence"])


# ==================== SCHEMAS ====================

class GoalCreateRequest(BaseModel):
    text: str
    owner: Optional[str] = None


class AlignProjectRequest(BaseModel):
    project_id: str
    goal_id: str


class AskRequest(BaseModel):
    question: str
    project_id: Optional[str] = None


# ==================== STRATEGY ENDPOINTS ====================

@router.post("/goals")
async def create_goal(
    request: GoalCreateRequest,
    db: Session = Depends(get_db)
):
    """Create structured goal from text using AI."""
    agent = StrategyAgent(db)
    result = agent.create_goal_from_text(request.text, request.owner)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/goals/{goal_id}/alignment")
async def get_goal_alignment(
    goal_id: str,
    db: Session = Depends(get_db)
):
    """Get projects aligned to a goal and identify unaligned projects."""
    agent = StrategyAgent(db)
    result = agent.get_goal_alignment(goal_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/projects/{project_id}/align")
async def align_project_to_goal(
    project_id: str,
    request: AlignProjectRequest,
    db: Session = Depends(get_db)
):
    """Link a project to a strategic goal."""
    agent = StrategyAgent(db)
    result = agent.align_project_to_goal(project_id, request.goal_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/projects/{project_id}/scope-creep")
async def detect_scope_creep(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Detect if project is not aligned to any active goal (scope creep)."""
    agent = StrategyAgent(db)
    result = agent.detect_scope_creep(project_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ==================== RISK ENDPOINTS ====================

@router.post("/analyze/risk/{project_id}")
async def analyze_project_risk(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Force a risk assessment run on a project."""
    agent = RiskAgent(db)
    result = agent.assess_project_risk(project_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/risks/{project_id}")
async def get_project_risks(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get active risks for a project."""
    agent = RiskAgent(db)
    return agent.get_project_risks(project_id)


@router.post("/risks/{risk_id}/mitigate")
async def mitigate_risk(
    risk_id: str,
    resolution_notes: str,
    db: Session = Depends(get_db)
):
    """Mark a risk as mitigated."""
    agent = RiskAgent(db)
    result = agent.mitigate_risk(risk_id, resolution_notes)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ==================== COMMUNICATION ENDPOINTS ====================

@router.get("/standup")
async def get_daily_standup(
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Generate daily standup summary from database activity."""
    from backend.app.agents.communication import CommunicationAgent
    agent = CommunicationAgent()
    
    # For now, return basic standup - we'd integrate with DB here
    return {
        "message": "Standup generation requires integration with task history",
        "project_id": project_id
    }


@router.post("/ask")
async def ask_question(
    request: AskRequest,
    db: Session = Depends(get_db)
):
    """General Q&A endpoint - answer questions about projects."""
    from backend.app.agents.communication import CommunicationAgent
    agent = CommunicationAgent()
    
    # Gather context from DB
    context = {}
    if request.project_id:
        from backend.app.models import Project, Task
        project = db.query(Project).filter(Project.id == request.project_id).first()
        if project:
            context["project"] = project.name
            tasks = db.query(Task).filter(Task.project_id == request.project_id).limit(10).all()
            context["tasks"] = [{"name": t.name, "status": t.status.value} for t in tasks]
    
    # Use existing communication agent
    return agent.answer_stakeholder_query(request.question, context) if hasattr(agent, 'answer_stakeholder_query') else {
        "question": request.question,
        "answer": "Q&A functionality requires LLM configuration"
    }
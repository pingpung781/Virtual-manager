from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from backend.app.core.database import get_db
from backend.app.goal_service import GoalService

router = APIRouter(prefix="/goals", tags=["goals"])


# ==================== SCHEMAS ====================

class GoalCreate(BaseModel):
    objective: str
    kpis: List[str]
    owner: Optional[str] = None
    time_horizon: str = "quarterly"
    is_measurable: bool = True
    missing_criteria: Optional[str] = None


class GoalResponse(BaseModel):
    goal_id: str
    objective: str
    progress: int
    status: str
    linked_tasks: int
    completed_tasks: int
    
    class Config:
        from_attributes = True


class TaskLinkRequest(BaseModel):
    task_id: str


class AlignmentResponse(BaseModel):
    task_id: str
    task_name: str
    is_aligned: bool
    linked_goals: List[dict]
    recommendation: Optional[str]


class ScopeCreepItem(BaseModel):
    id: str
    name: str
    project_id: str
    owner: str
    priority: str
    recommendation: str


# ==================== ENDPOINTS ====================

@router.post("/", response_model=GoalResponse)
async def create_goal(goal: GoalCreate, db: Session = Depends(get_db)):
    """Create a new strategic goal."""
    service = GoalService(db)
    created = service.create_goal(
        objective=goal.objective,
        kpis=goal.kpis,
        owner=goal.owner,
        time_horizon=goal.time_horizon,
        is_measurable=goal.is_measurable,
        missing_criteria=goal.missing_criteria
    )
    return service.calculate_goal_progress(created.id)


@router.get("/", response_model=List[GoalResponse])
async def list_goals(
    include_completed: bool = False,
    db: Session = Depends(get_db)
):
    """List all goals with progress."""
    service = GoalService(db)
    return service.get_all_goals(include_completed)


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(goal_id: str, db: Session = Depends(get_db)):
    """Get a specific goal with progress."""
    service = GoalService(db)
    try:
        return service.calculate_goal_progress(goal_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{goal_id}/link-task")
async def link_task_to_goal(
    goal_id: str,
    request: TaskLinkRequest,
    db: Session = Depends(get_db)
):
    """Link a task to a goal."""
    service = GoalService(db)
    try:
        link = service.link_task_to_goal(goal_id, request.task_id)
        return {"message": "Task linked successfully", "link_id": link.id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{goal_id}/unlink-task/{task_id}")
async def unlink_task_from_goal(
    goal_id: str,
    task_id: str,
    db: Session = Depends(get_db)
):
    """Remove a task from goal alignment."""
    service = GoalService(db)
    success = service.unlink_task(goal_id, task_id)
    if success:
        return {"message": "Task unlinked successfully"}
    raise HTTPException(status_code=404, detail="Link not found")


@router.get("/alignment/check/{task_id}", response_model=AlignmentResponse)
async def check_task_alignment(task_id: str, db: Session = Depends(get_db)):
    """Check if a task is aligned with any goals."""
    service = GoalService(db)
    try:
        return service.check_task_alignment(task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/scope-creep/detect", response_model=List[ScopeCreepItem])
async def detect_scope_creep(db: Session = Depends(get_db)):
    """Detect tasks not aligned with any goal (potential scope creep)."""
    service = GoalService(db)
    return service.detect_scope_creep()


@router.get("/deprioritization/suggestions")
async def get_deprioritization_suggestions(
    capacity_limit: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get suggestions for tasks to deprioritize when capacity is constrained."""
    service = GoalService(db)
    return service.suggest_deprioritization(capacity_limit)

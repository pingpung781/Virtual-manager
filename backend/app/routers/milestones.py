from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from backend.app.core.database import get_db
from backend.app.milestone_service import MilestoneService

router = APIRouter(prefix="/milestones", tags=["milestones"])


# ==================== SCHEMAS ====================

class MilestoneCreate(BaseModel):
    project_id: str
    name: str
    description: Optional[str] = None
    target_date: Optional[datetime] = None


class MilestoneResponse(BaseModel):
    id: str
    name: str
    target_date: Optional[str]
    completion_percentage: int
    is_completed: bool
    at_risk: bool
    risk_reason: Optional[str]
    task_breakdown: dict
    
    class Config:
        from_attributes = True


class TaskLinkRequest(BaseModel):
    task_ids: List[str]


# ==================== ENDPOINTS ====================

@router.post("/", response_model=MilestoneResponse)
async def create_milestone(milestone: MilestoneCreate, db: Session = Depends(get_db)):
    """Create a new milestone."""
    service = MilestoneService(db)
    created = service.create_milestone(
        project_id=milestone.project_id,
        name=milestone.name,
        description=milestone.description,
        target_date=milestone.target_date
    )
    return service.get_milestone_status(created.id)


@router.get("/{milestone_id}", response_model=MilestoneResponse)
async def get_milestone(milestone_id: str, db: Session = Depends(get_db)):
    """Get milestone status."""
    service = MilestoneService(db)
    try:
        return service.get_milestone_status(milestone_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/project/{project_id}", response_model=List[MilestoneResponse])
async def get_project_milestones(project_id: str, db: Session = Depends(get_db)):
    """Get all milestones for a project."""
    service = MilestoneService(db)
    return service.get_project_milestones(project_id)


@router.post("/{milestone_id}/link-tasks")
async def link_tasks_to_milestone(
    milestone_id: str,
    request: TaskLinkRequest,
    db: Session = Depends(get_db)
):
    """Link tasks to a milestone."""
    service = MilestoneService(db)
    try:
        result = service.link_tasks(milestone_id, request.task_ids)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{milestone_id}/unlink-task/{task_id}")
async def unlink_task_from_milestone(
    milestone_id: str,
    task_id: str,
    db: Session = Depends(get_db)
):
    """Remove a task from a milestone."""
    service = MilestoneService(db)
    success = service.unlink_task(task_id)
    if success:
        return {"message": "Task unlinked successfully"}
    raise HTTPException(status_code=404, detail="Task not linked to milestone")


@router.post("/{milestone_id}/refresh-progress", response_model=MilestoneResponse)
async def refresh_milestone_progress(milestone_id: str, db: Session = Depends(get_db)):
    """Manually refresh milestone progress calculation."""
    service = MilestoneService(db)
    try:
        service.update_progress(milestone_id)
        return service.get_milestone_status(milestone_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

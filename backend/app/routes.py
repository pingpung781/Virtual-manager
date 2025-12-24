from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from backend.app.core.database import get_db
from backend.app.task_service import TaskService
from backend.app.project_service import ProjectService
from backend.app.models import TaskStatus, TaskPriority, ProjectHealth

router = APIRouter(prefix="/api/v1", tags=["VAM"])


# ==================== PYDANTIC SCHEMAS ====================

class TaskCreate(BaseModel):
    name: str
    project_id: str
    owner: str
    description: Optional[str] = None
    priority: str = "medium"
    deadline: Optional[datetime] = None
    milestone_id: Optional[str] = None


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    deadline: Optional[datetime] = None


class TaskReassign(BaseModel):
    new_owner: str
    reason: str


class TaskExtractRequest(BaseModel):
    text: str
    project_id: str
    default_owner: Optional[str] = None


class DeadlineValidation(BaseModel):
    proposed_deadline: datetime


class ProjectCreate(BaseModel):
    name: str
    owner: str
    objective: Optional[str] = None
    priority: str = "medium"
    end_date: Optional[datetime] = None


class TaskResponse(BaseModel):
    id: str
    name: str
    project_id: str
    owner: str
    priority: str
    status: str
    deadline: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    id: str
    name: str
    owner: str
    objective: Optional[str]
    priority: str
    health: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class AgentActivityResponse(BaseModel):
    id: str
    timestamp: datetime
    agent_name: str
    activity_type: str
    message: str
    
    class Config:
        from_attributes = True


# ==================== PROJECT ENDPOINTS ====================

@router.post("/projects", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project."""
    service = ProjectService(db)
    created = service.create_project(
        name=project.name,
        owner=project.owner,
        objective=project.objective,
        priority=TaskPriority[project.priority.upper()],
        end_date=project.end_date
    )
    return created


@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(db: Session = Depends(get_db)):
    """List all projects."""
    from backend.app.models import Project
    
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return projects


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get project by ID."""
    from backend.app.models import Project
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project


@router.get("/projects/{project_id}/health")
async def get_project_health(project_id: str, db: Session = Depends(get_db)):
    """Get project health status with metrics."""
    service = ProjectService(db)
    try:
        return service.calculate_health(project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/projects/{project_id}/dag")
async def get_project_dag(project_id: str, db: Session = Depends(get_db)):
    """Get project dependency graph."""
    service = ProjectService(db)
    return service.get_dependency_graph(project_id)


@router.post("/projects/{project_id}/replan")
async def trigger_replan(
    project_id: str,
    trigger_reason: str = "Manual trigger",
    db: Session = Depends(get_db)
):
    """Trigger replanning for a project."""
    service = ProjectService(db)
    try:
        return service.suggest_replan(project_id, trigger_reason)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== TASK ENDPOINTS ====================

@router.post("/tasks", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    service = TaskService(db)
    
    try:
        priority = TaskPriority[task.priority.upper()]
        db_task = service.create_task(
            name=task.name,
            project_id=task.project_id,
            owner=task.owner,
            description=task.description,
            priority=priority,
            deadline=task.deadline,
            milestone_id=task.milestone_id,
            trigger="user"
        )
        return db_task
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    owner: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List tasks with optional filters."""
    from backend.app.models import Task
    
    query = db.query(Task)
    
    if project_id:
        query = query.filter(Task.project_id == project_id)
    
    if owner:
        query = query.filter(Task.owner == owner)
    
    if status:
        try:
            status_enum = TaskStatus[status.upper()]
            query = query.filter(Task.status == status_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid status")
    
    tasks = query.order_by(Task.created_at.desc()).all()
    return tasks


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get task by ID."""
    from backend.app.models import Task
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    db: Session = Depends(get_db)
):
    """Update a task."""
    from backend.app.models import Task
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    service = TaskService(db)
    
    if task_update.name:
        task.name = task_update.name
    
    if task_update.description:
        task.description = task_update.description
    
    if task_update.owner:
        task.owner = task_update.owner
    
    if task_update.priority:
        task.priority = TaskPriority[task_update.priority.upper()]
    
    if task_update.deadline:
        task.deadline = task_update.deadline
    
    if task_update.status:
        status_enum = TaskStatus[task_update.status.upper()]
        service.update_task_status(task_id, status_enum, trigger="user")
    else:
        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
    
    return task


@router.post("/tasks/{task_id}/reassign", response_model=TaskResponse)
async def reassign_task(
    task_id: str,
    request: TaskReassign,
    db: Session = Depends(get_db)
):
    """Reassign a task to a new owner."""
    service = TaskService(db)
    try:
        return service.reassign_task(task_id, request.new_owner, request.reason)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/tasks/{task_id}/validate-deadline")
async def validate_task_deadline(
    task_id: str,
    request: DeadlineValidation,
    db: Session = Depends(get_db)
):
    """Validate a proposed deadline for a task."""
    service = TaskService(db)
    try:
        return service.validate_deadline(task_id, request.proposed_deadline)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/tasks/{task_id}/history")
async def get_task_history(task_id: str, db: Session = Depends(get_db)):
    """Get full history of a task."""
    service = TaskService(db)
    return service.get_task_history(task_id)


@router.post("/tasks/{task_id}/dependencies/{depends_on_id}")
async def add_task_dependency(
    task_id: str,
    depends_on_id: str,
    db: Session = Depends(get_db)
):
    """Add a dependency between tasks."""
    service = TaskService(db)
    
    try:
        dependency = service.add_dependency(task_id, depends_on_id)
        return {"message": "Dependency added successfully", "id": dependency.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/tasks/{task_id}/dependencies/{depends_on_id}")
async def remove_task_dependency(
    task_id: str,
    depends_on_id: str,
    db: Session = Depends(get_db)
):
    """Remove a dependency between tasks."""
    service = TaskService(db)
    success = service.remove_dependency(task_id, depends_on_id)
    if success:
        return {"message": "Dependency removed"}
    raise HTTPException(status_code=404, detail="Dependency not found")


@router.post("/tasks/extract")
async def extract_tasks_from_text(
    request: TaskExtractRequest,
    db: Session = Depends(get_db)
):
    """Extract tasks from meeting notes or text using AI."""
    service = TaskService(db)
    try:
        tasks = service.extract_tasks_from_text(
            text=request.text,
            project_id=request.project_id,
            default_owner=request.default_owner
        )
        return {
            "message": f"Extracted {len(tasks)} tasks",
            "tasks": [{"id": t.id, "name": t.name} for t in tasks]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks/overdue", response_model=List[TaskResponse])
async def get_overdue_tasks(db: Session = Depends(get_db)):
    """Get all overdue tasks."""
    service = TaskService(db)
    tasks = service.get_overdue_tasks()
    return tasks


@router.get("/tasks/blocked", response_model=List[TaskResponse])
async def get_blocked_tasks(db: Session = Depends(get_db)):
    """Get all blocked tasks."""
    service = TaskService(db)
    tasks = service.get_blocked_tasks()
    return tasks


@router.get("/projects/{project_id}/tasks/prioritized", response_model=List[TaskResponse])
async def get_prioritized_tasks(project_id: str, db: Session = Depends(get_db)):
    """Get prioritized task list for a project."""
    service = TaskService(db)
    tasks = service.prioritize_tasks(project_id)
    return tasks


# ==================== ACTIVITY FEED ====================

@router.get("/activities", response_model=List[AgentActivityResponse])
async def get_activities(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent agent activities."""
    from backend.app.models import AgentActivity
    
    activities = db.query(AgentActivity).order_by(
        AgentActivity.timestamp.desc()
    ).limit(limit).all()
    
    return activities


# ==================== DASHBOARD STATS ====================

@router.get("/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    from backend.app.models import Task, Project, Escalation, EscalationStatus
    
    total_projects = db.query(Project).count()
    total_tasks = db.query(Task).count()
    
    pending_tasks = db.query(Task).filter(
        Task.status.in_([TaskStatus.NOT_STARTED, TaskStatus.IN_PROGRESS])
    ).count()
    
    blocked_tasks = db.query(Task).filter(
        Task.status == TaskStatus.BLOCKED
    ).count()
    
    completed_tasks = db.query(Task).filter(
        Task.status == TaskStatus.COMPLETED
    ).count()
    
    service = TaskService(db)
    overdue_tasks = len(service.get_overdue_tasks())
    
    # Escalation stats
    open_escalations = db.query(Escalation).filter(
        Escalation.status.in_([EscalationStatus.OPEN, EscalationStatus.ACKNOWLEDGED])
    ).count()
    
    # Project health summary
    projects_at_risk = db.query(Project).filter(
        Project.health.in_([ProjectHealth.AT_RISK, ProjectHealth.DELAYED])
    ).count()
    
    return {
        "total_projects": total_projects,
        "projects_at_risk": projects_at_risk,
        "total_tasks": total_tasks,
        "pending_tasks": pending_tasks,
        "blocked_tasks": blocked_tasks,
        "completed_tasks": completed_tasks,
        "overdue_tasks": overdue_tasks,
        "open_escalations": open_escalations,
        "completion_rate": round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0
    }
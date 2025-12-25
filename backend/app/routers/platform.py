"""
Platform & Enterprise API Routes.

Provides REST API endpoints for:
- User management and RBAC
- Audit trail access
- Approval workflows
- System health and state
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from backend.app.core.database import get_db
from backend.app.agents.platform_enterprise import PlatformEnterpriseAgent


router = APIRouter(prefix="/api/v1/platform", tags=["Platform & Enterprise"])


# ==================== PYDANTIC SCHEMAS ====================

class UserCreate(BaseModel):
    email: str
    name: str
    role: str = "viewer"


class RoleUpdate(BaseModel):
    new_role: str
    reason: str


class ApprovalAction(BaseModel):
    approved: bool
    reason: str


class StateUpdate(BaseModel):
    value: Any
    reason: Optional[str] = None


class RollbackRequest(BaseModel):
    reason: str


class ActionLog(BaseModel):
    action: str
    resource_type: str
    resource_id: str
    reason: Optional[str] = None
    changes: Optional[Dict] = None


# ==================== USER MANAGEMENT ENDPOINTS ====================

@router.post("/users")
def create_user(
    user: UserCreate,
    x_user_id: str = Header("system"),
    db: Session = Depends(get_db)
):
    """Create a new user."""
    agent = PlatformEnterpriseAgent(db)
    
    # Check if requester has permission
    perm = agent.check_permission(x_user_id, "create:user")
    if not perm.get("allowed") and x_user_id != "system":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    result = agent.create_user(
        email=user.email,
        name=user.name,
        role=user.role,
        created_by=x_user_id
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/users")
def list_users(
    role: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all users."""
    agent = PlatformEnterpriseAgent(db)
    return agent.get_users(role)


@router.get("/users/{user_id}/permissions")
def get_user_permissions(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get user's permissions."""
    agent = PlatformEnterpriseAgent(db)
    result = agent.get_user_permissions(user_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    update: RoleUpdate,
    x_user_id: str = Header(...),
    db: Session = Depends(get_db)
):
    """Update user role. May require approval for escalation."""
    agent = PlatformEnterpriseAgent(db)
    result = agent.update_user_role(
        user_id=user_id,
        new_role=update.new_role,
        changed_by=x_user_id,
        reason=update.reason
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/check-permission")
def check_permission(
    user_id: str,
    permission: str,
    resource_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Check if user has a specific permission."""
    agent = PlatformEnterpriseAgent(db)
    return agent.check_permission(user_id, permission, resource_id)


# ==================== APPROVAL ENDPOINTS ====================

@router.get("/approvals")
def list_pending_approvals(
    db: Session = Depends(get_db)
):
    """List all pending approvals."""
    agent = PlatformEnterpriseAgent(db)
    return agent.get_pending_approvals()


@router.post("/approvals/{approval_id}/process")
def process_approval(
    approval_id: str,
    action: ApprovalAction,
    x_user_id: str = Header(...),
    db: Session = Depends(get_db)
):
    """Approve or reject an approval request."""
    agent = PlatformEnterpriseAgent(db)
    result = agent.process_approval(
        approval_id=approval_id,
        approver_id=x_user_id,
        approved=action.approved,
        reason=action.reason
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ==================== AUDIT ENDPOINTS ====================

@router.get("/audit")
def get_audit_logs(
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get audit trail with optional filters."""
    agent = PlatformEnterpriseAgent(db)
    return agent.get_audit_trail(
        resource_type=resource_type,
        resource_id=resource_id,
        actor_id=actor_id,
        limit=limit
    )


@router.post("/audit/log")
def log_action(
    log: ActionLog,
    x_user_id: str = Header(...),
    db: Session = Depends(get_db)
):
    """Log a custom action."""
    agent = PlatformEnterpriseAgent(db)
    agent.log_action(
        actor_id=x_user_id,
        action=log.action,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        reason=log.reason,
        changes=log.changes
    )
    return {"status": "logged"}


# ==================== STATE MANAGEMENT ENDPOINTS ====================

@router.get("/state/{key}")
def get_state(
    key: str,
    db: Session = Depends(get_db)
):
    """Get current state value."""
    agent = PlatformEnterpriseAgent(db)
    result = agent.get_state(key)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/state/{key}")
def save_state(
    key: str,
    update: StateUpdate,
    x_user_id: str = Header(...),
    db: Session = Depends(get_db)
):
    """Save state with versioning."""
    agent = PlatformEnterpriseAgent(db)
    return agent.save_state(
        key=key,
        value=update.value,
        changed_by=x_user_id,
        reason=update.reason
    )


@router.post("/state/{key}/rollback")
def rollback_state(
    key: str,
    request: RollbackRequest,
    x_user_id: str = Header(...),
    db: Session = Depends(get_db)
):
    """Rollback state to previous version."""
    agent = PlatformEnterpriseAgent(db)
    result = agent.rollback_state(
        key=key,
        rolled_back_by=x_user_id,
        reason=request.reason
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ==================== SYSTEM HEALTH ENDPOINTS ====================

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Get system health status."""
    agent = PlatformEnterpriseAgent(db)
    return agent.health_check()

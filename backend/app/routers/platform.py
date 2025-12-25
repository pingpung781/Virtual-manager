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


# ==================== NEW PHASE 6 ENDPOINTS ====================

class TenantCreate(BaseModel):
    name: str
    owner_email: str
    subscription_tier: str = "free"
    config: Optional[Dict] = None


class MCPToolRegister(BaseModel):
    name: str
    server_name: str
    description: Optional[str] = None
    input_schema: Optional[Dict] = None
    requires_approval: bool = False
    sensitivity_level: str = "low"
    allowed_roles: Optional[List[str]] = None


@router.get("/audit-logs")
def export_audit_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    actor_id: Optional[str] = None,
    action_type: Optional[str] = None,
    x_tenant_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Export audit logs for compliance reporting."""
    from datetime import datetime
    from backend.app.services.platform_service import export_audit_logs as export_logs
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    return export_logs(
        db=db,
        tenant_id=x_tenant_id,
        start_date=start,
        end_date=end,
        actor_id=actor_id,
        action_type=action_type
    )


@router.post("/tools/register")
def register_mcp_tool(
    tool: MCPToolRegister,
    x_user_id: str = Header("system"),
    db: Session = Depends(get_db)
):
    """Register a new MCP tool for external integrations."""
    from backend.app.services.platform_service import register_mcp_tool as register_tool
    
    # Check admin permission
    agent = PlatformEnterpriseAgent(db)
    perm = agent.check_permission(x_user_id, "admin:tools")
    if not perm.get("allowed") and x_user_id != "system":
        raise HTTPException(status_code=403, detail="Admin permission required")
    
    return register_tool(
        db=db,
        name=tool.name,
        server_name=tool.server_name,
        description=tool.description,
        input_schema=tool.input_schema,
        requires_approval=tool.requires_approval,
        sensitivity_level=tool.sensitivity_level,
        allowed_roles=tool.allowed_roles
    )


@router.get("/tools")
def list_mcp_tools(
    x_user_id: str = Header("anonymous"),
    db: Session = Depends(get_db)
):
    """List available MCP tools for the user."""
    from backend.app.services.platform_service import get_available_tools
    from backend.app.models import Employee
    
    # Get user role
    user = db.query(Employee).filter(Employee.id == x_user_id).first()
    role = user.role if user else "viewer"
    
    return get_available_tools(db, role)


@router.post("/tenants")
def create_tenant(
    tenant: TenantCreate,
    x_user_id: str = Header("system"),
    db: Session = Depends(get_db)
):
    """Create a new tenant environment."""
    from backend.app.services.platform_service import configure_tenant
    
    result = configure_tenant(
        db=db,
        name=tenant.name,
        owner_email=tenant.owner_email,
        subscription_tier=tenant.subscription_tier,
        config=tenant.config
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/tenants/{tenant_id}")
def get_tenant(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """Get tenant details."""
    from backend.app.models import Tenant
    import json
    
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "tier": tenant.subscription_tier,
        "config": json.loads(tenant.config) if tenant.config else {},
        "limits": {
            "max_users": tenant.max_users,
            "max_projects": tenant.max_projects,
            "max_storage_gb": tenant.max_storage_gb
        },
        "is_active": tenant.is_active
    }


@router.post("/seed-permissions")
def seed_permissions(
    x_user_id: str = Header("system"),
    db: Session = Depends(get_db)
):
    """Seed default RBAC permissions into database."""
    from backend.app.services.platform_service import seed_default_permissions
    
    if x_user_id != "system":
        agent = PlatformEnterpriseAgent(db)
        perm = agent.check_permission(x_user_id, "admin:system")
        if not perm.get("allowed"):
            raise HTTPException(status_code=403, detail="Admin permission required")
    
    return seed_default_permissions(db)


# ==================== MCP TOOL ENDPOINTS ====================

class ToolExecute(BaseModel):
    tool_name: str
    server_name: str
    parameters: Dict


@router.post("/tools/discover/{server_name}")
def discover_tools(
    server_name: str,
    x_user_id: str = Header("system"),
    db: Session = Depends(get_db)
):
    """Discover and register tools from an MCP server."""
    agent = PlatformEnterpriseAgent(db)
    
    if x_user_id != "system":
        perm = agent.check_permission(x_user_id, "admin:tools")
        if not perm.get("allowed"):
            raise HTTPException(status_code=403, detail="Admin permission required")
    
    return agent.discover_and_register_tools(server_name)


@router.post("/tools/execute")
def execute_tool(
    request: ToolExecute,
    x_user_id: str = Header(...),
    db: Session = Depends(get_db)
):
    """Execute an MCP tool (may require approval for sensitive actions)."""
    agent = PlatformEnterpriseAgent(db)
    
    result = agent.execute_mcp_tool(
        tool_name=request.tool_name,
        server_name=request.server_name,
        parameters=request.parameters,
        user_id=x_user_id
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/tools/health")
def get_tools_health(db: Session = Depends(get_db)):
    """Get health status of all registered MCP tools."""
    agent = PlatformEnterpriseAgent(db)
    return agent.get_tool_health()



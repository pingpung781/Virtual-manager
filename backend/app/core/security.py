"""
Security Module - RBAC Middleware and Audit Logging.

Provides:
- Permission verification for all API calls
- Audit logging for compliance and explainability
- Tenant isolation for multi-tenancy
"""

import json
import uuid
from datetime import datetime
from functools import wraps
from typing import Dict, Any, List, Optional, Callable
from fastapi import HTTPException, Request, Depends
from sqlalchemy.orm import Session
from backend.app.models import RolePermission, AuditLog, Employee, Tenant


# Default role permissions (can be overridden in DB)
DEFAULT_PERMISSIONS = {
    "admin": {
        "project": ["create", "read", "update", "delete", "approve"],
        "task": ["create", "read", "update", "delete", "approve"],
        "user": ["create", "read", "update", "delete", "approve"],
        "budget": ["create", "read", "update", "delete", "approve"],
        "goal": ["create", "read", "update", "delete", "approve"],
        "audit": ["read"],
    },
    "manager": {
        "project": ["create", "read", "update", "approve"],
        "task": ["create", "read", "update", "delete", "approve"],
        "user": ["read", "update"],
        "budget": ["read", "update", "approve"],
        "goal": ["create", "read", "update"],
        "audit": ["read"],
    },
    "contributor": {
        "project": ["read"],
        "task": ["create", "read", "update"],
        "user": ["read"],
        "budget": ["read"],
        "goal": ["read"],
    },
    "viewer": {
        "project": ["read"],
        "task": ["read"],
        "user": ["read"],
        "budget": [],
        "goal": ["read"],
    }
}


def verify_permission(
    db: Session,
    user_id: str,
    resource: str,
    action: str,
    resource_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Verify if a user has permission to perform an action on a resource.
    
    This is the core RBAC check that should be called before any action.
    AI Agents inherit the permissions of the invoking user.
    """
    # Get user and their role
    employee = db.query(Employee).filter(Employee.id == user_id).first()
    if not employee:
        return {
            "allowed": False,
            "reason": "User not found",
            "user_id": user_id
        }
    
    role = employee.role.lower() if employee.role else "viewer"
    
    # First check DB for custom permissions
    db_permission = db.query(RolePermission).filter(
        RolePermission.role_name == role,
        RolePermission.resource == resource.lower(),
        RolePermission.action == action.lower(),
        RolePermission.is_active == True
    ).first()
    
    if db_permission:
        # Check conditions if any
        if db_permission.condition:
            try:
                conditions = json.loads(db_permission.condition)
                # TODO: Evaluate conditions (own_team_only, etc.)
            except:
                pass
        return {
            "allowed": True,
            "source": "database",
            "role": role,
            "permission_id": db_permission.id
        }
    
    # Fall back to default permissions
    role_perms = DEFAULT_PERMISSIONS.get(role, {})
    resource_perms = role_perms.get(resource.lower(), [])
    
    if action.lower() in resource_perms:
        return {
            "allowed": True,
            "source": "default",
            "role": role
        }
    
    return {
        "allowed": False,
        "reason": f"Role '{role}' lacks '{action}' permission on '{resource}'",
        "role": role,
        "user_id": user_id
    }


def log_action(
    db: Session,
    actor_id: str,
    action_type: str,
    target_entity: str,
    target_id: str,
    changes: Optional[Dict] = None,
    reason: Optional[str] = None,
    prompt: Optional[str] = None,
    response: Optional[str] = None,
    is_sensitive: bool = False,
    tenant_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    actor_type: str = "user"
) -> str:
    """
    Create immutable audit log entry.
    
    Captures the "Prompt" and "Response" for AI actions to ensure explainability.
    Should be called for all critical actions in the system.
    """
    log = AuditLog(
        id=str(uuid.uuid4()),
        timestamp=datetime.utcnow(),
        actor_id=actor_id,
        actor_type=actor_type,
        action_type=action_type,
        target_entity=target_entity,
        target_id=target_id,
        changes=json.dumps(changes) if changes else None,
        reason=reason,
        prompt=prompt,
        response=response,
        is_sensitive=is_sensitive,
        tenant_id=tenant_id,
        ip_address=ip_address,
        is_success=True
    )
    
    db.add(log)
    db.commit()
    
    return log.id


def require_permission(resource: str, action: str):
    """
    FastAPI dependency decorator for RBAC enforcement.
    
    Usage:
        @router.post("/projects")
        def create_project(
            _: bool = Depends(require_permission("project", "create")),
            db: Session = Depends(get_db)
        ):
    """
    def dependency(
        request: Request,
        db: Session = Depends(lambda: None)  # Placeholder
    ):
        from backend.app.core.database import get_db
        
        # Get user ID from header
        user_id = request.headers.get("x-user-id", "anonymous")
        
        if user_id == "anonymous":
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        
        # Get actual db session
        from backend.app.core.database import SessionLocal
        db = SessionLocal()
        
        try:
            result = verify_permission(db, user_id, resource, action)
            
            if not result.get("allowed"):
                # Log unauthorized attempt
                log_action(
                    db=db,
                    actor_id=user_id,
                    action_type=f"{action}_{resource}",
                    target_entity=resource,
                    target_id="denied",
                    reason=result.get("reason"),
                    is_sensitive=True
                )
                db.close()
                raise HTTPException(
                    status_code=403,
                    detail=result.get("reason", "Permission denied")
                )
            
            return True
        finally:
            db.close()
    
    return dependency


def get_tenant_id(request: Request) -> Optional[str]:
    """Extract tenant ID from request for multi-tenancy."""
    # Can be from header, subdomain, or path
    return request.headers.get("x-tenant-id")


def filter_by_tenant(query, tenant_id: Optional[str]):
    """Add tenant filter to SQLAlchemy query for data isolation."""
    if tenant_id:
        return query.filter_by(tenant_id=tenant_id)
    return query


# Sensitive actions that require approval
SENSITIVE_ACTIONS = {
    "delete:project": "Deleting a project is permanent",
    "delete:user": "Removing user access",
    "update:budget": "Budget changes require manager approval",
    "create:offer": "Sending offer letters requires HR approval",
    "execute:deployment": "Production deployments require lead approval"
}


def is_sensitive_action(action: str, resource: str) -> bool:
    """Check if action requires approval workflow."""
    key = f"{action}:{resource}"
    return key in SENSITIVE_ACTIONS

"""
Platform Service - Tenant configuration, audit export, and MCP tool registration.

Provides:
- Tenant environment setup
- Compliance audit log export
- Dynamic MCP tool registration
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.models import (
    Tenant, AuditLog, MCPTool, RolePermission
)


def configure_tenant(
    db: Session,
    name: str,
    owner_email: str,
    subscription_tier: str = "free",
    config: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Set up new organization environment.
    Creates tenant with default configuration.
    """
    # Generate slug from name
    slug = name.lower().replace(" ", "-").replace("_", "-")
    
    # Check if exists
    existing = db.query(Tenant).filter(Tenant.slug == slug).first()
    if existing:
        return {"error": "Tenant with this name already exists"}
    
    # Default config based on tier
    default_config = {
        "features": {
            "analytics": True,
            "automation": subscription_tier in ["pro", "enterprise"],
            "mcp_integrations": subscription_tier == "enterprise",
            "custom_roles": subscription_tier in ["pro", "enterprise"],
            "audit_export": True,
            "api_access": True
        },
        "branding": {
            "logo_url": None,
            "primary_color": "#3B82F6"
        }
    }
    
    if config:
        default_config.update(config)
    
    # Tier limits
    limits = {
        "free": {"users": 5, "projects": 3, "storage": 1},
        "pro": {"users": 25, "projects": 20, "storage": 10},
        "enterprise": {"users": -1, "projects": -1, "storage": 100}  # -1 = unlimited
    }
    tier_limits = limits.get(subscription_tier, limits["free"])
    
    tenant = Tenant(
        id=str(uuid.uuid4()),
        name=name,
        slug=slug,
        owner_email=owner_email,
        subscription_tier=subscription_tier,
        config=json.dumps(default_config),
        max_users=tier_limits["users"],
        max_projects=tier_limits["projects"],
        max_storage_gb=tier_limits["storage"],
        trial_ends_at=datetime.utcnow() + timedelta(days=14) if subscription_tier == "free" else None
    )
    
    db.add(tenant)
    db.commit()
    
    return {
        "tenant_id": tenant.id,
        "name": name,
        "slug": slug,
        "tier": subscription_tier,
        "trial_ends_at": tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None,
        "next_step": "Invite team members and configure integrations"
    }


def export_audit_logs(
    db: Session,
    tenant_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    actor_id: Optional[str] = None,
    action_type: Optional[str] = None,
    format: str = "json"
) -> Dict[str, Any]:
    """
    Export audit logs for compliance reporting.
    Supports filtering by time range, actor, and action type.
    """
    query = db.query(AuditLog)
    
    if tenant_id:
        query = query.filter(AuditLog.tenant_id == tenant_id)
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)
    if actor_id:
        query = query.filter(AuditLog.actor_id == actor_id)
    if action_type:
        query = query.filter(AuditLog.action_type == action_type)
    
    logs = query.order_by(AuditLog.timestamp.desc()).limit(10000).all()
    
    records = []
    for log in logs:
        record = {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "actor_id": log.actor_id,
            "actor_type": log.actor_type,
            "action_type": log.action_type,
            "target_entity": log.target_entity,
            "target_id": log.target_id,
            "is_sensitive": log.is_sensitive,
            "is_success": log.is_success
        }
        
        # Include reason but not full prompt/response for privacy
        if log.reason:
            record["reason"] = log.reason
        if log.error_message:
            record["error"] = log.error_message
            
        records.append(record)
    
    return {
        "export_date": datetime.utcnow().isoformat(),
        "total_records": len(records),
        "filters_applied": {
            "tenant_id": tenant_id,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "actor_id": actor_id,
            "action_type": action_type
        },
        "records": records
    }


def register_mcp_tool(
    db: Session,
    name: str,
    server_name: str,
    description: Optional[str] = None,
    input_schema: Optional[Dict] = None,
    requires_approval: bool = False,
    sensitivity_level: str = "low",
    allowed_roles: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Register a new MCP tool for external integrations.
    
    Safety: Wraps unsafe tools with approval requirements.
    """
    # Check if tool already exists
    existing = db.query(MCPTool).filter(
        MCPTool.name == name,
        MCPTool.server_name == server_name
    ).first()
    
    if existing:
        # Update existing tool
        existing.description = description or existing.description
        existing.input_schema = json.dumps(input_schema) if input_schema else existing.input_schema
        existing.requires_approval = requires_approval
        existing.sensitivity_level = sensitivity_level
        existing.allowed_roles = json.dumps(allowed_roles) if allowed_roles else existing.allowed_roles
        existing.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "tool_id": existing.id,
            "name": name,
            "status": "updated",
            "requires_approval": requires_approval
        }
    
    # Auto-detect if tool needs approval based on name
    dangerous_keywords = ["delete", "remove", "destroy", "drop", "send", "publish", "deploy"]
    if any(kw in name.lower() for kw in dangerous_keywords):
        requires_approval = True
        sensitivity_level = "high" if sensitivity_level == "low" else sensitivity_level
    
    tool = MCPTool(
        id=str(uuid.uuid4()),
        name=name,
        description=description,
        server_name=server_name,
        input_schema=json.dumps(input_schema) if input_schema else None,
        requires_approval=requires_approval,
        sensitivity_level=sensitivity_level,
        allowed_roles=json.dumps(allowed_roles) if allowed_roles else None
    )
    
    db.add(tool)
    db.commit()
    
    return {
        "tool_id": tool.id,
        "name": name,
        "server": server_name,
        "status": "registered",
        "requires_approval": requires_approval,
        "sensitivity_level": sensitivity_level
    }


def get_available_tools(
    db: Session,
    user_role: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get all available MCP tools, filtered by user role."""
    query = db.query(MCPTool).filter(
        MCPTool.is_active == True,
        MCPTool.is_available == True
    )
    
    tools = query.all()
    result = []
    
    for tool in tools:
        # Check role access
        if tool.allowed_roles and user_role:
            allowed = json.loads(tool.allowed_roles)
            if user_role.lower() not in [r.lower() for r in allowed]:
                continue
        
        result.append({
            "id": tool.id,
            "name": tool.name,
            "description": tool.description,
            "server": tool.server_name,
            "requires_approval": tool.requires_approval,
            "sensitivity_level": tool.sensitivity_level
        })
    
    return result


def seed_default_permissions(db: Session) -> Dict[str, Any]:
    """Seed default RBAC permissions into database."""
    from backend.app.core.security import DEFAULT_PERMISSIONS
    
    created = 0
    for role, resources in DEFAULT_PERMISSIONS.items():
        for resource, actions in resources.items():
            for action in actions:
                existing = db.query(RolePermission).filter(
                    RolePermission.role_name == role,
                    RolePermission.resource == resource,
                    RolePermission.action == action
                ).first()
                
                if not existing:
                    perm = RolePermission(
                        id=str(uuid.uuid4()),
                        role_name=role,
                        resource=resource,
                        action=action,
                        created_by="system"
                    )
                    db.add(perm)
                    created += 1
    
    db.commit()
    
    return {
        "status": "completed",
        "permissions_created": created
    }

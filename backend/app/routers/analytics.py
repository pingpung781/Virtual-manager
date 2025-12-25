"""
Analytics & Automation API Routes.

Provides REST API endpoints for:
- Project performance analytics
- Team workload analytics
- Delivery trend analysis
- Risk forecasting
- Executive dashboards
- Proactive suggestions
- Early warnings
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from backend.app.core.database import get_db
from backend.app.agents.analytics_automation import AnalyticsAutomationAgent


router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics & Automation"])


# ==================== PYDANTIC SCHEMAS ====================

class ReplanningRequest(BaseModel):
    task_id: str
    reason: str


# ==================== ANALYTICS ENDPOINTS ====================

@router.get("/projects")
def get_project_analytics(
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get project performance analytics with health scores and trends."""
    agent = AnalyticsAutomationAgent(db)
    return agent.analyze_project_performance(project_id)


@router.get("/workload")
def get_workload_analytics(db: Session = Depends(get_db)):
    """Get team workload distribution and balance signals."""
    agent = AnalyticsAutomationAgent(db)
    return agent.analyze_team_workload()


@router.get("/delivery-trends")
def get_delivery_trends(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Analyze delivery trends over a period."""
    agent = AnalyticsAutomationAgent(db)
    return agent.analyze_delivery_trends(days)


@router.get("/risks")
def get_risk_forecast(
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Forecast risks with probability and impact assessment."""
    agent = AnalyticsAutomationAgent(db)
    return agent.forecast_risks(project_id)


@router.get("/executive-dashboard")
def get_executive_dashboard(db: Session = Depends(get_db)):
    """Generate executive dashboard for senior leadership."""
    agent = AnalyticsAutomationAgent(db)
    return agent.generate_executive_dashboard()


# ==================== PROACTIVE INTELLIGENCE ENDPOINTS ====================

@router.get("/suggestions")
def get_proactive_suggestions(db: Session = Depends(get_db)):
    """Get proactive suggestions based on current state analysis."""
    agent = AnalyticsAutomationAgent(db)
    return agent.get_proactive_suggestions()


@router.get("/warnings")
def get_early_warnings(db: Session = Depends(get_db)):
    """Get early warning alerts prioritized by severity."""
    agent = AnalyticsAutomationAgent(db)
    return agent.get_early_warnings()


@router.post("/replan")
def propose_replanning(
    request: ReplanningRequest,
    db: Session = Depends(get_db)
):
    """
    Propose replanning alternatives for a delayed task.
    
    Note: This only proposes options. Approval required for execution.
    """
    agent = AnalyticsAutomationAgent(db)
    result = agent.propose_replanning(request.task_id, request.reason)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/patterns")
def get_pattern_insights(db: Session = Depends(get_db)):
    """Get pattern learning insights from historical data."""
    agent = AnalyticsAutomationAgent(db)
    return agent.get_pattern_insights()


# ==================== NEW PHASE 5 ENDPOINTS ====================

class AutomationRuleCreate(BaseModel):
    name: str
    trigger_condition: dict  # {"metric": "overdue_tasks", "operator": ">", "value": 5}
    action_type: str  # alert, replan, auto_assign, escalate
    action_config: Optional[dict] = None
    project_id: Optional[str] = None


@router.get("/dashboard/data")
def get_dashboard_data(db: Session = Depends(get_db)):
    """Get structured dashboard data for frontend charts."""
    from backend.app.services.analytics_service import get_dashboard_data
    return get_dashboard_data(db)


@router.get("/projects/{project_id}/forecast")
def get_project_forecast(project_id: str, db: Session = Depends(get_db)):
    """Get AI prediction of project completion."""
    from backend.app.services.analytics_service import run_forecast
    return run_forecast(db, project_id)


@router.get("/projects/{project_id}/velocity")
def get_project_velocity(project_id: str, days: int = 30, db: Session = Depends(get_db)):
    """Calculate completion velocity for a project."""
    from backend.app.core.analytics import calculate_velocity
    return calculate_velocity(db, project_id, days)


@router.post("/rules")
def create_automation_rule(rule: AutomationRuleCreate, db: Session = Depends(get_db)):
    """Create new automation trigger rule."""
    import uuid
    import json
    from backend.app.models import AutomationRule, AutomationActionType
    
    new_rule = AutomationRule(
        id=str(uuid.uuid4()),
        name=rule.name,
        trigger_condition=json.dumps(rule.trigger_condition),
        action_type=AutomationActionType(rule.action_type),
        action_config=json.dumps(rule.action_config) if rule.action_config else None,
        project_id=rule.project_id
    )
    db.add(new_rule)
    db.commit()
    
    return {"rule_id": new_rule.id, "name": new_rule.name, "status": "active"}


@router.get("/rules")
def list_automation_rules(db: Session = Depends(get_db)):
    """List all automation rules."""
    from backend.app.models import AutomationRule
    rules = db.query(AutomationRule).all()
    return [{
        "id": r.id,
        "name": r.name,
        "action_type": r.action_type.value,
        "is_active": r.is_active,
        "trigger_count": r.trigger_count
    } for r in rules]


@router.post("/snapshots/{project_id}")
def take_snapshot(project_id: str, db: Session = Depends(get_db)):
    """Manually trigger project snapshot."""
    from backend.app.core.analytics import take_project_snapshot
    return take_project_snapshot(db, project_id)


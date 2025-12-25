"""
Analytics Service - Dashboard data and rule evaluation.

Handles:
- Dashboard data aggregation
- Automation rule evaluation
- Forecast generation
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.models import (
    Project, Task, TaskStatus, AutomationRule, AutomationActionType,
    ProjectSnapshot, Goal, GoalStatus, Forecast
)
from backend.app.core.analytics import compute_risk_score, calculate_velocity


def get_dashboard_data(db: Session, scope: str = "all") -> Dict[str, Any]:
    """
    Get structured dashboard data for frontend charts.
    
    Includes: Burndown, Velocity, Risk Heatmap
    """
    projects = db.query(Project).all()
    
    # Risk heatmap data
    risk_data = []
    for project in projects:
        risk = compute_risk_score(db, project.id)
        risk_data.append({
            "project_id": project.id,
            "project_name": project.name,
            "risk_score": risk.get("risk_score", 0),
            "risk_level": risk.get("risk_level", "low")
        })
    
    # Goal progress
    goals = db.query(Goal).filter(Goal.status != GoalStatus.CANCELLED).all()
    goal_data = [{
        "id": g.id,
        "objective": g.objective[:50] if g.objective else "",
        "progress": g.progress_percentage,
        "status": g.status.value
    } for g in goals]
    
    # Task distribution
    tasks = db.query(Task).all()
    status_dist = {}
    for task in tasks:
        status = task.status.value
        status_dist[status] = status_dist.get(status, 0) + 1
    
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "scope": scope,
        "risk_heatmap": sorted(risk_data, key=lambda x: x["risk_score"], reverse=True),
        "goals_summary": goal_data,
        "task_distribution": status_dist,
        "project_count": len(projects),
        "high_risk_projects": sum(1 for r in risk_data if r["risk_level"] in ["high", "critical"])
    }


def evaluate_rules(db: Session, event: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Evaluate automation rules against an event.
    
    Returns list of triggered actions.
    """
    rules = db.query(AutomationRule).filter(
        AutomationRule.is_active == True
    ).all()
    
    triggered = []
    
    for rule in rules:
        try:
            condition = json.loads(rule.trigger_condition)
        except:
            continue
        
        # Simple rule evaluation
        metric = condition.get("metric")
        operator = condition.get("operator")
        value = condition.get("value")
        
        event_value = event.get(metric)
        
        if event_value is None:
            continue
        
        matched = False
        if operator == ">" and event_value > value:
            matched = True
        elif operator == ">=" and event_value >= value:
            matched = True
        elif operator == "<" and event_value < value:
            matched = True
        elif operator == "<=" and event_value <= value:
            matched = True
        elif operator == "==" and event_value == value:
            matched = True
        elif operator == "!=" and event_value != value:
            matched = True
        
        if matched:
            rule.last_triggered = datetime.utcnow()
            rule.trigger_count += 1
            
            action_config = {}
            if rule.action_config:
                try:
                    action_config = json.loads(rule.action_config)
                except:
                    pass
            
            triggered.append({
                "rule_id": rule.id,
                "rule_name": rule.name,
                "action_type": rule.action_type.value,
                "action_config": action_config
            })
    
    db.commit()
    
    return triggered


def run_forecast(db: Session, project_id: str) -> Dict[str, Any]:
    """Run forecasting for a project and store prediction."""
    velocity = calculate_velocity(db, project_id)
    risk = compute_risk_score(db, project_id)
    
    # Build prediction text
    prediction_text = f"Based on current velocity ({velocity['velocity_per_week']} tasks/week), "
    
    if velocity.get("projected_completion"):
        prediction_text += f"project expected to complete by {velocity['projected_completion'][:10]}."
        confidence = 0.7 if velocity["trend"] == "stable" else 0.5
    else:
        prediction_text += "completion date cannot be determined due to low velocity."
        confidence = 0.3
    
    # Adjust confidence based on risk
    if risk.get("risk_level") == "critical":
        confidence *= 0.6
        prediction_text += " WARNING: High risk may impact timeline."
    elif risk.get("risk_level") == "high":
        confidence *= 0.8
    
    # Create forecast record
    target_date = None
    if velocity.get("projected_completion"):
        try:
            target_date = datetime.fromisoformat(velocity["projected_completion"])
        except:
            pass
    
    forecast = Forecast(
        id=str(uuid.uuid4()),
        entity_type="PROJECT",
        entity_id=project_id,
        prediction_type="completion_date",
        prediction_text=prediction_text,
        predicted_value=velocity.get("projected_completion"),
        confidence_score=round(confidence, 2),
        target_date=target_date
    )
    
    db.add(forecast)
    db.commit()
    
    return {
        "forecast_id": forecast.id,
        "project_id": project_id,
        "velocity": velocity,
        "risk": risk,
        "prediction": prediction_text,
        "confidence": round(confidence, 2)
    }

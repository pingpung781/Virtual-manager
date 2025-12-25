"""
Risk Agent - Implements Decision Support & Risk Management.

Capabilities:
- Risk Assessment: Analyze project health and generate risks
- Mitigation Planning: Suggest mitigations for identified risks
- Daily Monitoring: Run risk checks on schedule

Maps to: "Decision Support & Risk Management" prompt requirements.
"""

import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from openai import OpenAI
import os

from backend.app.models import (
    Project, Task, TaskStatus, Risk, RiskLevel, DecisionLog, ProjectHealth
)
from backend.app.core.logging import logger


class RiskAgent:
    """
    Risk Agent for project risk management.
    
    Monitors project health and generates actionable risk assessments.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._llm_client = None
    
    @property
    def llm_client(self):
        if self._llm_client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self._llm_client = OpenAI(api_key=api_key)
        return self._llm_client
    
    def assess_project_risk(self, project_id: str) -> Dict[str, Any]:
        """
        Run a full risk assessment on a project.
        
        1. Fetches project health (from Phase 1)
        2. Analyzes blocked tasks and deadlines
        3. Generates risk entries with mitigations
        """
        # Get project
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "Project not found"}
        
        # Get project health data
        health_data = self._get_project_health(project_id)
        
        # Get blocked and overdue tasks
        tasks = self.db.query(Task).filter(Task.project_id == project_id).all()
        blocked_tasks = [t for t in tasks if t.status == TaskStatus.BLOCKED]
        overdue_tasks = [
            t for t in tasks 
            if t.deadline and t.deadline < datetime.utcnow() 
            and t.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]
        ]
        
        risks = []
        
        # Generate risks based on health status
        if health_data["status"] in ["AT_RISK", "DELAYED"]:
            if self.llm_client:
                risks = self._generate_risks_with_llm(
                    project, health_data, blocked_tasks, overdue_tasks
                )
            else:
                risks = self._generate_risks_simple(
                    project, health_data, blocked_tasks, overdue_tasks
                )
        
        # Save risks to database
        saved_risks = []
        for risk_data in risks:
            risk = Risk(
                id=str(uuid.uuid4()),
                project_id=project_id,
                description=risk_data["description"],
                likelihood=RiskLevel(risk_data.get("likelihood", "medium")),
                impact=RiskLevel(risk_data.get("impact", "medium")),
                mitigation_plan=risk_data.get("mitigation"),
                created_by="system"
            )
            self.db.add(risk)
            saved_risks.append({
                "id": risk.id,
                "description": risk.description,
                "likelihood": risk.likelihood.value,
                "impact": risk.impact.value,
                "mitigation": risk.mitigation_plan
            })
        
        # Log decision
        self._log_decision(
            context=f"Risk assessment for project '{project.name}' (Health: {health_data['status']})",
            decision=f"Identified {len(risks)} risks",
            rationale=f"Project has {len(blocked_tasks)} blocked tasks and {len(overdue_tasks)} overdue tasks",
            project_id=project_id
        )
        
        self.db.commit()
        
        return {
            "project_id": project_id,
            "project_name": project.name,
            "health_status": health_data["status"],
            "blocked_count": len(blocked_tasks),
            "overdue_count": len(overdue_tasks),
            "risks_identified": len(saved_risks),
            "risks": saved_risks
        }
    
    def _get_project_health(self, project_id: str) -> Dict[str, Any]:
        """Calculate project health (same logic as Phase 1 health endpoint)."""
        tasks = self.db.query(Task).filter(Task.project_id == project_id).all()
        
        if not tasks:
            return {"status": "NO_TASKS", "completion_percentage": 0}
        
        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        blocked = sum(1 for t in tasks if t.status == TaskStatus.BLOCKED)
        cancelled = sum(1 for t in tasks if t.status == TaskStatus.CANCELLED)
        
        now = datetime.utcnow()
        overdue = sum(
            1 for t in tasks 
            if t.deadline and t.deadline < now 
            and t.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]
        )
        
        active_tasks = total - cancelled
        overdue_percentage = (overdue / active_tasks * 100) if active_tasks > 0 else 0
        blocked_percentage = (blocked / active_tasks * 100) if active_tasks > 0 else 0
        completion_percentage = (completed / active_tasks * 100) if active_tasks > 0 else 0
        
        if overdue_percentage > 20:
            status = "DELAYED"
        elif overdue > 0 or blocked_percentage > 50:
            status = "AT_RISK"
        else:
            status = "ON_TRACK"
        
        return {
            "status": status,
            "completion_percentage": round(completion_percentage, 1),
            "blocked_count": blocked,
            "overdue_count": overdue
        }
    
    def _generate_risks_with_llm(
        self,
        project: Project,
        health_data: Dict,
        blocked_tasks: List[Task],
        overdue_tasks: List[Task]
    ) -> List[Dict]:
        """Use LLM to generate detailed risk assessments."""
        blocked_summary = ", ".join([f"'{t.name}'" for t in blocked_tasks[:5]])
        overdue_summary = ", ".join([f"'{t.name}' (due {t.deadline.date()})" for t in overdue_tasks[:5]])
        
        prompt = f"""
        Analyze this project and generate specific risks with mitigations.
        
        Project: {project.name}
        Health Status: {health_data['status']}
        Completion: {health_data['completion_percentage']}%
        Blocked Tasks: {blocked_summary or 'None'}
        Overdue Tasks: {overdue_summary or 'None'}
        Project End Date: {project.end_date.date() if project.end_date else 'Not set'}
        
        Return JSON with array of risks:
        - description: Specific risk description
        - likelihood: low, medium, or high
        - impact: low, medium, or high
        - mitigation: Actionable mitigation plan
        
        Generate 1-3 most important risks.
        """
        
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a project risk analyst. Generate specific, actionable risk assessments."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response.choices[0].message.content)
            return data.get("risks", [data]) if isinstance(data, dict) else data
            
        except Exception as e:
            logger.error(f"LLM risk generation failed: {e}")
            return self._generate_risks_simple(project, health_data, blocked_tasks, overdue_tasks)
    
    def _generate_risks_simple(
        self,
        project: Project,
        health_data: Dict,
        blocked_tasks: List[Task],
        overdue_tasks: List[Task]
    ) -> List[Dict]:
        """Generate basic risks without LLM."""
        risks = []
        
        if overdue_tasks:
            risks.append({
                "description": f"Project has {len(overdue_tasks)} overdue task(s), risking overall deadline",
                "likelihood": "high",
                "impact": "high" if len(overdue_tasks) > 2 else "medium",
                "mitigation": "Review overdue tasks and reassign or adjust deadlines"
            })
        
        if blocked_tasks:
            risks.append({
                "description": f"Project has {len(blocked_tasks)} blocked task(s) causing delivery delays",
                "likelihood": "high",
                "impact": "medium",
                "mitigation": "Identify blocking dependencies and prioritize their completion"
            })
        
        if health_data["status"] == "DELAYED":
            risks.append({
                "description": "Project is significantly delayed with more than 20% tasks overdue",
                "likelihood": "high",
                "impact": "high",
                "mitigation": "Escalate to stakeholders and consider scope reduction or deadline extension"
            })
        
        return risks
    
    def get_project_risks(self, project_id: str) -> List[Dict]:
        """Get all active risks for a project."""
        risks = self.db.query(Risk).filter(
            Risk.project_id == project_id,
            Risk.status == "open"
        ).all()
        
        return [{
            "id": r.id,
            "description": r.description,
            "likelihood": r.likelihood.value,
            "impact": r.impact.value,
            "mitigation": r.mitigation_plan,
            "created_at": r.created_at.isoformat()
        } for r in risks]
    
    def mitigate_risk(self, risk_id: str, resolution_notes: str) -> Dict[str, Any]:
        """Mark a risk as mitigated."""
        risk = self.db.query(Risk).filter(Risk.id == risk_id).first()
        if not risk:
            return {"error": "Risk not found"}
        
        risk.status = "mitigated"
        risk.mitigation_plan = f"{risk.mitigation_plan}\n\nResolution: {resolution_notes}"
        self.db.commit()
        
        return {"success": True, "risk_id": risk_id, "status": "mitigated"}
    
    def _log_decision(
        self,
        context: str,
        decision: str,
        rationale: str,
        project_id: str = None
    ):
        """Log agent decision."""
        log = DecisionLog(
            id=str(uuid.uuid4()),
            context=context,
            decision_made=decision,
            rationale=rationale,
            agent_name="RiskAgent",
            project_id=project_id
        )
        self.db.add(log)

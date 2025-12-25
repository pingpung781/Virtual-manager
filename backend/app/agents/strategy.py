"""
Strategy Agent - Implements Strategy & Business Planning.

Capabilities:
- Goal Parsing: Raw text -> Structured Goal & KeyResult objects
- Scope Creep Detection: Flags projects not aligned to active goals
- Goal Alignment: Links projects to strategic goals

Maps to: "Strategy & Business Planning" prompt requirements.
"""

import uuid
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from openai import OpenAI
import os

from backend.app.models import (
    Goal, GoalStatus, KeyResult, Project, GoalTaskLink,
    Risk, RiskLevel, DecisionLog
)
from backend.app.core.logging import logger


class StrategyAgent:
    """
    Strategy Agent for goal management and alignment.
    
    Implements the strategic planning layer of VAM.
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
    
    def create_goal_from_text(self, text: str, owner: str = None) -> Dict[str, Any]:
        """
        Parse raw text into structured Goal and KeyResult objects.
        
        Example: "Increase revenue by 10% in Q1" -> Goal + KeyResult
        """
        if not self.llm_client:
            # Fallback: create simple goal without parsing
            return self._create_simple_goal(text, owner)
        
        prompt = f"""
        Parse the following goal statement into structured data.
        Return JSON with:
        - title: Short goal title
        - description: Full goal description
        - time_horizon: quarterly, monthly, yearly, or specific (e.g., Q1 2025)
        - key_results: Array of objects with:
          - metric_name: What to measure
          - target_value: Target number
          - unit: Unit of measurement (%, USD, count, etc.)
        - is_measurable: true/false
        - missing_criteria: What's missing if not measurable
        
        Goal statement: {text}
        
        Return ONLY valid JSON.
        """
        
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a strategic planning assistant. Parse goals into structured data."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response.choices[0].message.content)
            return self._save_goal_from_data(data, owner, text)
            
        except Exception as e:
            logger.error(f"LLM goal parsing failed: {e}")
            return self._create_simple_goal(text, owner)
    
    def _create_simple_goal(self, text: str, owner: str = None) -> Dict[str, Any]:
        """Create a simple goal without LLM parsing."""
        goal = Goal(
            id=str(uuid.uuid4()),
            objective=text,
            owner=owner or "Unassigned",
            time_horizon="quarterly",
            is_measurable=False,
            missing_criteria="Goal needs structured metrics",
            status=GoalStatus.ACTIVE
        )
        
        self.db.add(goal)
        self.db.commit()
        self.db.refresh(goal)
        
        return {
            "goal_id": goal.id,
            "title": text[:50],
            "is_measurable": False,
            "key_results": []
        }
    
    def _save_goal_from_data(self, data: Dict, owner: str, original_text: str) -> Dict[str, Any]:
        """Save parsed goal data to database."""
        goal_id = str(uuid.uuid4())
        
        goal = Goal(
            id=goal_id,
            objective=data.get("description", original_text),
            kpis=json.dumps(data.get("key_results", [])),
            owner=owner or "Unassigned",
            time_horizon=data.get("time_horizon", "quarterly"),
            is_measurable=data.get("is_measurable", False),
            missing_criteria=data.get("missing_criteria"),
            status=GoalStatus.ACTIVE
        )
        
        self.db.add(goal)
        
        # Create KeyResult entries
        key_results = []
        for kr_data in data.get("key_results", []):
            kr = KeyResult(
                id=str(uuid.uuid4()),
                goal_id=goal_id,
                metric_name=kr_data.get("metric_name", "Unnamed metric"),
                target_value=float(kr_data.get("target_value", 0)),
                current_value=0,
                unit=kr_data.get("unit", "count")
            )
            self.db.add(kr)
            key_results.append({
                "id": kr.id,
                "metric": kr.metric_name,
                "target": kr.target_value,
                "unit": kr.unit
            })
        
        # Log decision
        self._log_decision(
            context=f"Goal creation from text: {original_text[:100]}",
            decision=f"Created goal: {data.get('title', goal.objective[:50])}",
            rationale="Parsed user input into structured strategic goal with measurable key results"
        )
        
        self.db.commit()
        self.db.refresh(goal)
        
        return {
            "goal_id": goal_id,
            "title": data.get("title", goal.objective[:50]),
            "is_measurable": goal.is_measurable,
            "key_results": key_results
        }
    
    def detect_scope_creep(self, project_id: str) -> Dict[str, Any]:
        """
        Detect if a project is not aligned to any active goal.
        
        Returns alignment score and scope creep warning if applicable.
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "Project not found"}
        
        # Get all active goals
        goals = self.db.query(Goal).filter(Goal.status == GoalStatus.ACTIVE).all()
        
        if not goals:
            return {
                "project_id": project_id,
                "alignment_score": 0,
                "aligned_goals": [],
                "is_scope_creep": True,
                "warning": "No active goals defined in the system"
            }
        
        # Check if project is linked to any goal
        linked_goals = []
        for goal in goals:
            links = self.db.query(GoalTaskLink).join(
                "task"
            ).filter(
                GoalTaskLink.goal_id == goal.id
            ).all()
            
            # Check if any linked tasks belong to this project
            for link in links:
                if link.task and link.task.project_id == project_id:
                    linked_goals.append({
                        "goal_id": goal.id,
                        "objective": goal.objective[:100]
                    })
                    break
        
        # Simple alignment check
        if linked_goals:
            alignment_score = min(100, len(linked_goals) * 50)
            is_scope_creep = False
        else:
            # Use LLM for semantic similarity if available
            if self.llm_client:
                alignment_score, matched_goal = self._check_semantic_alignment(project, goals)
                is_scope_creep = alignment_score < 30
                if matched_goal:
                    linked_goals.append(matched_goal)
            else:
                alignment_score = 0
                is_scope_creep = True
        
        result = {
            "project_id": project_id,
            "project_name": project.name,
            "alignment_score": alignment_score,
            "aligned_goals": linked_goals,
            "is_scope_creep": is_scope_creep
        }
        
        if is_scope_creep:
            result["warning"] = "Potential scope creep: Project not aligned to active goals"
            # Create risk entry
            self._create_scope_creep_risk(project_id, project.name)
        
        return result
    
    def _check_semantic_alignment(self, project: Project, goals: List[Goal]):
        """Use LLM to check semantic alignment between project and goals."""
        goal_texts = [f"Goal {g.id}: {g.objective}" for g in goals]
        
        prompt = f"""
        Analyze if this project aligns with any of these strategic goals.
        
        Project: {project.name}
        Description: {project.objective or 'No description'}
        
        Goals:
        {chr(10).join(goal_texts)}
        
        Return JSON with:
        - alignment_score: 0-100 (how well project aligns)
        - matched_goal_id: ID of best matching goal (or null)
        - reasoning: Brief explanation
        """
        
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Analyze strategic alignment between projects and goals."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response.choices[0].message.content)
            score = data.get("alignment_score", 0)
            matched_id = data.get("matched_goal_id")
            
            matched_goal = None
            if matched_id:
                for g in goals:
                    if g.id == matched_id:
                        matched_goal = {"goal_id": g.id, "objective": g.objective[:100]}
                        break
            
            return score, matched_goal
            
        except Exception as e:
            logger.error(f"Semantic alignment check failed: {e}")
            return 0, None
    
    def _create_scope_creep_risk(self, project_id: str, project_name: str):
        """Create a risk entry for scope creep."""
        risk = Risk(
            id=str(uuid.uuid4()),
            project_id=project_id,
            description=f"Scope creep detected: Project '{project_name}' is not aligned to any active strategic goal",
            likelihood=RiskLevel.MEDIUM,
            impact=RiskLevel.MEDIUM,
            mitigation_plan="Review project objectives and either align to existing goals or create new strategic goal",
            created_by="system"
        )
        self.db.add(risk)
    
    def align_project_to_goal(self, project_id: str, goal_id: str) -> Dict[str, Any]:
        """Link a project to a strategic goal."""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        goal = self.db.query(Goal).filter(Goal.id == goal_id).first()
        
        if not project:
            return {"error": "Project not found"}
        if not goal:
            return {"error": "Goal not found"}
        
        # Log the alignment decision
        self._log_decision(
            context=f"Project alignment request for '{project.name}'",
            decision=f"Aligned to goal: {goal.objective[:50]}",
            rationale="Manual alignment by user to establish strategic connection",
            project_id=project_id
        )
        
        return {
            "success": True,
            "project_id": project_id,
            "goal_id": goal_id,
            "message": f"Project '{project.name}' aligned to goal"
        }
    
    def get_goal_alignment(self, goal_id: str) -> Dict[str, Any]:
        """Get all projects aligned to a goal and identify unaligned projects."""
        goal = self.db.query(Goal).filter(Goal.id == goal_id).first()
        if not goal:
            return {"error": "Goal not found"}
        
        # Get linked tasks
        links = self.db.query(GoalTaskLink).filter(
            GoalTaskLink.goal_id == goal_id
        ).all()
        
        # Get unique projects from linked tasks
        aligned_projects = set()
        for link in links:
            if link.task:
                aligned_projects.add(link.task.project_id)
        
        aligned = self.db.query(Project).filter(
            Project.id.in_(aligned_projects)
        ).all() if aligned_projects else []
        
        # Get all projects
        all_projects = self.db.query(Project).all()
        unaligned = [p for p in all_projects if p.id not in aligned_projects]
        
        return {
            "goal_id": goal_id,
            "goal_objective": goal.objective,
            "aligned_projects": [{"id": p.id, "name": p.name} for p in aligned],
            "unaligned_projects": [{"id": p.id, "name": p.name} for p in unaligned[:10]]
        }
    
    def _log_decision(
        self,
        context: str,
        decision: str,
        rationale: str,
        project_id: str = None,
        task_id: str = None
    ):
        """Log agent decision for transparency."""
        log = DecisionLog(
            id=str(uuid.uuid4()),
            context=context,
            decision_made=decision,
            rationale=rationale,
            agent_name="StrategyAgent",
            project_id=project_id,
            task_id=task_id
        )
        self.db.add(log)

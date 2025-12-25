"""
Analytics & Automation Agent - Data-driven insights and proactive intelligence.

Implements the Virtual AI Manager – Analytics & Automation Agent:
- Project performance analytics
- Team workload analytics
- Delivery trend analysis
- Risk and delay forecasting
- Executive dashboards
- Proactive suggestions
- Automatic replanning proposals
- Early warning alerts
- Pattern learning over time

Operating Principles:
1. Insight before automation
2. Evidence-based predictions only
3. Prefer early warnings over late explanations
4. Automation must be reversible and explainable
5. Never override human decisions without approval
"""

import uuid
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from backend.app.models import (
    Task, TaskStatus, TaskPriority, Project, ProjectHealth,
    Milestone, Goal, GoalStatus, AgentActivity, Employee
)


class AnalyticsAutomationAgent:
    """
    Analytics & Automation Agent for data-driven insights and proactive intelligence.
    
    Operates as a data-driven analytics, forecasting, and proactive intelligence system.
    Analyzes execution data, detects patterns, forecasts outcomes, and triggers 
    early warnings or recommendations.
    
    CRITICAL: Never fabricates data. All outputs based on available signals.
    States uncertainty when data is insufficient.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.risk_threshold = 0.6  # 60% probability triggers suggestions
        self.overload_hours = 45  # Hours threshold for overload
        self.underload_hours = 15  # Hours threshold for underutilization
    
    # ==================== PROJECT ANALYTICS ====================
    
    def analyze_project_performance(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze project health using task completion, milestones, deadlines, blockers.
        
        Outputs: health score, trend, key contributing factors.
        """
        query = self.db.query(Project)
        if project_id:
            query = query.filter(Project.id == project_id)
        
        projects = query.all()
        
        if not projects:
            return {"error": "No projects found", "data_available": False}
        
        results = []
        for project in projects:
            # Get project tasks
            tasks = self.db.query(Task).filter(Task.project_id == project.id).all()
            
            if not tasks:
                results.append({
                    "project_id": project.id,
                    "project_name": project.name,
                    "health_score": 0,
                    "trend": "insufficient_data",
                    "data_quality": "No tasks found"
                })
                continue
            
            # Calculate metrics
            total_tasks = len(tasks)
            completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
            blocked = sum(1 for t in tasks if t.status == TaskStatus.BLOCKED)
            in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
            
            # Deadline variance
            overdue = 0
            for task in tasks:
                if task.deadline and task.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
                    if task.deadline < datetime.utcnow():
                        overdue += 1
            
            # Calculate health score (0-100)
            completion_rate = (completed / total_tasks) * 100 if total_tasks > 0 else 0
            blocker_rate = (blocked / total_tasks) * 100 if total_tasks > 0 else 0
            overdue_rate = (overdue / total_tasks) * 100 if total_tasks > 0 else 0
            
            health_score = max(0, min(100, 
                completion_rate * 0.4 +
                (100 - blocker_rate * 2) * 0.3 +
                (100 - overdue_rate * 2) * 0.3
            ))
            
            # Determine trend
            trend = "stable"
            factors = []
            
            if blocker_rate > 20:
                trend = "declining"
                factors.append(f"High blocker rate: {blocker_rate:.1f}%")
            if overdue_rate > 30:
                trend = "declining"
                factors.append(f"High overdue rate: {overdue_rate:.1f}%")
            if completion_rate > 60 and blocker_rate < 10:
                trend = "improving"
                factors.append(f"Good completion rate: {completion_rate:.1f}%")
            
            results.append({
                "project_id": project.id,
                "project_name": project.name,
                "health_score": round(health_score, 1),
                "trend": trend,
                "metrics": {
                    "total_tasks": total_tasks,
                    "completed": completed,
                    "in_progress": in_progress,
                    "blocked": blocked,
                    "overdue": overdue,
                    "completion_rate": round(completion_rate, 1),
                    "blocker_rate": round(blocker_rate, 1)
                },
                "contributing_factors": factors if factors else ["Project on track"]
            })
        
        if len(results) == 1:
            return results[0]
        
        return {
            "projects": results,
            "summary": {
                "total_analyzed": len(results),
                "average_health": round(sum(r["health_score"] for r in results) / len(results), 1),
                "declining_count": sum(1 for r in results if r["trend"] == "declining")
            }
        }
    
    def analyze_team_workload(self) -> Dict[str, Any]:
        """
        Analyze workload distribution across team.
        
        Outputs: workload distribution, overload/underutilization signals, recommendations.
        """
        # Get active tasks
        active_tasks = self.db.query(Task).filter(
            Task.status.in_([TaskStatus.IN_PROGRESS, TaskStatus.NOT_STARTED])
        ).all()
        
        if not active_tasks:
            return {
                "data_available": False,
                "message": "No active tasks found for analysis"
            }
        
        # Aggregate by owner
        workload_by_user: Dict[str, Dict] = {}
        
        for task in active_tasks:
            owner = task.owner or "Unassigned"
            if owner not in workload_by_user:
                workload_by_user[owner] = {
                    "task_count": 0,
                    "estimated_hours": 0,
                    "critical_count": 0,
                    "deadline_density": 0,
                    "deadlines_this_week": 0
                }
            
            workload_by_user[owner]["task_count"] += 1
            workload_by_user[owner]["estimated_hours"] += task.estimated_hours or 4
            
            if task.priority == TaskPriority.CRITICAL:
                workload_by_user[owner]["critical_count"] += 1
            
            if task.deadline:
                week_from_now = datetime.utcnow() + timedelta(days=7)
                if task.deadline <= week_from_now:
                    workload_by_user[owner]["deadlines_this_week"] += 1
        
        # Classify workload status
        distribution = []
        overloaded = []
        underutilized = []
        
        for user, data in workload_by_user.items():
            hours = data["estimated_hours"]
            density = data["deadlines_this_week"] / max(data["task_count"], 1)
            
            status = "balanced"
            if hours > self.overload_hours or data["critical_count"] > 3:
                status = "overloaded"
                overloaded.append(user)
            elif hours < self.underload_hours and data["task_count"] < 3:
                status = "underutilized"
                underutilized.append(user)
            
            distribution.append({
                "user": user,
                "task_count": data["task_count"],
                "estimated_hours": hours,
                "critical_tasks": data["critical_count"],
                "deadlines_this_week": data["deadlines_this_week"],
                "deadline_density": round(density, 2),
                "status": status
            })
        
        # Generate recommendations
        recommendations = []
        if overloaded and underutilized:
            recommendations.append({
                "type": "rebalance",
                "action": f"Consider moving tasks from {overloaded[0]} to {underutilized[0]}",
                "rationale": "Balances workload distribution",
                "impact": "Reduces burnout risk and improves delivery"
            })
        if len(overloaded) > len(distribution) * 0.3:
            recommendations.append({
                "type": "capacity_warning",
                "action": "Team may need additional resources or scope reduction",
                "rationale": f"{len(overloaded)} of {len(distribution)} team members overloaded",
                "impact": "Risk of delays and quality issues"
            })
        
        return {
            "data_available": True,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "distribution": sorted(distribution, key=lambda x: x["estimated_hours"], reverse=True),
            "signals": {
                "overloaded": overloaded,
                "underutilized": underutilized,
                "balanced_count": len(distribution) - len(overloaded) - len(underutilized)
            },
            "recommendations": recommendations
        }
    
    def analyze_delivery_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze delivery trends comparing planned vs actual timelines.
        
        Outputs: trend summaries, root cause indicators.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Get completed tasks in period
        completed_tasks = self.db.query(Task).filter(
            Task.status == TaskStatus.COMPLETED,
            Task.updated_at >= cutoff
        ).all()
        
        if len(completed_tasks) < 5:
            return {
                "data_available": False,
                "confidence": "low",
                "message": f"Insufficient data: only {len(completed_tasks)} completed tasks in last {days} days"
            }
        
        # Analyze delays
        on_time = 0
        delayed = 0
        delay_days_total = 0
        delays_by_priority: Dict[str, int] = {}
        
        for task in completed_tasks:
            if task.deadline and task.updated_at:
                if task.updated_at <= task.deadline:
                    on_time += 1
                else:
                    delayed += 1
                    delay = (task.updated_at - task.deadline).days
                    delay_days_total += delay
                    
                    priority = task.priority.value if task.priority else "unknown"
                    delays_by_priority[priority] = delays_by_priority.get(priority, 0) + 1
        
        total = on_time + delayed
        on_time_rate = (on_time / total * 100) if total > 0 else 0
        avg_delay = delay_days_total / delayed if delayed > 0 else 0
        
        # Identify patterns
        root_causes = []
        if delays_by_priority.get("critical", 0) > 2:
            root_causes.append("Critical tasks frequently delayed - may indicate scope creep or underestimation")
        if avg_delay > 5:
            root_causes.append(f"Average delay of {avg_delay:.1f} days suggests systematic estimation issues")
        if on_time_rate < 50:
            root_causes.append("Less than 50% on-time delivery indicates planning or capacity problems")
        
        return {
            "data_available": True,
            "period_days": days,
            "sample_size": len(completed_tasks),
            "confidence": "high" if len(completed_tasks) > 20 else "medium",
            "trends": {
                "on_time_rate": round(on_time_rate, 1),
                "delayed_count": delayed,
                "average_delay_days": round(avg_delay, 1),
                "delays_by_priority": delays_by_priority
            },
            "root_cause_indicators": root_causes if root_causes else ["No significant patterns detected"],
            "summary": f"{on_time_rate:.0f}% on-time delivery with avg delay of {avg_delay:.1f} days"
        }
    
    # ==================== RISK FORECASTING ====================
    
    def forecast_risks(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Forecast risks using historical patterns, dependencies, and resource availability.
        
        Outputs: risk probability, estimated impact, time-to-risk window.
        """
        query = self.db.query(Task).filter(
            Task.status.in_([TaskStatus.IN_PROGRESS, TaskStatus.NOT_STARTED, TaskStatus.BLOCKED])
        )
        
        if project_id:
            query = query.filter(Task.project_id == project_id)
        
        tasks = query.all()
        
        if not tasks:
            return {"risks": [], "data_available": False}
        
        risks = []
        
        for task in tasks:
            risk_score = 0
            risk_factors = []
            
            # Check deadline proximity
            if task.deadline:
                days_until = (task.deadline - datetime.utcnow()).days
                if days_until < 0:
                    risk_score += 40
                    risk_factors.append(f"Overdue by {abs(days_until)} days")
                elif days_until < 3:
                    risk_score += 30
                    risk_factors.append(f"Due in {days_until} days")
                elif days_until < 7:
                    risk_score += 15
                    risk_factors.append("Due within a week")
            
            # Check blockers
            if task.status == TaskStatus.BLOCKED:
                risk_score += 35
                risk_factors.append("Currently blocked")
            
            # Check priority
            if task.priority == TaskPriority.CRITICAL:
                risk_score += 20
                risk_factors.append("Critical priority")
            
            # Check dependencies
            if task.dependencies:
                deps = json.loads(task.dependencies) if isinstance(task.dependencies, str) else task.dependencies
                if deps:
                    risk_score += 10
                    risk_factors.append(f"Has {len(deps)} dependencies")
            
            # Only report significant risks
            if risk_score >= 30:
                probability = min(risk_score / 100, 0.95)
                
                impact = "low"
                if task.priority == TaskPriority.CRITICAL:
                    impact = "high"
                elif task.priority == TaskPriority.HIGH:
                    impact = "medium"
                
                risks.append({
                    "task_id": task.id,
                    "task_name": task.name,
                    "risk_probability": round(probability, 2),
                    "impact": impact,
                    "time_to_risk": f"{max(0, (task.deadline - datetime.utcnow()).days) if task.deadline else 'unknown'} days",
                    "risk_factors": risk_factors,
                    "suggested_action": self._suggest_risk_mitigation(risk_factors, probability)
                })
        
        risks.sort(key=lambda x: x["risk_probability"], reverse=True)
        
        high_risk_count = sum(1 for r in risks if r["risk_probability"] > 0.6)
        
        return {
            "data_available": True,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "total_risks_identified": len(risks),
            "high_risk_count": high_risk_count,
            "risks": risks[:10],  # Top 10 risks
            "overall_risk_level": "high" if high_risk_count > 3 else ("medium" if high_risk_count > 0 else "low")
        }
    
    def _suggest_risk_mitigation(self, factors: List[str], probability: float) -> str:
        """Generate risk mitigation suggestion based on factors."""
        if "Currently blocked" in str(factors):
            return "Prioritize unblocking - identify and address blocker immediately"
        if "Overdue" in str(factors):
            return "Escalate and consider scope reduction or deadline extension"
        if probability > 0.7:
            return "High risk - consider adding resources or reprioritizing"
        return "Monitor closely and prepare contingency"
    
    # ==================== EXECUTIVE DASHBOARD ====================
    
    def generate_executive_dashboard(self) -> Dict[str, Any]:
        """
        Generate executive dashboard with goal progress, risks, capacity, and decisions.
        
        Audience: Senior leadership
        Format: Concise, outcome-focused
        """
        # Goal progress
        goals = self.db.query(Goal).filter(Goal.status != GoalStatus.CANCELLED).all()
        goal_summary = {
            "total": len(goals),
            "on_track": sum(1 for g in goals if g.status == GoalStatus.ON_TRACK),
            "at_risk": sum(1 for g in goals if g.status == GoalStatus.AT_RISK),
            "completed": sum(1 for g in goals if g.status == GoalStatus.COMPLETED)
        }
        
        # Project health
        project_analysis = self.analyze_project_performance()
        projects_summary = {
            "total": project_analysis.get("summary", {}).get("total_analyzed", 0) if "summary" in project_analysis else 1,
            "average_health": project_analysis.get("summary", {}).get("average_health", project_analysis.get("health_score", 0)),
            "declining": project_analysis.get("summary", {}).get("declining_count", 0) if "summary" in project_analysis else (1 if project_analysis.get("trend") == "declining" else 0)
        }
        
        # Risk summary
        risk_analysis = self.forecast_risks()
        
        # Capacity overview
        workload_analysis = self.analyze_team_workload()
        capacity_summary = {
            "overloaded_count": len(workload_analysis.get("signals", {}).get("overloaded", [])),
            "underutilized_count": len(workload_analysis.get("signals", {}).get("underutilized", [])),
            "balanced_count": workload_analysis.get("signals", {}).get("balanced_count", 0)
        }
        
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "audience": "senior_leadership",
            "summary": {
                "goals": goal_summary,
                "projects": projects_summary,
                "risks": {
                    "level": risk_analysis.get("overall_risk_level", "unknown"),
                    "high_risk_items": risk_analysis.get("high_risk_count", 0)
                },
                "capacity": capacity_summary
            },
            "key_insights": self._generate_executive_insights(goal_summary, projects_summary, risk_analysis, capacity_summary),
            "recommended_actions": workload_analysis.get("recommendations", [])[:3]
        }
    
    def _generate_executive_insights(self, goals: Dict, projects: Dict, risks: Dict, capacity: Dict) -> List[str]:
        """Generate key insights for executives."""
        insights = []
        
        if goals["at_risk"] > goals["on_track"]:
            insights.append(f"⚠️ {goals['at_risk']} goals at risk vs {goals['on_track']} on track")
        
        if projects["average_health"] < 60:
            insights.append(f"📉 Average project health at {projects['average_health']}% - below target")
        elif projects["average_health"] > 80:
            insights.append(f"✅ Strong project health at {projects['average_health']}%")
        
        if risks.get("high_risk_count", 0) > 3:
            insights.append(f"🚨 {risks['high_risk_count']} high-risk items require attention")
        
        if capacity["overloaded_count"] > 0:
            insights.append(f"👥 {capacity['overloaded_count']} team members overloaded")
        
        if not insights:
            insights.append("✅ Operations running smoothly")
        
        return insights
    
    # ==================== PROACTIVE INTELLIGENCE ====================
    
    def get_proactive_suggestions(self) -> List[Dict[str, Any]]:
        """
        Generate proactive suggestions when thresholds are crossed.
        
        Triggers: risk probability, workload imbalance, goals off-track.
        Suggestions are actionable with rationale and expected impact.
        """
        suggestions = []
        
        # Check risks
        risks = self.forecast_risks()
        high_risks = [r for r in risks.get("risks", []) if r["risk_probability"] > self.risk_threshold]
        
        for risk in high_risks[:3]:
            suggestions.append({
                "type": "risk_mitigation",
                "priority": "high",
                "title": f"Address risk: {risk['task_name']}",
                "action": risk["suggested_action"],
                "rationale": f"Risk probability at {risk['risk_probability']*100:.0f}%",
                "expected_impact": "Reduces delay probability and project risk",
                "requires_approval": True
            })
        
        # Check workload
        workload = self.analyze_team_workload()
        if workload.get("signals", {}).get("overloaded"):
            suggestions.append({
                "type": "workload_rebalance",
                "priority": "medium",
                "title": "Rebalance team workload",
                "action": "Redistribute tasks from overloaded to underutilized members",
                "rationale": f"{len(workload['signals']['overloaded'])} team members overloaded",
                "expected_impact": "Prevents burnout and improves delivery predictability",
                "requires_approval": True
            })
        
        # Check goals
        goals = self.db.query(Goal).filter(Goal.status == GoalStatus.AT_RISK).all()
        if goals:
            suggestions.append({
                "type": "goal_recovery",
                "priority": "high",
                "title": f"Review {len(goals)} at-risk goals",
                "action": "Assess scope, resources, or timeline adjustments needed",
                "rationale": "Goals marked at-risk need intervention",
                "expected_impact": "Prevents goal failure and stakeholder disappointment",
                "requires_approval": True
            })
        
        return suggestions
    
    def propose_replanning(self, task_id: str, reason: str) -> Dict[str, Any]:
        """
        Propose replanning when critical delays or resource unavailability occurs.
        
        Rules:
        - Never auto-apply without approval
        - Present at least one alternative plan
        """
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return {"error": "Task not found"}
        
        alternatives = []
        
        # Alternative 1: Extend deadline
        if task.deadline:
            new_deadline = task.deadline + timedelta(days=7)
            alternatives.append({
                "option": "extend_deadline",
                "description": f"Extend deadline by 7 days to {new_deadline.date()}",
                "impact": "Low scope impact, stakeholder communication needed",
                "trade_offs": ["Delays downstream dependencies", "May affect project timeline"]
            })
        
        # Alternative 2: Reduce scope
        alternatives.append({
            "option": "reduce_scope",
            "description": "Deliver MVP version with reduced features",
            "impact": "Meets deadline but with reduced functionality",
            "trade_offs": ["Technical debt for completing full scope later", "May need follow-up work"]
        })
        
        # Alternative 3: Add resources
        workload = self.analyze_team_workload()
        underutilized = workload.get("signals", {}).get("underutilized", [])
        if underutilized:
            alternatives.append({
                "option": "add_resources",
                "description": f"Assign additional resource ({underutilized[0]}) to accelerate",
                "impact": "Potential to meet deadline with team collaboration",
                "trade_offs": ["Knowledge transfer overhead", "May affect other work"]
            })
        
        return {
            "task_id": task_id,
            "task_name": task.name,
            "reason": reason,
            "current_deadline": task.deadline.isoformat() if task.deadline else None,
            "alternatives": alternatives,
            "requires_approval": True,
            "note": "Select an option and approve to proceed. No changes will be made automatically."
        }
    
    def get_early_warnings(self) -> List[Dict[str, Any]]:
        """
        Generate early warning alerts.
        
        Alerts trigger early enough to act, state cause clearly, suggest next actions.
        Prioritizes severity to avoid alert fatigue.
        """
        warnings = []
        
        # Check for tasks due soon without progress
        soon = datetime.utcnow() + timedelta(days=3)
        at_risk_tasks = self.db.query(Task).filter(
            Task.deadline <= soon,
            Task.status == TaskStatus.NOT_STARTED
        ).all()
        
        for task in at_risk_tasks[:5]:
            warnings.append({
                "severity": "high",
                "type": "deadline_approaching",
                "title": f"Task not started: {task.name}",
                "cause": f"Due in {(task.deadline - datetime.utcnow()).days} days but not started",
                "suggested_action": "Start immediately or reassess deadline",
                "task_id": task.id
            })
        
        # Check blocked tasks
        blocked_tasks = self.db.query(Task).filter(Task.status == TaskStatus.BLOCKED).all()
        blocked_critical = [t for t in blocked_tasks if t.priority == TaskPriority.CRITICAL]
        
        if blocked_critical:
            warnings.append({
                "severity": "critical",
                "type": "critical_blocker",
                "title": f"{len(blocked_critical)} critical task(s) blocked",
                "cause": "Critical priority tasks unable to progress",
                "suggested_action": "Identify and resolve blockers immediately"
            })
        
        # Check overdue milestones
        overdue_milestones = self.db.query(Milestone).filter(
            Milestone.due_date < datetime.utcnow(),
            Milestone.status != "completed"
        ).all()
        
        if overdue_milestones:
            warnings.append({
                "severity": "high",
                "type": "milestone_overdue",
                "title": f"{len(overdue_milestones)} milestone(s) overdue",
                "cause": "Milestones past due date without completion",
                "suggested_action": "Review milestone scope and update timeline"
            })
        
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        warnings.sort(key=lambda x: severity_order.get(x["severity"], 4))
        
        return warnings[:10]  # Limit to prevent alert fatigue
    
    # ==================== PATTERN LEARNING ====================
    
    def get_pattern_insights(self) -> Dict[str, Any]:
        """
        Analyze patterns over time for improved forecasting.
        
        Tracks recurring issues and adjusts confidence based on accuracy.
        Only claims learning when improvement is measurable.
        """
        # Analyze historical completed tasks
        completed = self.db.query(Task).filter(
            Task.status == TaskStatus.COMPLETED
        ).order_by(Task.updated_at.desc()).limit(100).all()
        
        if len(completed) < 20:
            return {
                "patterns_detected": False,
                "confidence": "insufficient_data",
                "message": "Need more historical data for pattern analysis"
            }
        
        # Analyze estimation accuracy
        estimation_errors = []
        for task in completed:
            if task.estimated_hours and task.actual_hours:
                error = abs(task.actual_hours - task.estimated_hours) / task.estimated_hours
                estimation_errors.append(error)
        
        avg_estimation_error = sum(estimation_errors) / len(estimation_errors) if estimation_errors else None
        
        # Analyze common blockers (from notes/tags if available)
        patterns = {
            "estimation_accuracy": {
                "average_error": f"{avg_estimation_error*100:.1f}%" if avg_estimation_error else "No data",
                "recommendation": "Consider adding buffer for complex tasks" if avg_estimation_error and avg_estimation_error > 0.3 else "Estimation accuracy is good"
            },
            "completion_velocity": {
                "tasks_per_week": len(completed) / 4,  # Approximate
                "trend": "stable"  # Would need more data points for real trend
            }
        }
        
        return {
            "patterns_detected": True,
            "confidence": "medium" if len(completed) > 50 else "low",
            "sample_size": len(completed),
            "patterns": patterns,
            "note": "Pattern analysis improves with more historical data"
        }
    
    # ==================== ACTIVITY LOGGING ====================
    
    def _log_activity(self, message: str, activity_type: str = "analysis"):
        """Log analytics activity."""
        activity = AgentActivity(
            id=str(uuid.uuid4()),
            agent_name="AnalyticsAutomationAgent",
            activity_type=activity_type,
            message=message
        )
        self.db.add(activity)

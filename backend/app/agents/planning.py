"""
Planning Agent - Goal Decomposition and Timeline Suggestions.

Implements:
- Goal decomposition into tasks
- Timeline validation
- Plan optimization
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from openai import OpenAI


class PlanningAgent:
    """
    Planning Agent for goal decomposition and project planning.
    Uses LLM for intelligent task breakdown.
    """
    
    SYSTEM_PROMPT = """
    You are an expert project planning assistant.
    Your role is to:
    1. Break down high-level goals into concrete, actionable tasks
    2. Suggest realistic timelines based on task complexity
    3. Identify dependencies between tasks
    4. Flag potential risks and bottlenecks
    
    Always provide structured, actionable output.
    Be conservative with time estimates - it's better to under-promise and over-deliver.
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            print("Warning: OPENAI_API_KEY not found")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.model = "gpt-4o"
    
    def _query_llm(self, prompt: str) -> str:
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    
    def decompose_goal(
        self,
        goal_text: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Decompose a high-level goal into actionable tasks.
        
        Args:
            goal_text: The goal to decompose
            constraints: Optional constraints (deadline, team size, etc.)
        
        Returns:
            Dictionary with tasks, dependencies, and timeline
        """
        constraint_text = ""
        if constraints:
            constraint_text = f"\nConstraints: {json.dumps(constraints)}"
        
        prompt = f"""
        Decompose this goal into actionable tasks:
        
        GOAL: {goal_text}
        {constraint_text}
        
        Return JSON with:
        {{
            "summary": "Brief summary of the plan",
            "tasks": [
                {{
                    "name": "Task name",
                    "description": "What needs to be done",
                    "priority": "critical|high|medium|low",
                    "estimated_hours": number,
                    "skills_required": ["skill1", "skill2"],
                    "depends_on": [indices of dependent tasks]
                }}
            ],
            "milestones": [
                {{
                    "name": "Milestone name",
                    "task_indices": [indices of tasks in this milestone],
                    "target_percentage": number
                }}
            ],
            "risks": [
                {{
                    "description": "Risk description",
                    "mitigation": "How to mitigate"
                }}
            ],
            "total_estimated_hours": number
        }}
        """
        
        result = self._query_llm(prompt)
        return json.loads(result)
    
    def suggest_timeline(
        self,
        tasks: List[Dict[str, Any]],
        start_date: Optional[datetime] = None,
        team_size: int = 1,
        hours_per_day: int = 6
    ) -> Dict[str, Any]:
        """
        Suggest a realistic timeline for a set of tasks.
        
        Args:
            tasks: List of tasks with estimated hours
            start_date: When to start
            team_size: Number of people working
            hours_per_day: Productive hours per person per day
        
        Returns:
            Timeline with suggested dates for each task
        """
        if start_date is None:
            start_date = datetime.utcnow()
        
        # Calculate total hours and duration
        total_hours = sum(t.get("estimated_hours", 4) for t in tasks)
        daily_capacity = team_size * hours_per_day
        estimated_days = total_hours / daily_capacity if daily_capacity > 0 else total_hours
        
        # Add buffer for dependencies and context switching
        buffer_factor = 1.3
        estimated_days = int(estimated_days * buffer_factor)
        
        # Assign dates to tasks
        scheduled_tasks = []
        current_date = start_date
        
        for task in tasks:
            hours = task.get("estimated_hours", 4)
            days_needed = max(1, int(hours / hours_per_day))
            
            scheduled_tasks.append({
                "name": task.get("name", "Unnamed Task"),
                "start_date": current_date.isoformat(),
                "end_date": (current_date + timedelta(days=days_needed)).isoformat(),
                "days": days_needed
            })
            
            current_date += timedelta(days=days_needed)
        
        return {
            "start_date": start_date.isoformat(),
            "end_date": current_date.isoformat(),
            "total_days": estimated_days,
            "team_size": team_size,
            "schedule": scheduled_tasks,
            "recommendations": [
                "Add 20% buffer for unexpected issues",
                "Schedule regular check-ins to track progress",
                "Prioritize critical path tasks"
            ]
        }
    
    def validate_plan(
        self,
        tasks: List[Dict[str, Any]],
        deadline: Optional[datetime] = None,
        available_resources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate a project plan and identify issues.
        
        Args:
            tasks: List of planned tasks
            deadline: Target deadline
            available_resources: List of available team members
        
        Returns:
            Validation results with issues and recommendations
        """
        issues = []
        warnings = []
        recommendations = []
        
        # Check total hours
        total_hours = sum(t.get("estimated_hours", 0) for t in tasks)
        
        if deadline:
            days_available = (deadline - datetime.utcnow()).days
            hours_available = days_available * 6  # Assuming 6 productive hours/day
            
            if total_hours > hours_available:
                issues.append({
                    "type": "timeline",
                    "message": f"Estimated {total_hours}h exceeds available {hours_available}h before deadline",
                    "severity": "high"
                })
                recommendations.append("Consider reducing scope or extending deadline")
        
        # Check for unassigned tasks
        unassigned = [t for t in tasks if not t.get("owner")]
        if unassigned:
            warnings.append({
                "type": "resources",
                "message": f"{len(unassigned)} tasks have no owner assigned",
                "severity": "medium"
            })
        
        # Check for missing estimates
        no_estimate = [t for t in tasks if not t.get("estimated_hours")]
        if no_estimate:
            warnings.append({
                "type": "planning",
                "message": f"{len(no_estimate)} tasks missing time estimates",
                "severity": "medium"
            })
            recommendations.append("Add time estimates to all tasks for accurate planning")
        
        # Check priority distribution
        priority_counts = {}
        for t in tasks:
            p = t.get("priority", "medium")
            priority_counts[p] = priority_counts.get(p, 0) + 1
        
        if priority_counts.get("critical", 0) > len(tasks) * 0.3:
            warnings.append({
                "type": "prioritization",
                "message": "More than 30% of tasks marked as critical",
                "severity": "medium"
            })
            recommendations.append("Review priorities - if everything is critical, nothing is")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "recommendations": recommendations,
            "summary": {
                "total_tasks": len(tasks),
                "total_hours": total_hours,
                "priority_distribution": priority_counts
            }
        }
    
    def optimize_plan(
        self,
        tasks: List[Dict[str, Any]],
        optimization_goal: str = "time"  # time, cost, risk
    ) -> Dict[str, Any]:
        """
        Suggest optimizations for a project plan.
        
        Args:
            tasks: Current task list
            optimization_goal: What to optimize for
        
        Returns:
            Optimization suggestions
        """
        prompt = f"""
        Analyze this project plan and suggest optimizations for {optimization_goal}:
        
        TASKS: {json.dumps(tasks)}
        
        Return JSON with:
        {{
            "current_assessment": "Brief assessment of current plan",
            "optimizations": [
                {{
                    "type": "parallelization|elimination|automation|delegation",
                    "description": "What to optimize",
                    "impact": "Expected improvement",
                    "effort": "low|medium|high"
                }}
            ],
            "potential_savings": {{
                "hours": number,
                "percentage": number
            }},
            "trade_offs": ["List of trade-offs to consider"]
        }}
        """
        
        result = self._query_llm(prompt)
        return json.loads(result)


# Singleton instance
planning_agent = PlanningAgent()

import os
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from backend.app.schemas.managerial import (
    RiskAnalysisResponse, StandupResponse, ReportResponse,
    StructuredGoal, ConversationSummary, StakeholderQueryResponse, ReminderResponse
)

# Comprehensive System Prompt based on PDF requirements
MANAGERIAL_SYSTEM_PROMPT = """
You are Virtual AI Manager - Managerial Intelligence Agent.

You operate as a senior manager and decision-support system. 
Your role is to: Ensure alignment with goals, Evaluate trade-offs, Detect risks, and Communicate clearly.

OPERATING PRINCIPLES:
1. Anchor decisions to goals, data, and constraints.
2. Prefer clarity over optimism.
3. Never make assumptions when information is missing.
4. Explain reasoning in plain language suitable for non-technical stakeholders.

CAPABILITIES:
1. Strategy: Parse vague goals into structured KPIs. Identify risks and mitigations.
2. Communication: Generate standups, reports, and respectful reminders.
3. Intelligence: Summarize conversations for decisions/actions. Answer stakeholder queries transparently.
4. Alignment: Track task-to-goal alignment, detect scope creep.
5. Decision Support: Analyze trade-offs, provide recommendations with confidence levels.

OUTPUT REQUIREMENTS:
- Structured JSON where possible.
- Short reasoning blocks.
- No unnecessary verbosity.
- Include confidence levels when applicable.
"""


class ManagerialAgent:
    """
    Enhanced Managerial Intelligence Agent.
    Implements all capabilities from the Priority 1 Managerial Intelligence Prompt.
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            print("Warning: OPENAI_API_KEY not found in environment variables.")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.model = "gpt-4o"

    def _query_llm(self, user_content: str, response_format=None) -> str:
        if not self.client:
            raise ValueError("OpenAI API key not configured")
            
        messages = [
            {"role": "system", "content": MANAGERIAL_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]
        kwargs = {"model": self.model, "messages": messages}
        if response_format:
            kwargs["response_format"] = response_format

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    # ==================== STRATEGY & RISK ====================
    
    def analyze_risks(self, tasks: list, goals: list) -> RiskAnalysisResponse:
        """Analyze project state for risks and suggest mitigations."""
        prompt = f"""
        Analyze the following Project State for Risks:
        GOALS: {json.dumps(goals)}
        TASKS: {json.dumps(tasks)}
        
        Identify risks (delays, bottlenecks, resource issues). 
        For each risk, suggest mitigations with cost/benefit analysis.
        
        Return JSON with:
        {{
            "risks": [
                {{
                    "description": "Risk description",
                    "likelihood": "Low|Medium|High",
                    "impact": "Low|Medium|High",
                    "affected_goals": ["goal1", "goal2"],
                    "mitigations": [
                        {{
                            "strategy": "What to do",
                            "cost_vs_benefit": "Explanation",
                            "required_approvals": ["manager", "stakeholder"]
                        }}
                    ]
                }}
            ],
            "overall_assessment": "Brief overall risk assessment"
        }}
        """
        res = self._query_llm(prompt, response_format={"type": "json_object"})
        return RiskAnalysisResponse(**json.loads(res))

    def refine_goal(self, raw_text: str) -> StructuredGoal:
        """Parse vague goal into structured, measurable format."""
        prompt = f"""
        Parse this goal into a structured format: "{raw_text}"
        
        Extract:
        - Objective: Clear statement of what to achieve
        - KPIs: Specific, measurable success metrics
        - Time horizon: monthly, quarterly, yearly
        - Owner: Who's responsible (if mentioned)
        
        Validate if it is measurable. If not, state what is missing.
        
        Return JSON with:
        {{
            "objective": "Clear objective statement",
            "kpis": ["metric 1", "metric 2"],
            "time_horizon": "quarterly",
            "owner": "Person or null",
            "is_measurable": true/false,
            "missing_criteria": "What's missing if not measurable"
        }}
        """
        res = self._query_llm(prompt, response_format={"type": "json_object"})
        return StructuredGoal(**json.loads(res))

    def analyze_tradeoffs(self, options: List[Dict[str, Any]], context: str) -> Dict[str, Any]:
        """Analyze trade-offs between multiple options."""
        prompt = f"""
        Analyze trade-offs between these options:
        
        CONTEXT: {context}
        OPTIONS: {json.dumps(options)}
        
        For each option, evaluate:
        - Impact (business value)
        - Cost (resources required)
        - Risk (what could go wrong)
        - Effort (time and complexity)
        
        Return JSON with:
        {{
            "analysis": [
                {{
                    "option": "Option name",
                    "impact": "High|Medium|Low",
                    "cost": "High|Medium|Low",
                    "risk": "High|Medium|Low",
                    "effort": "High|Medium|Low",
                    "pros": ["list of advantages"],
                    "cons": ["list of disadvantages"]
                }}
            ],
            "recommendation": "Which option to choose",
            "confidence": "High|Medium|Low",
            "reasoning": "Why this recommendation",
            "assumptions": ["assumptions made"]
        }}
        """
        res = self._query_llm(prompt, response_format={"type": "json_object"})
        return json.loads(res)

    def suggest_priority_changes(
        self,
        tasks: List[Dict[str, Any]],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Suggest task priority changes based on constraints."""
        prompt = f"""
        Suggest priority changes for these tasks given constraints:
        
        TASKS: {json.dumps(tasks)}
        CONSTRAINTS: {json.dumps(constraints)}
        
        Return JSON with:
        {{
            "recommendations": [
                {{
                    "task_id": "id",
                    "task_name": "name",
                    "current_priority": "current",
                    "suggested_priority": "new priority",
                    "reason": "why change",
                    "impact": "what happens if not changed"
                }}
            ],
            "summary": "Overall recommendation summary"
        }}
        """
        res = self._query_llm(prompt, response_format={"type": "json_object"})
        return json.loads(res)

    # ==================== COMMUNICATION ====================
    
    def generate_standup_summary(self, completed: list, planned: list, blockers: list) -> StandupResponse:
        """Generate a daily standup summary."""
        prompt = f"""
        Generate a Daily Standup Summary.
        Completed: {json.dumps(completed)}
        Planned: {json.dumps(planned)}
        Blockers: {json.dumps(blockers)}
        
        Tone: Clear, Neutral, Action-oriented.
        
        Return JSON with:
        {{
            "summary": "Brief overall summary",
            "action_items": ["List of action items to address blockers"]
        }}
        """
        res = self._query_llm(prompt, response_format={"type": "json_object"})
        return StandupResponse(**json.loads(res))

    def generate_report(
        self,
        report_type: str,
        goals: list,
        achievements: list,
        risks: list,
        priorities: list,
        audience: str
    ) -> ReportResponse:
        """Generate a progress report tailored to audience."""
        audience_guidance = {
            "Executive": "Focus on outcomes, ROI, and high-level status. Be concise.",
            "Team": "Include technical details and specific task progress."
        }
        
        prompt = f"""
        Generate a {report_type} Report for {audience}.
        
        Guidance: {audience_guidance.get(audience, '')}
        
        Goals Progress: {json.dumps(goals)}
        Achievements: {json.dumps(achievements)}
        Risks: {json.dumps(risks)}
        Upcoming Priorities: {json.dumps(priorities)}
        
        Return JSON with:
        {{
            "report_content": "Full formatted report",
            "key_takeaways": ["Main points to remember"]
        }}
        """
        res = self._query_llm(prompt, response_format={"type": "json_object"})
        return ReportResponse(**json.loads(res))

    def generate_reminder(self, recipient: str, topic: str, context: str, tone: str) -> ReminderResponse:
        """Generate a respectful reminder message."""
        prompt = f"""
        Draft a reminder message.
        Recipient: {recipient}
        Topic: {topic}
        Context: {context}
        Tone: {tone} (Respectful, avoid blame, provide context).
        
        Return JSON with:
        {{
            "message": "Full reminder message"
        }}
        """
        res = self._query_llm(prompt, response_format={"type": "json_object"})
        return ReminderResponse(**json.loads(res))

    def generate_escalation_brief(
        self,
        task_name: str,
        issue: str,
        history: List[str],
        suggested_actions: List[str]
    ) -> Dict[str, Any]:
        """Generate a brief for escalation."""
        prompt = f"""
        Generate an escalation brief.
        
        Task: {task_name}
        Issue: {issue}
        History: {json.dumps(history)}
        Suggested Actions: {json.dumps(suggested_actions)}
        
        Return JSON with:
        {{
            "summary": "One-paragraph summary",
            "urgency": "Critical|High|Medium",
            "impact_statement": "What happens if not addressed",
            "recommended_action": "What should be done",
            "decision_needed": "What decision is required"
        }}
        """
        res = self._query_llm(prompt, response_format={"type": "json_object"})
        return json.loads(res)

    # ==================== INTELLIGENCE ====================
    
    def summarize_conversation(self, transcript: str) -> ConversationSummary:
        """Summarize a conversation/meeting transcript."""
        prompt = f"""
        Summarize this conversation transcript:
        "{transcript}"
        
        Extract:
        - Decisions made
        - Action items (with owners if mentioned)
        - Unresolved questions
        
        Return JSON with:
        {{
            "decisions": ["Decision 1", "Decision 2"],
            "action_items": ["Action 1", "Action 2"],
            "unresolved_questions": ["Question 1"]
        }}
        """
        res = self._query_llm(prompt, response_format={"type": "json_object"})
        return ConversationSummary(**json.loads(res))

    def answer_stakeholder_query(self, query: str, context: str) -> StakeholderQueryResponse:
        """Answer stakeholder questions based on project context."""
        prompt = f"""
        Answer this stakeholder query based on project state:
        Query: "{query}"
        Context: "{context}"
        
        Requirements: 
        - Be transparent about uncertainty
        - Base response on available data
        - Include reasoning
        - Don't fabricate information
        
        Return JSON with:
        {{
            "answer": "Clear, direct answer",
            "reasoning": "How you arrived at this answer"
        }}
        """
        res = self._query_llm(prompt, response_format={"type": "json_object"})
        return StakeholderQueryResponse(**json.loads(res))

    def analyze_team_sentiment(self, updates: List[str]) -> Dict[str, Any]:
        """Analyze team sentiment from updates and communications."""
        prompt = f"""
        Analyze team sentiment from these updates:
        {json.dumps(updates)}
        
        Return JSON with:
        {{
            "overall_sentiment": "Positive|Neutral|Concerned|Stressed",
            "key_themes": ["theme1", "theme2"],
            "areas_of_concern": ["concern1"],
            "positive_indicators": ["positive1"],
            "recommendations": ["recommendation1"]
        }}
        """
        res = self._query_llm(prompt, response_format={"type": "json_object"})
        return json.loads(res)

    def extract_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract actionable insights from project data."""
        prompt = f"""
        Extract actionable insights from this project data:
        {json.dumps(data)}
        
        Return JSON with:
        {{
            "insights": [
                {{
                    "observation": "What you noticed",
                    "implication": "What it means",
                    "recommendation": "What to do about it",
                    "priority": "High|Medium|Low"
                }}
            ],
            "summary": "Overall summary of insights"
        }}
        """
        res = self._query_llm(prompt, response_format={"type": "json_object"})
        return json.loads(res)


# Singleton instance
managerial_agent = ManagerialAgent()
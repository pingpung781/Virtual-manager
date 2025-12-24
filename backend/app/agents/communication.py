"""
Communication Agent - Automated Communication Generation.

Implements:
- Standup summaries
- Progress reports
- Reminder messages
- Meeting summaries
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from openai import OpenAI


class CommunicationAgent:
    """
    Communication Agent for generating various types of communications.
    Uses LLM for natural language generation.
    """
    
    SYSTEM_PROMPT = """
    You are a professional communication assistant for project management.
    Your role is to:
    1. Generate clear, concise, professional communications
    2. Adapt tone based on audience (executives, team, individuals)
    3. Focus on actionable information
    4. Be respectful and supportive, never blame-oriented
    
    Always structure output in a clear, scannable format.
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.model = "gpt-4o"
    
    def _query_llm(self, prompt: str, system_override: Optional[str] = None) -> str:
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_override or self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    
    def generate_standup(
        self,
        user: str,
        completed: List[str],
        planned: List[str],
        blockers: List[str]
    ) -> Dict[str, Any]:
        """
        Generate a daily standup summary.
        
        Args:
            user: Who the standup is for
            completed: What was completed yesterday
            planned: What's planned for today
            blockers: Any blockers
        
        Returns:
            Formatted standup message
        """
        prompt = f"""
        Generate a daily standup summary for {user}.
        
        Yesterday's Completed Work:
        {json.dumps(completed)}
        
        Today's Planned Work:
        {json.dumps(planned)}
        
        Current Blockers:
        {json.dumps(blockers)}
        
        Return JSON with:
        {{
            "summary": "Brief overall summary",
            "formatted_message": "Full formatted standup message",
            "action_items": ["List of action items derived from blockers"],
            "needs_follow_up": boolean
        }}
        """
        
        result = self._query_llm(prompt)
        return json.loads(result)
    
    def generate_progress_report(
        self,
        report_type: str,  # daily, weekly, monthly
        audience: str,  # executive, team, stakeholder
        project_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a progress report.
        
        Args:
            report_type: Type of report
            audience: Target audience
            project_data: Data to include in report
        
        Returns:
            Formatted report
        """
        audience_guidance = {
            "executive": "Focus on outcomes, risks, and high-level status. Be concise.",
            "team": "Include technical details and specific task updates.",
            "stakeholder": "Focus on milestone progress and timeline adherence."
        }
        
        prompt = f"""
        Generate a {report_type} progress report for {audience} audience.
        
        Guidance: {audience_guidance.get(audience, '')}
        
        Project Data:
        {json.dumps(project_data, indent=2)}
        
        Return JSON with:
        {{
            "title": "Report title",
            "executive_summary": "2-3 sentence summary",
            "key_metrics": {{
                "completed": number,
                "in_progress": number,
                "blocked": number,
                "completion_rate": "percentage"
            }},
            "highlights": ["Key achievements"],
            "risks": ["Current risks and mitigations"],
            "next_steps": ["What's coming next"],
            "full_report": "Full formatted report text"
        }}
        """
        
        result = self._query_llm(prompt)
        return json.loads(result)
    
    def generate_reminder(
        self,
        recipient: str,
        topic: str,
        context: str,
        deadline: Optional[datetime] = None,
        tone: str = "friendly"
    ) -> Dict[str, Any]:
        """
        Generate a polite reminder message.
        
        Args:
            recipient: Who to remind
            topic: What the reminder is about
            context: Additional context
            deadline: Optional deadline
            tone: Tone of the message
        
        Returns:
            Reminder message
        """
        deadline_text = f"Deadline: {deadline.strftime('%B %d, %Y')}" if deadline else ""
        
        prompt = f"""
        Generate a {tone} reminder message.
        
        Recipient: {recipient}
        Topic: {topic}
        Context: {context}
        {deadline_text}
        
        Requirements:
        - Be respectful and professional
        - Provide context, not just demand
        - Avoid blame language
        - Include specific action needed
        
        Return JSON with:
        {{
            "subject": "Email subject line",
            "greeting": "Appropriate greeting",
            "message": "Main message body",
            "call_to_action": "What you need them to do",
            "closing": "Professional closing",
            "full_message": "Complete formatted message"
        }}
        """
        
        result = self._query_llm(prompt)
        return json.loads(result)
    
    def summarize_meeting(
        self,
        transcript: str,
        meeting_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Summarize a meeting transcript.
        
        Args:
            transcript: Meeting transcript
            meeting_type: Type of meeting
        
        Returns:
            Meeting summary with decisions and action items
        """
        prompt = f"""
        Summarize this {meeting_type} meeting transcript.
        
        Transcript:
        {transcript}
        
        Return JSON with:
        {{
            "summary": "2-3 sentence summary",
            "key_topics": ["Topics discussed"],
            "decisions_made": [
                {{
                    "decision": "What was decided",
                    "rationale": "Why",
                    "owner": "Who's responsible"
                }}
            ],
            "action_items": [
                {{
                    "task": "What needs to be done",
                    "owner": "Who",
                    "due_date": "When if mentioned"
                }}
            ],
            "unresolved_questions": ["Questions that weren't answered"],
            "follow_ups_needed": ["Things that need follow-up"]
        }}
        """
        
        result = self._query_llm(prompt)
        return json.loads(result)
    
    def generate_status_update(
        self,
        task_name: str,
        status: str,
        progress_notes: str,
        audience: str = "team"
    ) -> Dict[str, Any]:
        """
        Generate a status update message.
        
        Args:
            task_name: Name of the task
            status: Current status
            progress_notes: What's been done
            audience: Who the update is for
        
        Returns:
            Formatted status update
        """
        prompt = f"""
        Generate a status update for {audience}.
        
        Task: {task_name}
        Status: {status}
        Progress Notes: {progress_notes}
        
        Return JSON with:
        {{
            "headline": "One-line status",
            "details": "Detailed update",
            "next_actions": ["What happens next"],
            "needs_input": boolean,
            "formatted_update": "Full formatted update"
        }}
        """
        
        result = self._query_llm(prompt)
        return json.loads(result)
    
    def generate_escalation_message(
        self,
        task_name: str,
        issue: str,
        suggested_action: str,
        recipient: str
    ) -> Dict[str, Any]:
        """
        Generate an escalation message.
        
        Args:
            task_name: Task with issue
            issue: What the problem is
            suggested_action: Recommended action
            recipient: Who to escalate to
        
        Returns:
            Escalation message
        """
        prompt = f"""
        Generate an escalation message.
        
        Recipient: {recipient}
        Task: {task_name}
        Issue: {issue}
        Suggested Action: {suggested_action}
        
        Requirements:
        - Be clear about the urgency
        - Provide context
        - Present the suggested solution
        - Request specific action
        
        Return JSON with:
        {{
            "subject": "Urgent but professional subject",
            "message": "Clear, professional escalation message",
            "urgency_level": "high|medium",
            "action_requested": "Specific ask"
        }}
        """
        
        result = self._query_llm(prompt)
        return json.loads(result)


# Singleton instance
communication_agent = CommunicationAgent()

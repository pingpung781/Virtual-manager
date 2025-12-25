"""
Growth & Scaling Agent - Hiring, Onboarding, and Knowledge Management.

Implements the Virtual AI Manager – Growth & Scaling Agent:
- Role requirements definition
- Job description generation
- Candidate pipeline tracking
- Interview scheduling and feedback
- Onboarding plan generation
- Knowledge base management

Operating Principles:
1. Hiring quality is more important than speed
2. Human approval is mandatory for offers and rejections
3. Consistency and fairness in hiring and onboarding
4. Knowledge should be reusable and continuously improving
5. Avoid bias and ungrounded assumptions
"""

import uuid
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models import (
    JobRole, JobRoleStatus, Candidate, CandidateStage, Interview, InterviewStatus,
    OnboardingPlan, OnboardingTask, OnboardingStatus, KnowledgeArticle, ArticleStatus,
    Employee, AgentActivity
)


class GrowthScalingAgent:
    """
    Growth & Scaling Agent for hiring, onboarding, and knowledge management.
    
    Operates as a hiring manager, recruiter coordinator, and onboarding facilitator.
    Responsible for helping the organization scale teams while maintaining quality,
    fairness, and knowledge continuity.
    
    CRITICAL: Never makes final hiring decisions autonomously.
    All recommendations must be explainable and reviewable by humans.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== ROLE DEFINITION ====================
    
    def define_role_requirements(
        self,
        title: str,
        team: str,
        responsibilities: List[str],
        required_skills: List[str],
        nice_to_have_skills: Optional[List[str]] = None,
        experience_years: int = 0,
        seniority_level: str = "mid",
        location: Optional[str] = None,
        work_mode: str = "hybrid",
        reports_to: Optional[str] = None,
        success_criteria: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Define role requirements when a role is requested.
        
        Clarifies: role purpose, team context, required skills, 
        must-have vs nice-to-have, and success criteria.
        """
        role = JobRole(
            id=str(uuid.uuid4()),
            title=title,
            team=team,
            responsibilities=json.dumps(responsibilities),
            required_skills=json.dumps(required_skills),
            nice_to_have_skills=json.dumps(nice_to_have_skills or []),
            experience_years=experience_years,
            seniority_level=seniority_level,
            location=location,
            work_mode=work_mode,
            reports_to=reports_to,
            success_criteria=json.dumps(success_criteria or [])
        )
        self.db.add(role)
        
        self._log_activity(f"Defined role requirements: {title} for {team}")
        
        self.db.commit()
        self.db.refresh(role)
        
        return {
            "role_id": role.id,
            "title": title,
            "team": team,
            "responsibilities": responsibilities,
            "required_skills": required_skills,
            "nice_to_have_skills": nice_to_have_skills,
            "seniority_level": seniority_level,
            "status": "draft",
            "requires_approval": True,
            "next_step": "Generate job description and get human approval"
        }
    
    def generate_job_description(self, role_id: str) -> Dict[str, Any]:
        """
        Generate a professional job description from role requirements.
        
        Job descriptions must:
        - Reflect real responsibilities
        - Avoid unnecessary jargon
        - State expectations and growth opportunities
        - Include location, work mode, and reporting structure
        """
        role = self.db.query(JobRole).filter(JobRole.id == role_id).first()
        if not role:
            return {"error": "Role not found"}
        
        responsibilities = json.loads(role.responsibilities or "[]")
        required_skills = json.loads(role.required_skills or "[]")
        nice_to_have = json.loads(role.nice_to_have_skills or "[]")
        success_criteria = json.loads(role.success_criteria or "[]")
        
        # Generate structured JD
        jd_sections = []
        
        jd_sections.append(f"# {role.title}")
        jd_sections.append(f"\n**Team:** {role.team}")
        if role.department:
            jd_sections.append(f"**Department:** {role.department}")
        jd_sections.append(f"**Location:** {role.location or 'Flexible'}")
        jd_sections.append(f"**Work Mode:** {role.work_mode}")
        if role.reports_to:
            jd_sections.append(f"**Reports To:** {role.reports_to}")
        
        jd_sections.append("\n## About the Role")
        jd_sections.append(f"We are looking for a {role.seniority_level} {role.title} to join our {role.team} team.")
        
        if responsibilities:
            jd_sections.append("\n## Responsibilities")
            for resp in responsibilities:
                jd_sections.append(f"- {resp}")
        
        if required_skills:
            jd_sections.append("\n## Required Skills & Experience")
            jd_sections.append(f"- {role.experience_years}+ years of relevant experience")
            for skill in required_skills:
                jd_sections.append(f"- {skill}")
        
        if nice_to_have:
            jd_sections.append("\n## Nice to Have")
            for skill in nice_to_have:
                jd_sections.append(f"- {skill}")
        
        if success_criteria:
            jd_sections.append("\n## What Success Looks Like")
            for criteria in success_criteria:
                jd_sections.append(f"- {criteria}")
        
        jd_sections.append("\n## Growth Opportunities")
        jd_sections.append("- Mentorship and learning opportunities")
        jd_sections.append("- Path to senior/lead roles")
        jd_sections.append("- Cross-team collaboration")
        
        job_description = "\n".join(jd_sections)
        
        role.job_description = job_description
        self.db.commit()
        
        self._log_activity(f"Generated job description for: {role.title}")
        
        return {
            "role_id": role_id,
            "title": role.title,
            "job_description": job_description,
            "status": "draft",
            "requires_approval": True,
            "next_step": "Review and approve before posting"
        }
    
    def approve_job_posting(
        self,
        role_id: str,
        approved_by: str
    ) -> Dict[str, Any]:
        """
        Approve a job for posting (requires human approval).
        
        Constraint: Do not post without human approval.
        """
        role = self.db.query(JobRole).filter(JobRole.id == role_id).first()
        if not role:
            return {"error": "Role not found"}
        
        role.is_approved = True
        role.approved_by = approved_by
        role.approved_at = datetime.utcnow()
        role.status = JobRoleStatus.OPEN
        
        self._log_activity(f"Job posting approved by {approved_by}: {role.title}")
        
        self.db.commit()
        
        return {
            "role_id": role_id,
            "title": role.title,
            "status": "open",
            "approved_by": approved_by,
            "approved_at": role.approved_at.isoformat()
        }
    
    def get_open_roles(self) -> List[Dict[str, Any]]:
        """Get all open job roles."""
        roles = self.db.query(JobRole).filter(
            JobRole.status == JobRoleStatus.OPEN
        ).all()
        
        return [{
            "id": r.id,
            "title": r.title,
            "team": r.team,
            "seniority_level": r.seniority_level,
            "work_mode": r.work_mode,
            "candidate_count": len(r.candidates),
            "created_at": r.created_at.isoformat()
        } for r in roles]
    
    # ==================== CANDIDATE PIPELINE ====================
    
    def add_candidate(
        self,
        job_role_id: str,
        name: str,
        email: str,
        phone: Optional[str] = None,
        resume_url: Optional[str] = None,
        source: str = "website"
    ) -> Dict[str, Any]:
        """Add a new candidate to the pipeline."""
        role = self.db.query(JobRole).filter(JobRole.id == job_role_id).first()
        if not role:
            return {"error": "Job role not found"}
        
        candidate = Candidate(
            id=str(uuid.uuid4()),
            job_role_id=job_role_id,
            name=name,
            email=email,
            phone=phone,
            resume_url=resume_url,
            source=source,
            stage=CandidateStage.APPLIED
        )
        self.db.add(candidate)
        
        self._log_activity(f"New candidate added: {name} for {role.title}")
        
        self.db.commit()
        self.db.refresh(candidate)
        
        return {
            "candidate_id": candidate.id,
            "name": name,
            "role": role.title,
            "stage": "applied",
            "next_step": "Screen candidate and update stage"
        }
    
    def get_candidate_pipeline(
        self,
        job_role_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get candidate pipeline grouped by stage.
        
        Maintains up-to-date candidate status, avoids stale candidates.
        """
        query = self.db.query(Candidate)
        
        if job_role_id:
            query = query.filter(Candidate.job_role_id == job_role_id)
        
        candidates = query.all()
        
        pipeline = {
            "applied": [],
            "screening": [],
            "interviewing": [],
            "offer": [],
            "hired": [],
            "rejected": []
        }
        
        stale_candidates = []
        stale_threshold = datetime.utcnow() - timedelta(days=14)
        
        for c in candidates:
            candidate_data = {
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "source": c.source,
                "updated_at": c.updated_at.isoformat(),
                "days_in_stage": (datetime.utcnow() - c.updated_at).days
            }
            
            pipeline[c.stage.value].append(candidate_data)
            
            # Flag stale candidates
            if c.updated_at < stale_threshold and c.stage not in [CandidateStage.HIRED, CandidateStage.REJECTED]:
                stale_candidates.append({
                    "id": c.id,
                    "name": c.name,
                    "stage": c.stage.value,
                    "days_stale": (datetime.utcnow() - c.updated_at).days
                })
        
        return {
            "pipeline": pipeline,
            "total_candidates": len(candidates),
            "by_stage": {stage: len(candidates) for stage, candidates in pipeline.items()},
            "stale_candidates": stale_candidates,
            "stale_warning": len(stale_candidates) > 0
        }
    
    def update_candidate_stage(
        self,
        candidate_id: str,
        new_stage: str,
        notes: Optional[str] = None,
        approved_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update candidate stage in the pipeline.
        
        IMPORTANT: Rejections require human approval (approved_by).
        """
        candidate = self.db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            return {"error": "Candidate not found"}
        
        # Rejection requires human approval
        if new_stage == "rejected":
            if not approved_by:
                return {
                    "error": "Rejection requires human approval",
                    "requires_approval": True,
                    "action": "Provide approved_by to confirm rejection"
                }
            candidate.rejection_approved_by = approved_by
        
        old_stage = candidate.stage.value
        candidate.stage = CandidateStage(new_stage)
        if notes:
            candidate.notes = (candidate.notes or "") + f"\n[{datetime.utcnow().isoformat()}] {notes}"
        
        self._log_activity(
            f"Candidate {candidate.name} moved from {old_stage} to {new_stage}"
        )
        
        self.db.commit()
        
        return {
            "candidate_id": candidate_id,
            "name": candidate.name,
            "old_stage": old_stage,
            "new_stage": new_stage,
            "updated_at": candidate.updated_at.isoformat()
        }
    
    # ==================== INTERVIEW SCHEDULING ====================
    
    def schedule_interview(
        self,
        candidate_id: str,
        interviewers: List[str],
        scheduled_time: datetime,
        interview_type: str = "technical",
        duration_minutes: int = 60,
        location: Optional[str] = None,
        agenda: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Schedule an interview.
        
        Interview scheduling logic:
        - Respect interviewer and candidate availability
        - Avoid back-to-back overload
        - Include clear interview agenda
        """
        candidate = self.db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            return {"error": "Candidate not found"}
        
        # Count existing interviews to determine round
        existing = self.db.query(Interview).filter(
            Interview.candidate_id == candidate_id
        ).count()
        
        interview = Interview(
            id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            round_number=existing + 1,
            interview_type=interview_type,
            interviewers=json.dumps(interviewers),
            scheduled_time=scheduled_time,
            duration_minutes=duration_minutes,
            location=location,
            agenda=agenda or f"Interview agenda for {candidate.name}"
        )
        self.db.add(interview)
        
        # Update candidate stage if needed
        if candidate.stage == CandidateStage.SCREENING:
            candidate.stage = CandidateStage.INTERVIEWING
        
        self._log_activity(
            f"Interview scheduled: {candidate.name} with {interviewers} on {scheduled_time.date()}"
        )
        
        self.db.commit()
        self.db.refresh(interview)
        
        return {
            "interview_id": interview.id,
            "candidate": candidate.name,
            "round": interview.round_number,
            "type": interview_type,
            "scheduled_time": scheduled_time.isoformat(),
            "interviewers": interviewers,
            "duration_minutes": duration_minutes
        }
    
    def record_interview_feedback(
        self,
        interview_id: str,
        feedback: List[Dict[str, str]],
        strengths: List[str],
        concerns: List[str],
        recommendation: str
    ) -> Dict[str, Any]:
        """
        Record and summarize interview feedback.
        
        Feedback summaries must:
        - Combine inputs from all interviewers
        - Highlight strengths and concerns
        - Avoid subjective or biased language
        - Clearly separate facts from opinions
        """
        interview = self.db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            return {"error": "Interview not found"}
        
        interview.feedback = json.dumps(feedback)
        interview.strengths = json.dumps(strengths)
        interview.concerns = json.dumps(concerns)
        interview.recommendation = recommendation
        interview.status = InterviewStatus.COMPLETED
        
        # Generate summary
        summary_parts = []
        summary_parts.append(f"**Interview Round {interview.round_number}: {interview.interview_type}**")
        summary_parts.append(f"\n**Interviewers:** {', '.join(json.loads(interview.interviewers))}")
        
        if strengths:
            summary_parts.append("\n**Strengths (observed):**")
            for s in strengths:
                summary_parts.append(f"- {s}")
        
        if concerns:
            summary_parts.append("\n**Concerns (observed):**")
            for c in concerns:
                summary_parts.append(f"- {c}")
        
        summary_parts.append(f"\n**Recommendation:** {recommendation.replace('_', ' ').title()}")
        
        interview.feedback_summary = "\n".join(summary_parts)
        
        self._log_activity(
            f"Interview feedback recorded for candidate {interview.candidate_id}"
        )
        
        self.db.commit()
        
        return {
            "interview_id": interview_id,
            "status": "completed",
            "recommendation": recommendation,
            "feedback_summary": interview.feedback_summary,
            "note": "This is a factual summary. Final hiring decisions require human approval."
        }
    
    # ==================== ONBOARDING ====================
    
    def generate_onboarding_plan(
        self,
        employee_id: str,
        role: str,
        start_date: datetime,
        buddy_name: Optional[str] = None,
        mentor_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a 30-60-90 day onboarding plan.
        
        Onboarding plans should:
        - Be role-specific
        - Cover first 30–60–90 days
        - Include learning, setup, and delivery goals
        """
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return {"error": "Employee not found"}
        
        # Generate role-appropriate goals
        goals_30 = [
            "Complete all account and tool setup",
            "Review core documentation and processes",
            "Meet with team members and key stakeholders",
            "Understand team goals and current projects",
            "Complete initial training modules"
        ]
        
        goals_60 = [
            "Take ownership of first project or task area",
            "Contribute to team discussions and planning",
            "Build relationships across teams",
            "Identify process improvements",
            "Complete role-specific certifications if required"
        ]
        
        goals_90 = [
            "Deliver measurable impact in primary responsibility",
            "Mentor or support newer team members",
            "Propose and implement at least one improvement",
            "Establish regular feedback loop with manager",
            "Set goals for next quarter"
        ]
        
        plan = OnboardingPlan(
            id=str(uuid.uuid4()),
            employee_id=employee_id,
            role=role,
            start_date=start_date,
            goals_30_days=json.dumps(goals_30),
            goals_60_days=json.dumps(goals_60),
            goals_90_days=json.dumps(goals_90),
            buddy_name=buddy_name,
            mentor_name=mentor_name
        )
        self.db.add(plan)
        
        self._log_activity(f"Generated onboarding plan for {employee.name}")
        
        self.db.commit()
        self.db.refresh(plan)
        
        return {
            "plan_id": plan.id,
            "employee": employee.name,
            "role": role,
            "start_date": start_date.isoformat(),
            "goals_30_days": goals_30,
            "goals_60_days": goals_60,
            "goals_90_days": goals_90,
            "buddy": buddy_name,
            "mentor": mentor_name,
            "next_step": "Assign onboarding tasks"
        }
    
    def assign_onboarding_tasks(self, plan_id: str) -> Dict[str, Any]:
        """
        Assign standard onboarding tasks.
        
        Tasks include: account setup, tool access, documentation review, initial assignments.
        Tasks must be tracked like standard project tasks.
        """
        plan = self.db.query(OnboardingPlan).filter(OnboardingPlan.id == plan_id).first()
        if not plan:
            return {"error": "Onboarding plan not found"}
        
        standard_tasks = [
            # Day 1-3: Account setup
            {"title": "Complete HR paperwork", "category": "account_setup", "day_due": 1},
            {"title": "Set up email and calendar", "category": "account_setup", "day_due": 1},
            {"title": "Get access to communication tools (Slack, Teams)", "category": "tool_access", "day_due": 1},
            {"title": "Set up development environment", "category": "tool_access", "day_due": 2},
            {"title": "Request access to required systems", "category": "tool_access", "day_due": 2},
            
            # Day 3-7: Documentation review
            {"title": "Review company handbook", "category": "documentation", "day_due": 3},
            {"title": "Read team documentation and processes", "category": "documentation", "day_due": 5},
            {"title": "Review current project documentation", "category": "documentation", "day_due": 7},
            
            # Week 2: Initial assignments
            {"title": "Complete introductory training", "category": "assignment", "day_due": 10},
            {"title": "Shadow team member on project work", "category": "assignment", "day_due": 12},
            {"title": "Take on first small task", "category": "assignment", "day_due": 14},
            
            # Week 3-4: Integration
            {"title": "Schedule 1:1s with key stakeholders", "category": "assignment", "day_due": 21},
            {"title": "Present at team meeting", "category": "assignment", "day_due": 28},
            {"title": "Complete 30-day check-in with manager", "category": "assignment", "day_due": 30}
        ]
        
        created_tasks = []
        for task_data in standard_tasks:
            task = OnboardingTask(
                id=str(uuid.uuid4()),
                plan_id=plan_id,
                title=task_data["title"],
                category=task_data["category"],
                day_due=task_data["day_due"]
            )
            self.db.add(task)
            created_tasks.append(task_data)
        
        plan.status = OnboardingStatus.IN_PROGRESS
        
        self._log_activity(f"Assigned {len(created_tasks)} onboarding tasks for plan {plan_id}")
        
        self.db.commit()
        
        return {
            "plan_id": plan_id,
            "tasks_created": len(created_tasks),
            "tasks": created_tasks
        }
    
    def get_onboarding_progress(self, plan_id: str) -> Dict[str, Any]:
        """Get onboarding progress for an employee."""
        plan = self.db.query(OnboardingPlan).filter(OnboardingPlan.id == plan_id).first()
        if not plan:
            return {"error": "Onboarding plan not found"}
        
        tasks = self.db.query(OnboardingTask).filter(OnboardingTask.plan_id == plan_id).all()
        
        completed = sum(1 for t in tasks if t.is_completed)
        total = len(tasks)
        
        by_category = {}
        for task in tasks:
            if task.category not in by_category:
                by_category[task.category] = {"total": 0, "completed": 0}
            by_category[task.category]["total"] += 1
            if task.is_completed:
                by_category[task.category]["completed"] += 1
        
        plan.completion_percentage = int((completed / total * 100) if total > 0 else 0)
        self.db.commit()
        
        return {
            "plan_id": plan_id,
            "role": plan.role,
            "start_date": plan.start_date.isoformat(),
            "status": plan.status.value,
            "completion_percentage": plan.completion_percentage,
            "tasks_completed": completed,
            "tasks_total": total,
            "by_category": by_category,
            "goals_30_days": json.loads(plan.goals_30_days or "[]"),
            "goals_60_days": json.loads(plan.goals_60_days or "[]"),
            "goals_90_days": json.loads(plan.goals_90_days or "[]")
        }
    
    # ==================== KNOWLEDGE BASE ====================
    
    def add_knowledge_article(
        self,
        title: str,
        content: str,
        category: str,
        author: str,
        tags: Optional[List[str]] = None,
        target_roles: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Add a new knowledge base article."""
        # Generate summary (first 200 chars)
        summary = content[:200] + "..." if len(content) > 200 else content
        
        article = KnowledgeArticle(
            id=str(uuid.uuid4()),
            title=title,
            content=content,
            summary=summary,
            category=category,
            tags=json.dumps(tags or []),
            author=author,
            target_roles=json.dumps(target_roles or []),
            status=ArticleStatus.DRAFT
        )
        self.db.add(article)
        
        self._log_activity(f"Knowledge article created: {title}")
        
        self.db.commit()
        self.db.refresh(article)
        
        return {
            "article_id": article.id,
            "title": title,
            "category": category,
            "status": "draft",
            "next_step": "Review and publish"
        }
    
    def search_knowledge_base(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search the knowledge base.
        
        Behavior: Answer based on internal knowledge base, cite sources when possible.
        """
        db_query = self.db.query(KnowledgeArticle).filter(
            KnowledgeArticle.status == ArticleStatus.PUBLISHED
        )
        
        if category:
            db_query = db_query.filter(KnowledgeArticle.category == category)
        
        # Simple keyword search
        db_query = db_query.filter(
            KnowledgeArticle.title.ilike(f"%{query}%") | 
            KnowledgeArticle.content.ilike(f"%{query}%")
        )
        
        articles = db_query.limit(limit).all()
        
        # Update view counts
        for article in articles:
            article.view_count += 1
        self.db.commit()
        
        return [{
            "id": a.id,
            "title": a.title,
            "summary": a.summary,
            "category": a.category,
            "author": a.author,
            "tags": json.loads(a.tags or "[]"),
            "is_outdated": a.is_outdated
        } for a in articles]
    
    def flag_outdated_article(
        self,
        article_id: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Flag an article as outdated.
        
        Knowledge base management: Flag outdated documentation.
        """
        article = self.db.query(KnowledgeArticle).filter(
            KnowledgeArticle.id == article_id
        ).first()
        if not article:
            return {"error": "Article not found"}
        
        article.is_outdated = True
        article.outdated_reason = reason
        
        self._log_activity(f"Article flagged as outdated: {article.title}")
        
        self.db.commit()
        
        return {
            "article_id": article_id,
            "title": article.title,
            "is_outdated": True,
            "reason": reason
        }
    
    def get_role_documentation(
        self,
        role: str
    ) -> List[Dict[str, Any]]:
        """
        Get curated documentation for a specific role.
        
        Behavior:
        - Curate relevant documents
        - Avoid overwhelming new hires
        """
        articles = self.db.query(KnowledgeArticle).filter(
            KnowledgeArticle.status == ArticleStatus.PUBLISHED,
            KnowledgeArticle.is_outdated == False,
            KnowledgeArticle.target_roles.ilike(f"%{role}%")
        ).limit(10).all()
        
        return [{
            "id": a.id,
            "title": a.title,
            "summary": a.summary,
            "category": a.category
        } for a in articles]
    
    # ==================== ACTIVITY LOGGING ====================
    
    def _log_activity(self, message: str):
        """Log growth & scaling activity."""
        activity = AgentActivity(
            id=str(uuid.uuid4()),
            agent_name="GrowthScalingAgent",
            activity_type="action",
            message=message
        )
        self.db.add(activity)

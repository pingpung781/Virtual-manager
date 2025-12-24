"""
Enhanced Agent Orchestrator using LangGraph.

Implements multi-agent coordination for:
- Managerial Intelligence
- Planning
- Execution Monitoring
- People Operations
- Communication
"""

from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
import json
from backend.app.core.logging import logger


class AgentState(TypedDict):
    """State shared across all agents in the orchestration."""
    messages: List[str]
    current_agent: str
    next_step: str
    context: Dict[str, Any]
    result: Optional[Dict[str, Any]]


class AgentOrchestrator:
    """
    Central orchestrator for all VAM agents.
    Routes requests to appropriate agents based on intent.
    """
    
    INTENT_KEYWORDS = {
        "planning": ["plan", "decompose", "breakdown", "schedule", "timeline", "milestone"],
        "execution": ["status", "update", "progress", "blocked", "blocker", "overdue"],
        "people_ops": ["leave", "vacation", "workload", "assign", "reassign", "capacity"],
        "communication": ["standup", "report", "remind", "summary", "meeting"],
        "managerial": ["risk", "goal", "strategy", "analyze", "decision", "trade-off"]
    }
    
    def __init__(self):
        self.graph = self._build_graph()
    
    def _detect_intent(self, message: str) -> str:
        """Detect intent from message content."""
        message_lower = message.lower()
        
        for intent, keywords in self.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return intent
        
        return "managerial"  # Default to managerial agent
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        builder = StateGraph(AgentState)
        
        # Add nodes
        builder.add_node("router", self._router_node)
        builder.add_node("managerial_agent", self._managerial_node)
        builder.add_node("planning_agent", self._planning_node)
        builder.add_node("execution_agent", self._execution_node)
        builder.add_node("people_ops_agent", self._people_ops_node)
        builder.add_node("communication_agent", self._communication_node)
        
        # Set entry point
        builder.set_entry_point("router")
        
        # Add conditional edges from router
        builder.add_conditional_edges(
            "router",
            lambda x: x["next_step"],
            {
                "managerial_agent": "managerial_agent",
                "planning_agent": "planning_agent",
                "execution_agent": "execution_agent",
                "people_ops_agent": "people_ops_agent",
                "communication_agent": "communication_agent",
                END: END
            }
        )
        
        # All agents return to END
        builder.add_edge("managerial_agent", END)
        builder.add_edge("planning_agent", END)
        builder.add_edge("execution_agent", END)
        builder.add_edge("people_ops_agent", END)
        builder.add_edge("communication_agent", END)
        
        return builder.compile()
    
    def _router_node(self, state: AgentState) -> AgentState:
        """Route to appropriate agent based on message intent."""
        logger.info(f"Router processing state")
        
        last_message = state["messages"][-1] if state["messages"] else ""
        intent = self._detect_intent(last_message)
        
        agent_map = {
            "managerial": "managerial_agent",
            "planning": "planning_agent",
            "execution": "execution_agent",
            "people_ops": "people_ops_agent",
            "communication": "communication_agent"
        }
        
        next_agent = agent_map.get(intent, "managerial_agent")
        
        logger.info(f"Detected intent: {intent} -> Routing to: {next_agent}")
        
        return {
            **state,
            "current_agent": intent,
            "next_step": next_agent
        }
    
    def _managerial_node(self, state: AgentState) -> AgentState:
        """Handle managerial intelligence requests."""
        logger.info("Managerial Agent processing")
        
        from backend.app.agents.managerial import managerial_agent
        
        last_message = state["messages"][-1] if state["messages"] else ""
        context = state.get("context", {})
        
        result = {}
        message_lower = last_message.lower()
        
        if "risk" in message_lower:
            tasks = context.get("tasks", [])
            goals = context.get("goals", [])
            result = managerial_agent.analyze_risks(tasks, goals)
        elif "goal" in message_lower:
            raw_text = context.get("goal_text", last_message)
            result = managerial_agent.refine_goal(raw_text)
        else:
            # Default: stakeholder query
            result = managerial_agent.answer_stakeholder_query(
                last_message,
                json.dumps(context)
            )
        
        return {
            **state,
            "messages": state["messages"] + [f"Managerial Agent: Processed {last_message[:50]}..."],
            "result": result if isinstance(result, dict) else result.__dict__
        }
    
    def _planning_node(self, state: AgentState) -> AgentState:
        """Handle planning requests."""
        logger.info("Planning Agent processing")
        
        from backend.app.agents.planning import planning_agent
        
        last_message = state["messages"][-1] if state["messages"] else ""
        context = state.get("context", {})
        
        result = {}
        message_lower = last_message.lower()
        
        if "decompose" in message_lower or "breakdown" in message_lower:
            goal_text = context.get("goal_text", last_message)
            result = planning_agent.decompose_goal(goal_text, context.get("constraints"))
        elif "timeline" in message_lower:
            tasks = context.get("tasks", [])
            result = planning_agent.suggest_timeline(tasks)
        elif "validate" in message_lower:
            tasks = context.get("tasks", [])
            deadline = context.get("deadline")
            result = planning_agent.validate_plan(tasks, deadline)
        else:
            # Default: goal decomposition
            result = planning_agent.decompose_goal(last_message)
        
        return {
            **state,
            "messages": state["messages"] + [f"Planning Agent: Created plan for {last_message[:50]}..."],
            "result": result
        }
    
    def _execution_node(self, state: AgentState) -> AgentState:
        """Handle execution monitoring requests."""
        logger.info("Execution Agent processing")
        
        # Note: ExecutionAgent requires DB session
        # This is a simplified version for orchestration
        
        last_message = state["messages"][-1] if state["messages"] else ""
        
        result = {
            "status": "processed",
            "message": f"Execution monitoring request received: {last_message[:100]}",
            "note": "Full execution requires database session - use API endpoints directly"
        }
        
        return {
            **state,
            "messages": state["messages"] + ["Execution Agent: Monitoring request processed"],
            "result": result
        }
    
    def _people_ops_node(self, state: AgentState) -> AgentState:
        """Handle people/resource operations."""
        logger.info("People Ops Agent processing")
        
        # Note: PeopleOpsAgent requires DB session
        
        last_message = state["messages"][-1] if state["messages"] else ""
        context = state.get("context", {})
        
        result = {
            "status": "processed",
            "message": f"People ops request received: {last_message[:100]}",
            "note": "Full people ops requires database session - use API endpoints directly"
        }
        
        return {
            **state,
            "messages": state["messages"] + ["People Ops Agent: Request processed"],
            "result": result
        }
    
    def _communication_node(self, state: AgentState) -> AgentState:
        """Handle communication generation requests."""
        logger.info("Communication Agent processing")
        
        from backend.app.agents.communication import communication_agent
        
        last_message = state["messages"][-1] if state["messages"] else ""
        context = state.get("context", {})
        
        result = {}
        message_lower = last_message.lower()
        
        if "standup" in message_lower:
            completed = context.get("completed", [])
            planned = context.get("planned", [])
            blockers = context.get("blockers", [])
            result = communication_agent.generate_standup("Team", completed, planned, blockers)
        elif "report" in message_lower:
            project_data = context.get("project_data", {})
            audience = context.get("audience", "team")
            result = communication_agent.generate_progress_report("weekly", audience, project_data)
        elif "remind" in message_lower:
            recipient = context.get("recipient", "team")
            topic = context.get("topic", last_message)
            result = communication_agent.generate_reminder(recipient, topic, last_message)
        elif "meeting" in message_lower:
            transcript = context.get("transcript", last_message)
            result = communication_agent.summarize_meeting(transcript)
        else:
            result = {"message": f"Communication request processed: {last_message[:100]}"}
        
        return {
            **state,
            "messages": state["messages"] + ["Communication Agent: Generated content"],
            "result": result
        }
    
    def process(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a message through the orchestrator.
        
        Args:
            message: User message/request
            context: Additional context (tasks, goals, etc.)
        
        Returns:
            Processing result from the appropriate agent
        """
        initial_state: AgentState = {
            "messages": [message],
            "current_agent": "",
            "next_step": "",
            "context": context or {},
            "result": None
        }
        
        try:
            final_state = self.graph.invoke(initial_state)
            return {
                "success": True,
                "agent": final_state.get("current_agent"),
                "result": final_state.get("result"),
                "messages": final_state.get("messages")
            }
        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Singleton orchestrator instance
orchestrator = AgentOrchestrator()

# Legacy compatibility - expose the compiled graph
orchestrator_graph = orchestrator.graph

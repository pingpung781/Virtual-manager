from typing import TypedDict, Annotated, List, Union
from langgraph.graph import StateGraph, END
from app.core.logging import logger

class AgentState(TypedDict):
    messages: List[str]
    current_agent: str
    next_step: str

# Node: Manager Routing Logic
def manager_router(state: AgentState):
    logger.info(f"Manager processing state: {state}")
    # Placeholder logic for routing
    last_message = state["messages"][-1] if state["messages"] else ""
    
    if "plan" in last_message.lower():
        return {"current_agent": "planning", "next_step": "planning_agent"}
    elif "leave" in last_message.lower():
        return {"current_agent": "people_ops", "next_step": "people_ops_agent"}
    else:
        return {"current_agent": "manager", "next_step": END}

# Node: Planning Agent Stub
def planning_agent_node(state: AgentState):
    logger.info("Delegating to Planning Agent")
    return {"messages": state["messages"] + ["Planning Agent: Goals decomposed."]}

# Node: People Ops Agent Stub
def people_ops_agent_node(state: AgentState):
    logger.info("Delegating to People Ops Agent")
    return {"messages": state["messages"] + ["People Ops Agent: Leave processed."]}

# Build Graph
builder = StateGraph(AgentState)

builder.add_node("manager", manager_router)
builder.add_node("planning_agent", planning_agent_node)
builder.add_node("people_ops_agent", people_ops_agent_node)

builder.set_entry_point("manager")

builder.add_conditional_edges(
    "manager",
    lambda x: x["next_step"],
    {
        "planning_agent": "planning_agent",
        "people_ops_agent": "people_ops_agent",
        END: END
    }
)
builder.add_edge("planning_agent", END)
builder.add_edge("people_ops_agent", END)

orchestrator_graph = builder.compile()

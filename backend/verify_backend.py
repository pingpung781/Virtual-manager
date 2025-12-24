import sys
import os
sys.path.append(os.getcwd())

from app.agents.orchestrator import orchestrator_graph

def test_leave_approval():
    print("Testing Leave Approval Flow...")
    initial_state = {"messages": ["Approve leave for Ashish tomorrow"], "current_agent": "manager", "next_step": ""}
    
    # Run the graph
    result = orchestrator_graph.invoke(initial_state)
    
    print("\nXXX Result State XXX")
    print(result)
    
    # Check if it routed to people ops
    if "People Ops Agent: Leave processed." in result["messages"]:
         print("\nSUCCESS: Routed to People Ops Agent correctly.")
    else:
         print("\nFAILURE: Did not route correctly.")

if __name__ == "__main__":
    test_leave_approval()

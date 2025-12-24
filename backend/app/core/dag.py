from typing import List, Dict, Set, Optional, Tuple
from backend.app.models import Task, TaskStatus

class DAGManager:
    """
    Implements the 'Task Dependency Graphs (DAGs)' requirement from the 
    Task, Project & Execution Prompt Spec.
    Ensures no circular dependencies and calculates blockage.
    """

    @staticmethod
    def build_graph(tasks: List[Task]) -> Dict[str, List[str]]:
        """
        Builds an adjacency list representation of the task graph.
        Key: Task ID, Value: List of Dependency Task IDs (Prerequisites)
        """
        graph = {}
        for task in tasks:
            # task.dependencies is a list of TaskDependency objects
            # We want the IDs of the tasks that 'task' depends on
            deps = [d.depends_on_id for d in task.dependencies] if task.dependencies else []
            graph[task.id] = deps
        return graph

    @staticmethod
    def detect_cycles(tasks: List[Task], new_dependency: Optional[Tuple[str, str]] = None) -> bool:
        """
        Detects if a cycle exists in the task graph.
        Optionally checks a hypothetical new dependency (task_id, dependency_id).
        Returns True if a cycle is detected.
        """
        graph = DAGManager.build_graph(tasks)
        
        if new_dependency:
            task_id, dep_id = new_dependency
            if task_id not in graph:
                graph[task_id] = []
            graph[task_id].append(dep_id)

        visited = set()
        recursion_stack = set()

        def dfs(node):
            visited.add(node)
            recursion_stack.add(node)

            # Get dependencies for this node
            neighbors = graph.get(node, [])
            
            for neighbor in neighbors:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in recursion_stack:
                    return True

            recursion_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                if dfs(node):
                    return True
        
        return False

    @staticmethod
    def get_blocked_tasks(tasks: List[Task]) -> Set[str]:
        """
        Identifies tasks that are 'blocked' because their dependencies are not 'done'.
        Returns a set of Blocked Task IDs.
        """
        # Create a lookup for task status
        task_status_map = {t.id: t.status for t in tasks}
        blocked_ids = set()

        for task in tasks:
            # Skip if task is already completed
            if task.status == TaskStatus.COMPLETED:
                continue
            
            deps = [d.depends_on_id for d in task.dependencies] if task.dependencies else []
            for dep_id in deps:
                # If dependency is missing (deleted) or not done, the task is blocked
                dep_status = task_status_map.get(dep_id)
                if not dep_status or dep_status != TaskStatus.COMPLETED:
                    blocked_ids.add(task.id)
                    break
        
        return blocked_ids

    @staticmethod
    def topological_sort(tasks: List[Task]) -> List[str]:
        """
        Returns a valid execution order for tasks.
        If A depends on B, B comes before A in the list.
        """
        graph = DAGManager.build_graph(tasks)
        visited = set()
        stack = []

        def dfs(node):
            visited.add(node)
            neighbors = graph.get(node, [])
            for neighbor in neighbors:
                if neighbor not in visited:
                    dfs(neighbor)
            stack.append(node)

        for node in graph:
            if node not in visited:
                dfs(node)
        
        # The stack build order: leaf nodes (dependencies) are pushed first, then nodes relying on them.
        # But wait:
        # A -> B (A depends on B).
        # DFS(A) -> DFS(B). B finishes first -> Stack: [B]. Then A finishes -> Stack: [B, A].
        # We want B to execute first. B is at index 0.
        # So we just return the stack as is.
        return stack
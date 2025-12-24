"""
Routers package initialization.
Exports all API routers for the Virtual AI Manager.
"""

from backend.app.routers import managerial
from backend.app.routers import goals
from backend.app.routers import milestones
from backend.app.routers import execution

__all__ = ["managerial", "goals", "milestones", "execution"]

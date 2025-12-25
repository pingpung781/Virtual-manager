"""
People Service - CRUD operations for people management.

Handles:
- Leave request lifecycle
- Calendar synchronization
- Profile management
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.models import (
    Employee, LeaveRequest, LeaveStatus, CalendarEvent, EventType
)


def request_leave(
    db: Session,
    user_id: str,
    start_date: datetime,
    end_date: datetime,
    leave_type: str,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new leave request."""
    employee = db.query(Employee).filter(Employee.id == user_id).first()
    if not employee:
        return {"success": False, "error": "Employee not found"}
    
    # Calculate days
    days_requested = (end_date - start_date).days + 1
    
    # Check leave balance for vacation
    if leave_type == "vacation" and days_requested > employee.leave_balance:
        return {
            "success": False,
            "error": f"Insufficient leave balance. Available: {employee.leave_balance} days"
        }
    
    leave = LeaveRequest(
        id=str(uuid.uuid4()),
        employee_id=user_id,
        start_date=start_date,
        end_date=end_date,
        leave_type=leave_type,
        days_requested=days_requested,
        reason=reason,
        status=LeaveStatus.PENDING
    )
    
    db.add(leave)
    db.commit()
    
    return {
        "success": True,
        "leave_id": leave.id,
        "status": "pending",
        "days_requested": days_requested
    }


def sync_calendar(
    db: Session,
    user_id: str,
    events: List[Dict[str, Any]],
    source: str = "google"
) -> Dict[str, Any]:
    """
    Sync external calendar events.
    
    Connects via MCP to external calendar (Google/Outlook)
    and upserts CalendarEvent rows.
    """
    employee = db.query(Employee).filter(Employee.id == user_id).first()
    if not employee:
        return {"success": False, "error": "Employee not found"}
    
    synced = 0
    updated = 0
    
    for event_data in events:
        external_id = event_data.get("external_id")
        
        # Check if event exists
        existing = None
        if external_id:
            existing = db.query(CalendarEvent).filter(
                CalendarEvent.external_id == external_id
            ).first()
        
        if existing:
            # Update existing
            existing.title = event_data.get("title", existing.title)
            existing.start_time = event_data.get("start_time", existing.start_time)
            existing.end_time = event_data.get("end_time", existing.end_time)
            existing.updated_at = datetime.utcnow()
            updated += 1
        else:
            # Create new
            event_type_str = event_data.get("event_type", "meeting")
            try:
                event_type = EventType(event_type_str)
            except:
                event_type = EventType.MEETING
                
            event = CalendarEvent(
                id=str(uuid.uuid4()),
                user_id=user_id,
                title=event_data.get("title", "Untitled"),
                start_time=event_data.get("start_time"),
                end_time=event_data.get("end_time"),
                external_id=external_id,
                event_type=event_type,
                source=source
            )
            db.add(event)
            synced += 1
    
    db.commit()
    
    return {
        "success": True,
        "synced": synced,
        "updated": updated,
        "source": source
    }


def get_user_calendar_events(
    db: Session,
    user_id: str,
    start_date: datetime,
    end_date: datetime
) -> List[Dict[str, Any]]:
    """Get all calendar events for a user in a date range."""
    events = db.query(CalendarEvent).filter(
        CalendarEvent.user_id == user_id,
        CalendarEvent.start_time >= start_date,
        CalendarEvent.end_time <= end_date
    ).all()
    
    return [{
        "id": e.id,
        "title": e.title,
        "start_time": e.start_time.isoformat(),
        "end_time": e.end_time.isoformat(),
        "event_type": e.event_type.value,
        "source": e.source
    } for e in events]

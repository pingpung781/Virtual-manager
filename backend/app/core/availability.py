"""
Availability Calculator - Core module for capacity planning.

Calculates true available capacity considering:
- Working hours
- Approved leave
- Public holidays
- Calendar events/meetings
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.models import (
    Employee, UserLeave, Holiday, Meeting, CalendarEvent,
    Task, TaskStatus, OverloadStatus
)


def get_working_hours_per_day(employee: Employee) -> float:
    """Calculate daily working hours from employee profile."""
    try:
        start = datetime.strptime(employee.working_hours_start, "%H:%M")
        end = datetime.strptime(employee.working_hours_end, "%H:%M")
        return (end - start).seconds / 3600
    except:
        return 8.0  # Default 8 hours


def get_available_hours(
    db: Session,
    user_id: str,
    start_date: datetime,
    end_date: datetime
) -> Dict[str, Any]:
    """
    Calculate net available hours for a user in a date range.
    
    Formula:
    1. Start: Total working hours in range
    2. Subtract: Approved leave days
    3. Subtract: Public holidays
    4. Subtract: Existing calendar meetings
    5. Result: Net hours available for tasks
    """
    employee = db.query(Employee).filter(Employee.id == user_id).first()
    if not employee:
        return {"error": "Employee not found", "available_hours": 0}
    
    hours_per_day = get_working_hours_per_day(employee)
    
    # Calculate total working days (exclude weekends)
    total_days = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # Monday-Friday
            total_days += 1
        current += timedelta(days=1)
    
    total_working_hours = total_days * hours_per_day
    
    # Subtract approved leave
    leaves = db.query(UserLeave).filter(
        UserLeave.user == employee.name,
        UserLeave.status == "approved",
        UserLeave.start_date <= end_date,
        UserLeave.end_date >= start_date
    ).all()
    
    leave_hours = 0
    for leave in leaves:
        leave_start = max(leave.start_date, start_date)
        leave_end = min(leave.end_date, end_date)
        leave_days = (leave_end - leave_start).days + 1
        leave_hours += leave_days * hours_per_day
    
    # Subtract public holidays
    holidays = db.query(Holiday).filter(
        Holiday.date >= start_date,
        Holiday.date <= end_date
    ).all()
    holiday_hours = len(holidays) * hours_per_day
    
    # Subtract meeting hours from Meeting model
    meeting_hours = 0.0
    try:
        meetings = db.query(Meeting).filter(
            Meeting.start_time >= start_date,
            Meeting.end_time <= end_date
        ).all()
        
        for meeting in meetings:
            # Check if employee is a participant
            if employee in meeting.participants:
                meeting_hours += (meeting.end_time - meeting.start_time).seconds / 3600
    except:
        pass  # Meeting model might not have participants relationship set up
    
    # Subtract calendar events
    calendar_hours = 0.0
    try:
        events = db.query(CalendarEvent).filter(
            CalendarEvent.user_id == user_id,
            CalendarEvent.start_time >= start_date,
            CalendarEvent.end_time <= end_date
        ).all()
        
        for event in events:
            if not event.is_all_day:
                calendar_hours += (event.end_time - event.start_time).seconds / 3600
            else:
                calendar_hours += hours_per_day
    except:
        pass  # CalendarEvent might not exist yet
    
    total_blocked = leave_hours + holiday_hours + meeting_hours + calendar_hours
    
    # Calculate net available
    net_available = max(0, total_working_hours - total_blocked)
    
    return {
        "user_id": user_id,
        "user_name": employee.name,
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "breakdown": {
            "total_working_hours": round(total_working_hours, 1),
            "leave_hours": round(leave_hours, 1),
            "holiday_hours": round(holiday_hours, 1),
            "meeting_hours": round(meeting_hours + calendar_hours, 1)
        },
        "available_hours": round(net_available, 1),
        "utilization_percentage": round(
            (total_blocked / total_working_hours) * 100, 1
        ) if total_working_hours > 0 else 0
    }


def check_overload(db: Session, user_id: str) -> Dict[str, Any]:
    """
    Check workload status for a user.
    
    Returns OverloadStatus:
    - LOW: < 60% capacity utilized
    - BALANCED: 60-90% capacity
    - OVERLOADED: > 90% capacity
    """
    employee = db.query(Employee).filter(Employee.id == user_id).first()
    if not employee:
        return {"error": "Employee not found", "status": None}
    
    # Get current week dates
    today = datetime.utcnow()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=4)  # Mon-Fri
    
    # Get available hours
    availability = get_available_hours(db, user_id, week_start, week_end)
    available = availability.get("available_hours", 0)
    
    # Get assigned task hours
    tasks = db.query(Task).filter(
        Task.owner == employee.name,
        Task.status.in_([TaskStatus.IN_PROGRESS, TaskStatus.NOT_STARTED])
    ).all()
    
    assigned_hours = sum(t.estimated_hours or 4 for t in tasks)
    
    # Calculate utilization
    weekly_capacity = employee.weekly_capacity_hours or 40
    utilization = (assigned_hours / available * 100) if available > 0 else 100
    
    if utilization < 60:
        status = OverloadStatus.LOW
        recommendation = "Capacity available for additional tasks"
    elif utilization <= 90:
        status = OverloadStatus.BALANCED
        recommendation = "Workload is healthy"
    else:
        status = OverloadStatus.OVERLOADED
        recommendation = "Consider redistributing tasks or extending deadlines"
    
    return {
        "user_id": user_id,
        "user_name": employee.name,
        "status": status.value,
        "metrics": {
            "weekly_capacity": weekly_capacity,
            "available_hours": available,
            "assigned_hours": assigned_hours,
            "utilization_percentage": round(utilization, 1)
        },
        "task_count": len(tasks),
        "recommendation": recommendation
    }

"""
Scheduler - Daily snapshot and automation tasks.

Provides APScheduler-based background jobs for:
- Daily project snapshots
- Automation rule evaluation
"""

from datetime import datetime
from typing import Optional


def daily_snapshot_job():
    """Take snapshots of all active projects at midnight."""
    from backend.app.core.database import SessionLocal
    from backend.app.core.analytics import take_project_snapshot
    from backend.app.models import Project
    
    db = SessionLocal()
    try:
        projects = db.query(Project).all()
        for project in projects:
            take_project_snapshot(db, project.id)
        print(f"[Scheduler] Captured snapshots for {len(projects)} projects at {datetime.utcnow()}")
    except Exception as e:
        print(f"[Scheduler] Error taking snapshots: {e}")
    finally:
        db.close()


def start_scheduler():
    """
    Start the background scheduler.
    
    Note: Requires APScheduler to be installed.
    Install with: pip install apscheduler
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        
        scheduler = BackgroundScheduler()
        
        # Daily at midnight
        scheduler.add_job(
            daily_snapshot_job,
            CronTrigger(hour=0, minute=0),
            id='daily_snapshot',
            name='Daily Project Snapshots',
            replace_existing=True
        )
        
        scheduler.start()
        print("[Scheduler] Started background scheduler")
        return scheduler
    except ImportError:
        print("[Scheduler] APScheduler not installed. Run: pip install apscheduler")
        return None


def run_snapshot_now():
    """Manually trigger snapshot job (for testing)."""
    daily_snapshot_job()
    return {"status": "completed", "timestamp": datetime.utcnow().isoformat()}

from app.core.logging import logger

def check_leave_policy(employee_id: str, date: str) -> bool:
    logger.info(f"Checking leave policy for {employee_id} on {date}")
    return True

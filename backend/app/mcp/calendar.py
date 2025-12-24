from app.core.logging import logger

def list_events(day: str):
    logger.info(f"Listing events for {day}")
    return ["Daily Standup at 10:00 AM", "Client Review at 2:00 PM"]

def add_event(title: str, time: str):
    logger.info(f"Adding event: {title} at {time}")
    return "Event Created"

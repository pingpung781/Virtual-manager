from app.core.logging import logger

def send_notification(user_id: str, message: str):
    logger.info(f"Sending notification to {user_id}: {message}")
    # Placeholder: Integration with Slack/Email via MCP
    pass

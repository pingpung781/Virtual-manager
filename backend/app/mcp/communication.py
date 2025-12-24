from app.core.logging import logger

def send_email(to: str, subject: str, body: str):
    logger.info(f"Sending email to {to}: {subject}")
    return "Email Sent"

def send_slack_message(channel: str, message: str):
    logger.info(f"Sending slack message to {channel}: {message}")
    return "Message Sent"

"""
Telegram messaging utilities and helpers.
"""
import logging
from typing import Optional
from telegram.ext import ContextTypes

from config.config_manager import load_config

logger = logging.getLogger(__name__)

async def send_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, 
                      reply_markup=None, allow_sending=True, message_thread_id: Optional[int]=None):
    """
    Sends a message to the specified chat_id, or to primary_chat_id (with thread) if group_mode is enabled.
    """
    if not allow_sending:
        logger.debug(f"Skipped sending message to chat {chat_id}: sending not allowed")
        return

    config = load_config()
    if config["group_mode"] and config["primary_chat_id"]["chat_id"] is not None:
        chat_id = config["primary_chat_id"]["chat_id"]
        message_thread_id = config["primary_chat_id"]["message_thread_id"]
        logger.info(f"Group mode enabled, redirecting message to primary_chat_id: {chat_id}, thread: {message_thread_id}")
    try:
        kwargs = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": reply_markup
        }
        if message_thread_id is not None:
            kwargs["message_thread_id"] = message_thread_id
        await context.bot.send_message(**kwargs)
    except Exception as e:
        logger.error(f"Failed to send message to chat {chat_id}, thread {message_thread_id}: {e}")

def interpret_status(code: int) -> str:
    """Interpret Overseerr status codes into human-readable text."""
    status_map = {
        1: "Unknown",
        2: "Pending",
        3: "Processing", 
        4: "Partially Available",
        5: "Available"
    }
    return status_map.get(code, f"Status {code}")

def can_request_resolution(code: int) -> bool:
    """Check if a resolution can be requested based on status code."""
    return code in [1, 2]  # Unknown or Pending

def can_request_seasons(media_type: str) -> bool:
    """Check if seasons can be requested for this media type."""
    return media_type == "tv"

def is_reportable(code: int) -> bool:
    """Check if media can be reported based on status code."""
    return code in [4, 5]  # Partially Available or Available

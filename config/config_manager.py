"""
Configuration management utilities for the Overseerr Telegram Bot.
"""
import json
import os
import logging
from datetime import datetime, timezone
from typing import Optional

from .constants import CONFIG_FILE

logger = logging.getLogger(__name__)

def ensure_data_directory():
    """
    Ensures the directory for bot_config.json exists.
    Creates the directory if it doesn't exist.
    """
    directory = os.path.dirname(CONFIG_FILE)
    if directory:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")

def load_config():
    """
    Loads the configuration from data/bot_config.json.
    Returns a dict with default values if the file is missing or invalid.
    """
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            config.setdefault("group_mode", False)
            config.setdefault("primary_chat_id", {"chat_id": None, "message_thread_id": None})
            config["primary_chat_id"].setdefault("chat_id", None)
            config["primary_chat_id"].setdefault("message_thread_id", None)
            config.setdefault("mode", "normal")
            config.setdefault("users", {})
            logger.debug("Loaded configuration successfully")
            return config
    except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
        logger.warning(f"Failed to load {CONFIG_FILE}: {e}. Using defaults.")
        default_config = {
            "group_mode": False,
            "primary_chat_id": {"chat_id": None, "message_thread_id": None},
            "mode": "normal",
            "users": {}
        }
        save_config(default_config)
        return default_config

def save_config(config):
    """
    Saves the configuration to data/bot_config.json.
    Ensures the directory exists before writing.
    """
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        logger.info(f"Configuration saved to {CONFIG_FILE}")
    except (IOError, PermissionError) as e:
        logger.error(f"Failed to save {CONFIG_FILE}: {e}")

def is_command_allowed(chat_id: int, message_thread_id: Optional[int], config: dict, telegram_user_id: int) -> bool:
    """
    Checks if a command is allowed based on Group Mode, chat/thread, and user status.
    Admins can always use commands in private chats, even in Group Mode.
    """
    user_id_str = str(telegram_user_id)
    user = config["users"].get(user_id_str, {})
    is_admin = user.get("is_admin", False)
    is_blocked = user.get("is_blocked", False)

    if is_blocked:
        logger.debug(f"User {telegram_user_id} is blocked, denying command")
        return False

    if is_admin and chat_id > 0:  # Positive chat_id indicates a private chat
        logger.debug(f"Admin {telegram_user_id} in private chat {chat_id}, allowing command")
        return True

    if not config["group_mode"]:
        return True

    primary = config["primary_chat_id"]
    if primary["chat_id"] is None:
        logger.debug(f"Group Mode on, primary_chat_id unset, allowing command in chat {chat_id}")
        return True
    if chat_id != primary["chat_id"]:
        logger.info(f"Ignoring command in chat {chat_id}: Group Mode restricts to primary chat {primary['chat_id']}")
        return False
    if primary["message_thread_id"] is not None and message_thread_id != primary["message_thread_id"]:
        logger.info(f"Ignoring command in thread {message_thread_id}: Group Mode restricts to thread {primary['message_thread_id']}")
        return False
    return True

def user_is_authorized(telegram_user_id: int) -> bool:
    """
    Checks if a Telegram user is authorized based on the config.
    """
    config = load_config()
    user_id_str = str(telegram_user_id)
    user = config["users"].get(user_id_str, {})
    return user.get("is_authorized", False) and not user.get("is_blocked", False)

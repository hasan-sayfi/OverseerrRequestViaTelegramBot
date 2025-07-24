"""
Notification management for Overseerr integration.
"""
import logging
import requests
from typing import Dict, Optional

from ..config.constants import OVERSEERR_API_URL, OVERSEERR_API_KEY, TELEGRAM_TOKEN

logger = logging.getLogger(__name__)

def get_global_telegram_notifications():
    """
    Retrieves the current global Telegram notification settings from Overseerr.
    Returns a dictionary with the settings or None on error.
    """
    try:
        url = f"{OVERSEERR_API_URL}/settings/notifications/telegram"
        headers = {
            "X-Api-Key": OVERSEERR_API_KEY
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        settings = response.json()
        logger.info(f"Current Global Telegram notification settings: {settings}")
        return settings
    except requests.RequestException as e:
        logger.error(f"Error when retrieving Telegram notification settings: {e}")
        return None

async def set_global_telegram_notifications(update, context):
    """
    Activates the global Telegram notifications in Overseerr.
    Returns True if successful, otherwise False.
    """

    bot_info = await context.bot.get_me()
    chat_id = str(update.effective_chat.id)

    payload = {
        "enabled": True,
        "types": 1,  # Disable all notification types (except silent)
        "options": {
            "botUsername": bot_info.username,  # Botname
            "botAPI": TELEGRAM_TOKEN,          # Telegram Token
            "chatId": chat_id,                 # Chat-ID - i guess the admin will use the bot first?
            "sendSilently": True
        }
    }
    try:
        url = f"{OVERSEERR_API_URL}/settings/notifications/telegram"
        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": OVERSEERR_API_KEY
        }
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Global Telegram notifications have been successfully activated.")
        return True
    except requests.RequestException as e:
        logger.error(f"Error when activating global Telegram notifications: {e}")
        if e.response is not None:
            logger.error(f"Response content: {e.response.text}")
        return False

async def enable_global_telegram_notifications(update, context):
    """
    Activates global Telegram notifications
    """
    GLOBAL_TELEGRAM_NOTIFICATION_STATUS = get_global_telegram_notifications()
    if GLOBAL_TELEGRAM_NOTIFICATION_STATUS:
        enabled = GLOBAL_TELEGRAM_NOTIFICATION_STATUS.get("enabled", False)
        if enabled:
            logger.info("Global Telegram notifications are activated.")
        else:
            logger.info("Activate global Telegram notifications...")
            await set_global_telegram_notifications(update, context)
    else:
        logger.error("Could not retrieve Global Telegram notification settings.")

def get_user_notification_settings(overseerr_user_id: int) -> Dict:
    """
    Retrieves the current notification settings for a specific Overseerr user.
    Returns a dictionary with the settings or an empty dict on error.
    """
    try:
        url = f"{OVERSEERR_API_URL}/user/{overseerr_user_id}/settings/notifications"
        headers = {
            "X-Api-Key": OVERSEERR_API_KEY
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        settings = response.json()
        logger.info(f"User {overseerr_user_id} notification settings: {settings}")
        return settings
    except requests.RequestException as e:
        logger.error(f"Error when retrieving notification settings for user {overseerr_user_id}: {e}")
        return {}

def update_telegram_settings_for_user(
    overseerr_user_id: int,
    telegram_enabled: bool,
    telegram_bot_username: str,
    telegram_bot_api: str,
    telegram_chat_id: str,
    telegram_send_silently: bool
) -> bool:
    """
    Updates the Telegram notification settings for a specific Overseerr user.
    Returns True if successful, otherwise False.
    """
    payload = {
        "telegramEnabled": telegram_enabled,
        "telegramBotUsername": telegram_bot_username,
        "telegramBotAPI": telegram_bot_api,
        "telegramChatId": telegram_chat_id,
        "telegramSendSilently": telegram_send_silently
    }

    try:
        url = f"{OVERSEERR_API_URL}/user/{overseerr_user_id}/settings/notifications"
        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": OVERSEERR_API_KEY
        }
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Successfully updated Telegram notification settings for user {overseerr_user_id}.")
        return True
    except requests.RequestException as e:
        logger.error(f"Error when updating Telegram notification settings for user {overseerr_user_id}: {e}")
        if e.response is not None:
            logger.error(f"Response content: {e.response.text}")
        return False

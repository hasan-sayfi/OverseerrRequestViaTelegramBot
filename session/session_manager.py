"""
Session management for different bot modes.
"""
import json
import os
import logging
from typing import Optional

from config.constants import USER_SESSIONS_FILE, SHARED_SESSION_FILE, USER_SELECTION_FILE

logger = logging.getLogger(__name__)

###############################################################################
#                        NORMAL MODE SESSION MANAGEMENT
###############################################################################

def load_user_sessions():
    try:
        with open(USER_SESSIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_user_session(telegram_user_id: int, session_data: dict):
    """Save a user's session data to a JSON file for Normal mode."""
    try:
        # Load existing sessions if file exists
        try:
            with open(USER_SESSIONS_FILE, "r", encoding="utf-8") as f:
                all_sessions = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.info(f"Creating new sessions file: {e}")
            all_sessions = {}
        
        # Update with new session data
        all_sessions[str(telegram_user_id)] = session_data
        
        # Write to file
        with open(USER_SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(all_sessions, f, indent=2)
        logger.info(f"Saved session for Telegram user {telegram_user_id} to {USER_SESSIONS_FILE}")
    except Exception as e:
        logger.error(f"Failed to save session for Telegram user {telegram_user_id}: {e}")
        raise  # Re-raise to catch in caller if needed

def load_user_session(telegram_user_id: int) -> dict | None:
    """Load a user's session data from the JSON file."""
    try:
        with open(USER_SESSIONS_FILE, "r", encoding="utf-8") as f:
            all_sessions = json.load(f)
            return all_sessions.get(str(telegram_user_id))
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def save_user_sessions(sessions):
    with open(USER_SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=2)
    logger.info("Saved user sessions")

def clear_user_session(telegram_user_id: int):
    """Remove a user's session from persistent storage."""
    try:
        # Load all sessions
        try:
            with open(USER_SESSIONS_FILE, "r", encoding="utf-8") as f:
                all_sessions = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.info("No sessions file found, nothing to clear")
            return

        # Remove the specific user's session
        user_id_str = str(telegram_user_id)
        if user_id_str in all_sessions:
            del all_sessions[user_id_str]
            
            # Save back to file
            with open(USER_SESSIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(all_sessions, f, indent=2)
            logger.info(f"Cleared persistent session for user {telegram_user_id}")
        else:
            logger.info(f"No persistent session found for user {telegram_user_id}")
            
    except Exception as e:
        logger.error(f"Error clearing session for user {telegram_user_id}: {e}")

###############################################################################
#                        SHARED MODE SESSION MANAGEMENT
###############################################################################

def load_shared_session():
    try:
        with open(SHARED_SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def save_shared_session(session_data):
    with open(SHARED_SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2)
    logger.info("Saved shared session")

def clear_shared_session():
    """Clear the shared session data."""
    if os.path.exists(SHARED_SESSION_FILE):
        os.remove(SHARED_SESSION_FILE)
        logger.info("Cleared shared session")

###############################################################################
#                        API MODE USER SELECTION MANAGEMENT
###############################################################################

def load_user_selections() -> dict:
    """
    Load a dict from user_selection.json:
    {
      "<telegram_user_id>": {
        "userId": 10,
        "userName": "Some Name"
      },
      ...
    }
    """
    if not os.path.exists(USER_SELECTION_FILE):
        logger.info("No user_selection.json found. Returning empty dictionary.")
        return {}
    try:
        with open(USER_SELECTION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.info(f"Loaded user selections from {USER_SELECTION_FILE}: {data}")
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        logger.warning("user_selection.json not found or invalid. Returning empty dictionary.")
        return {}

def save_user_selection(telegram_user_id: int, user_id: int, user_name: str):
    """
    Store the user's Overseerr selection in user_selection.json:
    {
      "<telegram_user_id>": {
        "userId": 10,
        "userName": "DisplayName"
      }
    }
    """
    data = load_user_selections()
    data[str(telegram_user_id)] = {
        "userId": user_id,
        "userName": user_name
    }
    try:
        with open(USER_SELECTION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        logger.info(f"Saved user selection for Telegram user {telegram_user_id}: (Overseerr user {user_id})")
    except Exception as e:
        logger.error(f"Failed to save user selection: {e}")

def get_saved_user_for_telegram_id(telegram_user_id: int):
    """
    Return (userId, userName) or (None, None) if not found.
    """
    data = load_user_selections()
    entry = data.get(str(telegram_user_id))
    if entry:
        logger.info(f"Found saved user for Telegram user {telegram_user_id}: {entry}")
        return entry["userId"], entry["userName"]
    logger.info(f"No saved user found for Telegram user {telegram_user_id}.")
    return None, None

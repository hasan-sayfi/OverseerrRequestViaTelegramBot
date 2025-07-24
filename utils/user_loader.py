"""
User data loading and management utilities.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from ..config.constants import CURRENT_MODE, BotMode
from ..session.session_manager import load_user_session, get_saved_user_for_telegram_id, load_shared_session

logger = logging.getLogger(__name__)

async def user_data_loader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Load user data, including session data and user selections, at the start of each update.
    Ensures overseerr_user_id is available across restarts.
    """
    telegram_user_id = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
    logger.info(f"Loading user data for Telegram user {telegram_user_id} in mode {CURRENT_MODE.value}")

    # Normal mode: Load session data
    if CURRENT_MODE == BotMode.NORMAL:
        session_data = load_user_session(telegram_user_id)
        if session_data and "cookie" in session_data:
            context.user_data["session_data"] = session_data
            context.user_data["overseerr_user_id"] = session_data["overseerr_user_id"]
            context.user_data["overseerr_user_name"] = session_data.get("overseerr_user_name", "Unknown")
            logger.info(f"Loaded Normal mode session for user {telegram_user_id}: {session_data['overseerr_user_id']}")

    # API mode: Load user selection
    elif CURRENT_MODE == BotMode.API:
        overseerr_user_id, overseerr_user_name = get_saved_user_for_telegram_id(telegram_user_id)
        if overseerr_user_id:
            context.user_data["overseerr_user_id"] = overseerr_user_id
            context.user_data["overseerr_user_name"] = overseerr_user_name
            logger.info(f"Loaded API mode user selection for {telegram_user_id}: {overseerr_user_id} ({overseerr_user_name})")

    # Shared mode: Load shared session (global)
    elif CURRENT_MODE == BotMode.SHARED:
        shared_session = load_shared_session()
        if shared_session and "cookie" in shared_session:
            context.application.bot_data["shared_session"] = shared_session
            context.user_data["overseerr_user_id"] = shared_session["overseerr_user_id"]
            context.user_data["overseerr_user_name"] = shared_session.get("overseerr_user_name", "Shared User")
            logger.info(f"Loaded Shared mode session for user {telegram_user_id}: {shared_session['overseerr_user_id']}")

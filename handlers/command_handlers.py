"""
Command handlers for the Telegram bot.
"""
import logging
import base64
import requests
from datetime import datetime, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.config_manager import load_config, save_config, is_command_allowed
from config.constants import PASSWORD, CURRENT_MODE, BotMode, VERSION, BUILD
from session.session_manager import save_user_session, load_user_sessions, save_user_sessions, save_shared_session
from utils.telegram_utils import send_message
from api.overseerr_api import overseerr_login, search_media, process_search_results
from notifications.notification_manager import enable_global_telegram_notifications
from .ui_handlers import show_settings_menu, display_results_with_buttons

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /start command. Initialize user, check authorization, and show welcome message.
    """
    telegram_user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    message_thread_id = getattr(update.message, "message_thread_id", None)
    
    config = load_config()
    user_id_str = str(telegram_user_id)
    user = config["users"].get(user_id_str, {})

    # Check if command is allowed in this chat/thread
    if not is_command_allowed(chat_id, message_thread_id, config, telegram_user_id):
        logger.info(f"Ignoring /start in chat {chat_id}, thread {message_thread_id}: Group Mode restricts to primary")
        return

    # Update username if necessary
    current_username = update.effective_user.username or update.effective_user.full_name
    if not user or user.get("username") != current_username:
        is_first_user = not config["users"]  # True if no users exist yet
        config["users"][user_id_str] = {
            "username": current_username,
            "is_authorized": user.get("is_authorized", False),
            "is_blocked": user.get("is_blocked", False),
            "is_admin": user.get("is_admin", is_first_user),  # First user becomes admin
            "created_at": user.get("created_at", datetime.now(timezone.utc).isoformat() + "Z")
        }
        save_config(config)
        if is_first_user:
            logger.info(f"First user {telegram_user_id} registered as admin")

    # Handle Group Mode setup
    if config["group_mode"] and config["primary_chat_id"]["chat_id"] is None:
        config["primary_chat_id"]["chat_id"] = chat_id
        config["primary_chat_id"]["message_thread_id"] = message_thread_id
        save_config(config)
        await send_message(context, chat_id, "✅ *Primary chat set!* This chat is now the primary chat for Group Mode.", message_thread_id=message_thread_id)

    user = config["users"][user_id_str]  # Refresh user data
    
    # Check if user is blocked
    if user.get("is_blocked", False):
        await send_message(context, chat_id, "❌ *Access denied.* You have been blocked from using this bot.", message_thread_id=message_thread_id)
        return

    # Check authorization and password
    if not user.get("is_authorized", False) and PASSWORD:
        context.user_data["awaiting_password"] = True
        await send_message(context, chat_id, f"🤖 *Overseerr Telegram Bot* v{VERSION}\n\n🔐 Please enter the password to continue:", message_thread_id=message_thread_id)
        return
    elif not user.get("is_authorized", False) and not PASSWORD:
        # Auto-authorize if no password is set
        config["users"][user_id_str]["is_authorized"] = True
        save_config(config)

    # Show welcome message
    welcome_text = f"🎬 *Welcome to Overseerr Telegram Bot!*\n\n"
    welcome_text += f"📱 *Version:* {VERSION}\n"
    welcome_text += f"🔧 *Build:* {BUILD}\n\n"
    welcome_text += f"🎯 *Current Mode:* {CURRENT_MODE.value.title()}\n\n"
    welcome_text += "📚 *Available Commands:*\n"
    welcome_text += "• `/check <title>` - Search for movies/TV shows\n"
    welcome_text += "• `/settings` - Manage your account and bot settings\n\n"
    welcome_text += "💡 *Tip:* Use `/check The Matrix` to search for movies!"

    await send_message(context, chat_id, welcome_text, message_thread_id=message_thread_id)
    await enable_global_telegram_notifications(update, context)

async def check_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /check command to search for media.
    """
    telegram_user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    message_thread_id = getattr(update.message, "message_thread_id", None)
    
    config = load_config()
    
    # Check if command is allowed
    if not is_command_allowed(chat_id, message_thread_id, config, telegram_user_id):
        logger.info(f"Ignoring /check in chat {chat_id}, thread {message_thread_id}: Group Mode restricts to primary")
        return

    # Check authorization
    user_id_str = str(telegram_user_id)
    user = config["users"].get(user_id_str, {})
    if not user.get("is_authorized", False) or user.get("is_blocked", False):
        await send_message(context, chat_id, "❌ *Access denied.* Please use /start first.", message_thread_id=message_thread_id)
        return

    # Get search query
    if not context.args:
        await send_message(context, chat_id, "🔍 *Please provide a search term.*\n\nExample: `/check The Matrix`", message_thread_id=message_thread_id)
        return

    search_query = " ".join(context.args)
    logger.info(f"User {telegram_user_id} searching for: {search_query}")

    # Perform search directly without "searching..." message
    search_results = search_media(search_query)
    if not search_results:
        await send_message(context, chat_id, "❌ *Search failed.* Please try again later.", message_thread_id=message_thread_id)
        return

    results = search_results.get("results", [])
    if not results:
        await send_message(context, chat_id, f"🤷‍♂️ *No results found for:* {search_query}\n\nTry a different search term.", message_thread_id=message_thread_id)
        return

    # Process and display results
    processed_results = process_search_results(results)
    context.user_data["search_results"] = processed_results
    context.user_data["current_offset"] = 0

    await display_results_with_buttons(
        update, context, processed_results, offset=0,
        search_query=search_query, telegram_user_id=telegram_user_id
    )

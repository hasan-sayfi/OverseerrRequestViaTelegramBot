"""
Text input handlers for login, issue reporting, and password authentication.
"""
import logging
import base64
import requests
from datetime import datetime, timezone
from telegram import Update, CallbackQuery
from telegram.ext import ContextTypes

from config.config_manager import load_config, save_config, is_command_allowed
from config.constants import PASSWORD, CURRENT_MODE, BotMode, OVERSEERR_API_URL
from session.session_manager import load_user_sessions, save_user_sessions, save_shared_session
from utils.telegram_utils import send_message
from api.overseerr_api import overseerr_login, create_issue
from .command_handlers import start_command
from .ui_handlers import show_settings_menu

logger = logging.getLogger(__name__)

async def start_login(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    """Initiates login, deleting the settings menu and cleaning up prompts."""
    if isinstance(update_or_query, Update):
        telegram_user_id = update_or_query.effective_user.id
        message = update_or_query.message
    else:  # CallbackQuery
        telegram_user_id = update_or_query.from_user.id
        message = update_or_query.message

    logger.info(f"User {telegram_user_id} started login process.")

    # Check mode restrictions
    if CURRENT_MODE == BotMode.API:
        await message.reply_text("In API Mode, no login is required.")
        return

    if CURRENT_MODE == BotMode.SHARED:
        config = load_config()
        user_id_str = str(telegram_user_id)
        user = config["users"].get(user_id_str, {})
        if not user.get("is_admin", False):
            await message.reply_text("In Shared Mode, only admins can log in.")
            return

    # Delete the settings menu if this is a callback query
    if isinstance(update_or_query, CallbackQuery):
        try:
            await message.delete()
            logger.info(f"Deleted settings menu message for user {telegram_user_id} during login.")
        except Exception as e:
            logger.warning(f"Failed to delete settings menu message: {e}")

    # Set login state and prompt for email
    context.user_data["login_step"] = "email"
    msg = await context.bot.send_message(
        chat_id=message.chat_id,
        text="Please enter your Overseerr email address:"
    )
    context.user_data["login_message_id"] = msg.message_id

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles text input from users, including password authentication and issue reporting.
    """
    telegram_user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    message_thread_id = getattr(update.message, "message_thread_id", None)
    text = update.message.text
    logger.info(f"Text input from {telegram_user_id}: {text}, awaiting_password: {context.user_data.get('awaiting_password')}, chat {chat_id}, thread {message_thread_id}")

    config = load_config()
    user_id_str = str(telegram_user_id)
    user = config["users"].get(user_id_str, {})

    # Update username if necessary
    if not user or user.get("username") != (update.effective_user.username or update.effective_user.full_name):
        config["users"][user_id_str] = {
            "username": update.effective_user.username or update.effective_user.full_name,
            "is_authorized": user.get("is_authorized", False),
            "is_blocked": user.get("is_blocked", False),
            "is_admin": user.get("is_admin", False),
            "created_at": user.get("created_at", datetime.now(timezone.utc).isoformat() + "Z")
        }
        save_config(config)

    # Handle issue reporting
    if 'reporting_issue' in context.user_data:
        await handle_issue_report(update, context, text)
        return

    # Handle password authentication
    if context.user_data.get("awaiting_password"):
        await handle_password_authentication(update, context, text)
        return

    # Ignore non-command text input if Group Mode restricts this chat/thread
    if not is_command_allowed(chat_id, message_thread_id, config, telegram_user_id):
        logger.info(f"Ignoring text input in chat {chat_id}, thread {message_thread_id}: Group Mode restricts to primary")
        return

    # Handle Overseerr login
    if "login_step" in context.user_data:
        await handle_overseerr_login(update, context, text)
        return

    # Fallback for unrecognized input
    logger.info(f"User {telegram_user_id} typed something unrecognized: {text}")
    await update.message.reply_text(
        "I didn't understand that. Please use /start to see the available commands."
    )

async def handle_issue_report(update: Update, context: ContextTypes.DEFAULT_TYPE, issue_description: str):
    """Handle issue reporting text input."""
    telegram_user_id = update.effective_user.id
    reporting_issue = context.user_data['reporting_issue']
    issue_type_id = reporting_issue['issue_type']
    issue_type_name = reporting_issue['issue_type_name']

    selected_result = context.user_data.get('selected_result')
    if not selected_result:
        logger.error("No selected_result found while reporting an issue.")
        await update.message.reply_text(
            "An error occurred. Please try reporting the issue again.",
            parse_mode="Markdown",
        )
        return

    media_id = selected_result.get('overseerr_id')
    media_title = selected_result['title']
    media_type = selected_result['mediaType']

    overseerr_telegram_user_id = context.user_data.get("overseerr_telegram_user_id")
    user_display_name = context.user_data.get("overseerr_user_name", "Unknown User")
    logger.info(
        f"User {telegram_user_id} is reporting an issue on mediaId {media_id} "
        f"as Overseerr user {overseerr_telegram_user_id}."
    )

    final_issue_description = f"(Reported by {user_display_name})\n\n{issue_description}"

    success = create_issue(
        media_id=media_id,
        media_type=media_type,
        issue_description=final_issue_description,
        issue_type=issue_type_id,
        user_id=overseerr_telegram_user_id
    )

    if success:
        await update.message.reply_text(
            f"✅ Thank you! Your issue with *{media_title}* has been successfully reported.",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            f"❌ Failed to report the issue with *{media_title}*. Please try again later.",
            parse_mode="Markdown",
        )

    # Cleanup
    context.user_data.pop('reporting_issue', None)
    media_message_id = context.user_data.get('media_message_id')
    if media_message_id:
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=media_message_id
            )
            logger.info(f"Deleted media message {media_message_id} after issue reporting.")
        except Exception as e:
            logger.warning(f"Failed to delete media message {media_message_id}: {e}")
        context.user_data.pop('media_message_id', None)

    context.user_data.pop('selected_result', None)

async def handle_password_authentication(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle password authentication input."""
    telegram_user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    message_thread_id = getattr(update.message, "message_thread_id", None)
    
    config = load_config()
    user_id_str = str(telegram_user_id)
    user = config["users"].get(user_id_str, {})
    
    logger.info(f"Comparing input '{text}' with PASSWORD '{PASSWORD}'")
    if text == PASSWORD:
        is_admin = user.get("is_admin", False)
        if not user.get("is_authorized", False):
            config["users"][user_id_str] = {
                "username": update.effective_user.username or update.effective_user.full_name,
                "is_authorized": True,
                "is_blocked": False,
                "is_admin": is_admin,
                "created_at": datetime.now(timezone.utc).isoformat() + "Z"
            }
            save_config(config)
            logger.info(f"User {telegram_user_id} added to users with authorized status")
        context.user_data.pop("awaiting_password")
        await send_message(context, chat_id, "✅ *Access granted!* Let's get started...", message_thread_id=message_thread_id)
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
        await start_command(update, context)
        if not is_admin and CURRENT_MODE == BotMode.API:
            from .ui_handlers import handle_change_user
            await handle_change_user(update, context, is_initial=True)
    else:
        await send_message(context, chat_id, "❌ *Oops!* That's not the right password. Try again:", message_thread_id=message_thread_id)
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)

async def handle_overseerr_login(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle Overseerr login process."""
    telegram_user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    config = load_config()
    user_id_str = str(telegram_user_id)
    user = config["users"].get(user_id_str, {})
    
    # Delete previous prompt and user input
    if "login_message_id" in context.user_data:
        try:
            await context.bot.delete_message(chat_id, context.user_data["login_message_id"])
        except Exception as e:
            logger.warning(f"Failed to delete login prompt message: {e}")
    try:
        await context.bot.delete_message(chat_id, update.message.message_id)
    except Exception as e:
        logger.warning(f"Failed to delete user input message: {e}")

    is_admin = user.get("is_admin", False)

    if context.user_data["login_step"] == "email":
        context.user_data["login_email"] = text
        context.user_data["login_step"] = "password"
        msg = await context.bot.send_message(chat_id, "Please enter your Overseerr password:")
        context.user_data["login_message_id"] = msg.message_id
    elif context.user_data["login_step"] == "password":
        email = context.user_data["login_email"]
        password = text
        session_cookie = overseerr_login(email, password)
        if session_cookie:
            credentials = base64.b64encode(f"{email}:{password}".encode()).decode()
            response = requests.get(
                f"{OVERSEERR_API_URL}/auth/me",
                headers={"Cookie": f"connect.sid={session_cookie}"}
            )
            user_info = response.json()
            overseerr_id = user_info.get("id")
            if not overseerr_id:
                await context.bot.send_message(chat_id, "❌ Login failed: Invalid user data.")
                await show_settings_menu(update, context, is_admin=is_admin)
                return
            
            session_data = {
                "cookie": session_cookie,
                "credentials": credentials,
                "overseerr_telegram_user_id": overseerr_id,
                "overseerr_user_name": user_info.get("displayName", "Unknown")
            }
            context.user_data["session_data"] = session_data
            
            if CURRENT_MODE == BotMode.NORMAL:
                sessions = load_user_sessions()
                sessions[str(telegram_user_id)] = session_data
                save_user_sessions(sessions)
            elif CURRENT_MODE == BotMode.SHARED and is_admin:
                save_shared_session(session_data)
                context.application.bot_data["shared_session"] = session_data
            
            await context.bot.send_message(
                chat_id,
                f"✅ Logged in as {user_info.get('displayName', 'Unknown')}!"
            )
        else:
            await context.bot.send_message(chat_id, "❌ Login failed. Check your credentials.")
        
        context.user_data.pop("login_step", None)
        context.user_data.pop("login_email", None)
        context.user_data.pop("login_message_id", None)
        await show_settings_menu(update, context, is_admin=is_admin)

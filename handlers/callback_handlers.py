"""
Callback query handlers for button interactions.
"""
import logging
from telegram import Update, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..config.config_manager import load_config, save_config
from ..config.constants import CURRENT_MODE, BotMode
from ..session.session_manager import save_user_selection, clear_shared_session
from ..utils.telegram_utils import send_message
from ..api.overseerr_api import request_media, get_overseerr_users
from ..notifications.notification_manager import update_telegram_settings_for_user, get_user_notification_settings
from .ui_handlers import (
    show_settings_menu, display_results_with_buttons, process_user_selection, handle_change_user
)
from .text_handlers import start_login

logger = logging.getLogger(__name__)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main callback query handler for all button interactions.
    """
    query = update.callback_query
    await query.answer()
    
    data = query.data
    telegram_user_id = query.from_user.id
    
    logger.info(f"Button callback from user {telegram_user_id}: {data}")
    
    try:
        # Settings and login callbacks
        if data == "login":
            await start_login(query, context)
        elif data == "logout":
            await handle_logout(query, context)
        elif data == "change_user":
            await handle_change_user(query, context)
        elif data == "back_to_settings":
            config = load_config()
            user = config["users"].get(str(telegram_user_id), {})
            await show_settings_menu(query, context, is_admin=user.get("is_admin", False))
        elif data == "cancel_settings":
            await query.edit_message_text("⚙️ Settings cancelled.")
        
        # Mode selection callbacks
        elif data == "mode_select":
            await show_mode_selection(query, context)
        elif data.startswith("activate_"):
            mode = data.replace("activate_", "")
            await handle_mode_change(query, context, mode)
        
        # User management callbacks
        elif data == "manage_users":
            await show_user_management_menu(query, context)
        elif data.startswith("manage_user_"):
            user_id = data.replace("manage_user_", "")
            await manage_specific_user(query, context, user_id)
        elif data.startswith("promote_user_"):
            user_id = data.replace("promote_user_", "")
            await handle_user_promotion(query, context, user_id, True)
        elif data.startswith("demote_user_"):
            user_id = data.replace("demote_user_", "")
            await handle_user_promotion(query, context, user_id, False)
        elif data.startswith("block_user_"):
            user_id = data.replace("block_user_", "")
            await handle_user_block(query, context, user_id, True)
        elif data.startswith("unblock_user_"):
            user_id = data.replace("unblock_user_", "")
            await handle_user_block(query, context, user_id, False)
        
        # Search result navigation
        elif data.startswith("page_"):
            offset = int(data.replace("page_", ""))
            context.user_data["current_offset"] = offset
            search_results = context.user_data.get("search_results", [])
            search_query = context.user_data.get("search_query", "")
            await display_results_with_buttons(
                update, context, search_results, offset=offset, 
                search_query=search_query, telegram_user_id=telegram_user_id
            )
        elif data.startswith("select_"):
            selection_index = int(data.replace("select_", ""))
            await process_user_selection(update, context, selection_index, telegram_user_id)
        elif data == "back_to_results":
            await handle_back_to_results(query, context)
        elif data == "cancel_search":
            await query.edit_message_text("🔍 Search cancelled.")
        
        # Media request callbacks
        elif data.startswith("confirm_1080p_"):
            media_id = int(data.replace("confirm_1080p_", ""))
            await handle_media_request(query, context, media_id, is4k=False)
        elif data.startswith("confirm_4k_"):
            media_id = int(data.replace("confirm_4k_", ""))
            await handle_media_request(query, context, media_id, is4k=True)
        elif data.startswith("confirm_both_"):
            media_id = int(data.replace("confirm_both_", ""))
            await handle_media_request(query, context, media_id, is4k=False)
            await handle_media_request(query, context, media_id, is4k=True)
        
        # Season selection callbacks
        elif data.startswith("toggle_season_"):
            parts = data.split("_")
            media_id = int(parts[2])
            season_num = int(parts[3])
            await handle_season_toggle(query, context, media_id, season_num)
        elif data.startswith("finalize_seasons_"):
            media_id = int(data.replace("finalize_seasons_", ""))
            await handle_season_request(query, context, media_id)
        
        # Issue reporting callbacks
        elif data.startswith("report_"):
            media_id = int(data.replace("report_", ""))
            await handle_issue_report_start(query, context, media_id)
        elif data.startswith("issue_type_"):
            issue_type = int(data.replace("issue_type_", ""))
            await handle_issue_type_selection(query, context, issue_type)
        
        # User selection callbacks (API mode)
        elif data.startswith("select_user_"):
            user_id = int(data.replace("select_user_", ""))
            await handle_user_selection(query, context, user_id)
        elif data.startswith("users_page_"):
            offset = int(data.replace("users_page_", ""))
            await handle_change_user(query, context, offset=offset)
        elif data == "cancel_user_selection":
            await query.edit_message_text("👤 User selection cancelled.")
        
        # Notification management callbacks
        elif data == "manage_notifications":
            await show_manage_notifications_menu(query, context)
        elif data == "toggle_user_notifications":
            await toggle_user_notifications(query, context)
        elif data == "toggle_user_silent":
            await toggle_user_silent(query, context)
        
        # Group mode toggle
        elif data == "toggle_group_mode":
            await handle_group_mode_toggle(query, context)
        
        else:
            logger.warning(f"Unhandled callback data: {data}")
            await query.edit_message_text("❌ Unknown action. Please try again.")
    
    except Exception as e:
        logger.error(f"Error in button_handler: {e}")
        await query.edit_message_text("❌ An error occurred. Please try again.")

async def handle_logout(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """Handle logout for different modes."""
    telegram_user_id = query.from_user.id
    
    if CURRENT_MODE == BotMode.NORMAL:
        # Clear user session
        context.user_data.pop("session_data", None)
        context.user_data.pop("overseerr_user_id", None)
        context.user_data.pop("overseerr_user_name", None)
        await query.edit_message_text("🔓 Successfully logged out!")
    
    elif CURRENT_MODE == BotMode.SHARED:
        # Clear shared session (admin only)
        config = load_config()
        user = config["users"].get(str(telegram_user_id), {})
        if user.get("is_admin", False):
            clear_shared_session()
            context.application.bot_data.pop("shared_session", None)
            context.user_data.pop("overseerr_user_id", None)
            context.user_data.pop("overseerr_user_name", None)
            await query.edit_message_text("🔓 Shared session logged out!")
        else:
            await query.edit_message_text("❌ Only admins can logout in Shared mode.")
    
    else:
        await query.edit_message_text("❌ Logout not available in this mode.")

async def handle_media_request(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, media_id: int, is4k: bool):
    """Handle media request with proper authentication."""
    selected_result = context.user_data.get("selected_result")
    if not selected_result:
        await query.edit_message_text("❌ No media selected.")
        return
    
    media_type = selected_result["mediaType"]
    media_title = selected_result["title"]
    
    # Get authentication details based on mode
    session_cookie = None
    overseerr_user_id = context.user_data.get("overseerr_user_id")
    
    if CURRENT_MODE == BotMode.NORMAL:
        session_data = context.user_data.get("session_data")
        if session_data:
            session_cookie = session_data.get("cookie")
    elif CURRENT_MODE == BotMode.SHARED:
        shared_session = context.application.bot_data.get("shared_session")
        if shared_session:
            session_cookie = shared_session.get("cookie")
    
    # Make request
    success, message = request_media(
        media_id=media_id,
        media_type=media_type,
        requested_by=overseerr_user_id if CURRENT_MODE == BotMode.API else None,
        is4k=is4k,
        session_cookie=session_cookie
    )
    
    quality = "4K" if is4k else "1080p"
    if success:
        await query.edit_message_text(f"✅ Successfully requested *{media_title}* in {quality}!", parse_mode="Markdown")
    else:
        await query.edit_message_text(f"❌ Failed to request *{media_title}* in {quality}.\n\nError: {message}", parse_mode="Markdown")

async def handle_user_selection(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Handle user selection in API mode."""
    telegram_user_id = query.from_user.id
    
    # Get user details from Overseerr
    users = get_overseerr_users()
    selected_user = next((user for user in users if user["id"] == user_id), None)
    
    if not selected_user:
        await query.edit_message_text("❌ User not found.")
        return
    
    user_name = selected_user.get("displayName") or selected_user.get("email", f"User {user_id}")
    
    # Save selection
    save_user_selection(telegram_user_id, user_id, user_name)
    context.user_data["overseerr_user_id"] = user_id
    context.user_data["overseerr_user_name"] = user_name
    
    await query.edit_message_text(f"✅ Selected user: *{user_name}* (ID: {user_id})", parse_mode="Markdown")

async def show_mode_selection(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """Show mode selection menu for admins."""
    config = load_config()
    user = config["users"].get(str(query.from_user.id), {})
    
    if not user.get("is_admin", False):
        await query.edit_message_text("❌ Only admins can change bot mode.")
        return
    
    text = (
        "🔧 *Bot Mode Selection*\n\n"
        f"Current mode: *{CURRENT_MODE.value.title()}*\n\n"
        "**Modes:**\n"
        "🌟 **Normal** - Users login with their own credentials\n"
        "🔑 **API** - Users select from existing Overseerr users\n"
        "👥 **Shared** - All users share one account\n\n"
        "Select a new mode:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🌟 Normal", callback_data="activate_normal"),
            InlineKeyboardButton("🔑 API", callback_data="activate_api"),
            InlineKeyboardButton("👥 Shared", callback_data="activate_shared")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_settings")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)

async def handle_mode_change(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, mode: str):
    """Handle bot mode change."""
    global CURRENT_MODE
    
    config = load_config()
    user = config["users"].get(str(query.from_user.id), {})
    
    if not user.get("is_admin", False):
        await query.edit_message_text("❌ Only admins can change bot mode.")
        return
    
    try:
        new_mode = BotMode[mode.upper()]
        CURRENT_MODE = new_mode
        
        config["mode"] = mode
        save_config(config)
        
        await query.edit_message_text(f"✅ Bot mode changed to: *{mode.title()}*", parse_mode="Markdown")
    except KeyError:
        await query.edit_message_text("❌ Invalid mode selected.")

# Additional helper functions would go here...
async def show_user_management_menu(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """Show user management menu placeholder."""
    await query.edit_message_text("👤 User management feature coming soon...")

async def manage_specific_user(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, user_id: str):
    """Manage specific user placeholder."""
    await query.edit_message_text(f"Managing user {user_id}...")

async def handle_user_promotion(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, user_id: str, promote: bool):
    """Handle user promotion/demotion placeholder."""
    action = "promoted" if promote else "demoted"
    await query.edit_message_text(f"User {user_id} {action}.")

async def handle_user_block(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, user_id: str, block: bool):
    """Handle user blocking/unblocking placeholder."""
    action = "blocked" if block else "unblocked"
    await query.edit_message_text(f"User {user_id} {action}.")

async def handle_back_to_results(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to search results."""
    search_results = context.user_data.get("search_results", [])
    current_offset = context.user_data.get("current_offset", 0)
    search_query = context.user_data.get("search_query", "")
    
    if search_results:
        await display_results_with_buttons(
            query, context, search_results, offset=current_offset,
            search_query=search_query, telegram_user_id=query.from_user.id
        )
    else:
        await query.edit_message_text("❌ No search results to return to.")

async def handle_season_toggle(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, media_id: int, season_num: int):
    """Handle season selection toggle placeholder."""
    await query.answer(f"Season {season_num} toggled")

async def handle_season_request(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, media_id: int):
    """Handle season request placeholder."""
    await query.edit_message_text("📥 Season request feature coming soon...")

async def handle_issue_report_start(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, media_id: int):
    """Handle issue report start placeholder."""
    await query.edit_message_text("🛠 Issue reporting feature coming soon...")

async def handle_issue_type_selection(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, issue_type: int):
    """Handle issue type selection placeholder."""
    await query.edit_message_text(f"Selected issue type: {issue_type}")

async def show_manage_notifications_menu(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """Show notification management menu placeholder."""
    await query.edit_message_text("🔔 Notification management coming soon...")

async def toggle_user_notifications(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """Toggle user notifications placeholder."""
    await query.edit_message_text("🔔 Notification toggle coming soon...")

async def toggle_user_silent(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """Toggle silent notifications placeholder."""
    await query.edit_message_text("🤫 Silent mode toggle coming soon...")

async def handle_group_mode_toggle(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """Handle group mode toggle placeholder."""
    await query.edit_message_text("👥 Group mode toggle coming soon...")

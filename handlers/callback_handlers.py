"""
Callback query handlers for button interactions.
"""
import logging
from telegram import Update, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.config_manager import load_config, save_config
from config.constants import CURRENT_MODE, BotMode, ISSUE_TYPES
from session.session_manager import save_user_selection, clear_shared_session, clear_user_session
from utils.telegram_utils import send_message
from api.overseerr_api import request_media, get_overseerr_users, overseerr_logout
from notifications.notification_manager import update_telegram_settings_for_user, get_user_notification_settings
from .ui_handlers import (
    show_settings_menu, display_results_with_buttons, process_user_selection, handle_change_user
)
from .text_handlers import start_login

logger = logging.getLogger(__name__)

def escape_markdown(text: str) -> str:
    """Escape special Markdown characters to prevent parsing errors."""
    if not text:
        return text
    # Escape all markdown special characters
    return text.replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('`', '\\`').replace('~', '\\~').replace('>', '\\>')

async def safe_edit_message(query: CallbackQuery, text: str, parse_mode="Markdown", reply_markup=None):
    """
    Safely edit a message, handling both photo (caption) and text messages.
    Also handles cases where content is identical or message type conflicts.
    """
    try:
        current_message = query.message
        
        # Check if we're trying to edit with identical content
        if hasattr(current_message, 'text') and current_message.text:
            if current_message.text.strip() == text.strip():
                logger.debug("Skipping message edit - content is identical")
                return
        elif hasattr(current_message, 'caption') and current_message.caption:
            if current_message.caption.strip() == text.strip():
                logger.debug("Skipping caption edit - content is identical")
                return
        
        # Handle photo messages (edit caption)
        if hasattr(current_message, 'photo') and current_message.photo:
            await query.edit_message_caption(
                caption=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
        # Handle text messages (edit text)
        elif hasattr(current_message, 'text'):
            await query.edit_message_text(
                text,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
        else:
            # Fallback: send new message if we can't edit
            logger.warning("Cannot edit message - sending new message instead")
            await query.message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
            
    except Exception as e:
        logger.warning(f"Failed to edit message: {e}")
        try:
            # Try to send a new message as fallback
            await query.message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
        except Exception as fallback_error:
            logger.error(f"Even fallback message failed: {fallback_error}")
            # Last resort - just answer the query
            await query.answer("Action completed", show_alert=True)

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
        elif data == "show_settings":
            config = load_config()
            user = config["users"].get(str(telegram_user_id), {})
            await show_settings_menu(query, context, is_admin=user.get("is_admin", False))
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
            # Clear search data and provide a friendly message
            context.user_data.pop("search_results", None)
            context.user_data.pop("selected_result", None)
            context.user_data.pop("selected_seasons", None)
            context.user_data.pop("current_offset", None)
            
            await safe_edit_message(
                query, 
                "🔍 *Search Cancelled*\n\n"
                "Your search has been cancelled. Use `/check [title]` to start a new search.\n\n"
                "*Example:* `/check The Matrix`"
            )
        
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
        
        # Request More seasons callback
        elif data.startswith("request_more_"):
            media_id = int(data.replace("request_more_", ""))
            await handle_request_more_seasons(query, context, media_id)
        
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
        
        # TV/Anime selection for multi-season requests
        elif data in ("sonarr_multi_tv", "sonarr_multi_anime"):
            await handle_tv_anime_selection(query, context, data)
        elif data == "back_to_multi_selection":
            await handle_back_to_multi_selection(query, context)
        
        # TV/Anime selection for "All in 1080p/4K" requests
        elif data in ("all_sonarr_tv", "all_sonarr_anime"):
            await handle_all_tv_anime_selection(query, context, data)
        
        # Individual season request callbacks
        elif data.startswith("confirm_season_"):
            parts = data.split("_")
            season_number = int(parts[3])
            await handle_season_request_individual(query, context, season_number)
        elif data in ("sonarr_tv", "sonarr_anime"):
            await handle_individual_tv_anime_selection(query, context, data)
        
        # User page navigation (different from users_page_)
        elif data.startswith("user_page_"):
            offset = int(data.split("_")[2])
            await handle_change_user(query, context, offset=offset)
        
        # Back to media details
        elif data == "back_to_media_details":
            # Clear any pending requests and return to media details
            context.user_data.pop("pending_request", None)
            context.user_data.pop("pending_all_request", None)
            context.user_data.pop("pending_multi_request", None)
            await handle_back_to_results(query, context)
        
        else:
            logger.warning(f"Unhandled callback data: {data}")
            await safe_edit_message(query, "❌ Unknown action. Please try again.")
    
    except Exception as e:
        logger.error(f"Error in button_handler: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        # Show more specific error message
        error_msg = f"❌ Error: {str(e)}" if str(e) else "❌ An unknown error occurred. Check logs for details."
        await safe_edit_message(query, error_msg)

async def handle_logout(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """Handle logout for different modes."""
    telegram_user_id = query.from_user.id
    
    if CURRENT_MODE == BotMode.NORMAL:
        # Get session cookie before clearing
        session_data = context.user_data.get("session_data", {})
        session_cookie = session_data.get("cookie")
        
        # Call Overseerr logout API if we have a session cookie
        if session_cookie:
            logout_success = overseerr_logout(session_cookie)
            if logout_success:
                logger.info(f"User {telegram_user_id} successfully logged out from Overseerr")
            else:
                logger.warning(f"Failed to logout user {telegram_user_id} from Overseerr, but clearing local session")
        
        # Clear user session data from memory
        context.user_data.pop("session_data", None)
        context.user_data.pop("overseerr_user_id", None)
        context.user_data.pop("overseerr_user_name", None)
        
        # Clear user session from persistent storage
        clear_user_session(telegram_user_id)
        
        await query.edit_message_text("🔓 Successfully logged out!")
    
    elif CURRENT_MODE == BotMode.SHARED:
        # Clear shared session (admin only)
        config = load_config()
        user = config["users"].get(str(telegram_user_id), {})
        if user.get("is_admin", False):
            # Get shared session cookie before clearing
            shared_session = context.application.bot_data.get("shared_session", {})
            session_cookie = shared_session.get("cookie")
            
            # Call Overseerr logout API if we have a session cookie
            if session_cookie:
                logout_success = overseerr_logout(session_cookie)
                if logout_success:
                    logger.info(f"Admin {telegram_user_id} successfully logged out shared session from Overseerr")
                else:
                    logger.warning(f"Failed to logout shared session from Overseerr, but clearing local session")
            
            # Clear shared session
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
        await safe_edit_message(query, "❌ No media selected.")
        return
    
    media_type = selected_result["mediaType"]
    media_title = selected_result["title"]
    
    # For TV shows, prompt for TV/Anime choice instead of direct request
    if media_type == "tv":
        # Store request context for later processing
        context.user_data["pending_all_request"] = {
            "media_id": media_id,
            "title": media_title,
            "media_type": media_type,
            "is4k": is4k
        }

        # Build TV/Anime choice keyboard
        quality = "4K" if is4k else "1080p"
        keyboard = [
            [
                InlineKeyboardButton("📺 TV Series", callback_data="all_sonarr_tv"),
                InlineKeyboardButton("🎴 Anime", callback_data="all_sonarr_anime")
            ],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_to_media_details")]
        ]
        
        message_text = (
            f"*{media_title}* - All Seasons in {quality}\n\n"
            f"📁 Choose the content type for this request:"
        )
        
        await safe_edit_message(query, message_text, reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    # For movies, proceed with direct request
    await _process_direct_media_request(query, context, media_id, is4k)

async def _process_direct_media_request(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, media_id: int, is4k: bool):
    """Process direct media request (for movies or after TV/Anime choice)."""
    selected_result = context.user_data.get("selected_result")
    if not selected_result:
        await safe_edit_message(query, "❌ No media selected.")
        return
    
    media_type = selected_result["mediaType"]
    media_title = selected_result["title"]
    
    # Get authentication details based on mode
    session_cookie = None
    overseerr_user_id = context.user_data.get("overseerr_user_id")
    
    if CURRENT_MODE == BotMode.NORMAL:
        session_data = context.user_data.get("session_data")
        if not session_data:
            await safe_edit_message(query, "❌ You are not logged in. Please use /settings to login first.")
            return
        session_cookie = session_data.get("cookie")
        if not session_cookie:
            await safe_edit_message(query, "❌ Invalid session. Please login again via /settings.")
            return
    elif CURRENT_MODE == BotMode.SHARED:
        shared_session = context.application.bot_data.get("shared_session")
        if not shared_session:
            await safe_edit_message(query, "❌ No shared session available. Admin needs to login via /settings.")
            return
        session_cookie = shared_session.get("cookie")
    elif CURRENT_MODE == BotMode.API:
        if not overseerr_user_id:
            await safe_edit_message(query, "❌ No Overseerr user selected. Please use /settings to select a user.")
            return
    
    # Make request
    success, message = request_media(
        media_id=media_id,
        media_type=media_type,
        requested_by=overseerr_user_id if CURRENT_MODE == BotMode.API else None,
        is4k=is4k,
        session_cookie=session_cookie
    )
    
    quality = "4K" if is4k else "1080p"
    status_message = f"✅ Successfully requested *{media_title}* in {quality}!" if success else f"❌ Failed to request *{media_title}* in {quality}.\n\nError: {message}"
    
    await safe_edit_message(query, status_message)

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
    await safe_edit_message(query, text, parse_mode="Markdown", reply_markup=reply_markup)

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
async def show_user_management_menu(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, offset=0):
    """Show user management menu with pagination."""
    from config.config_manager import load_config
    
    config = load_config()
    telegram_user_id = query.from_user.id
    
    # Check if user is admin
    user_id_str = str(telegram_user_id)
    if not config["users"].get(user_id_str, {}).get("is_admin", False):
        await query.edit_message_text("❌ Only admins can manage users.")
        return

    users = [
        {
            "telegram_id": uid,
            "username": details.get("username", "Unknown"),
            "is_admin": details.get("is_admin", False),
            "is_blocked": details.get("is_blocked", False)
        }
        for uid, details in config["users"].items()
    ]

    if not users:
        text = "👥 *User Management*\n\nNo users found."
        keyboard = [
            [InlineKeyboardButton("➕ Create new Overseerr User", callback_data="create_user")],
            [InlineKeyboardButton("⬅️ Back to Settings", callback_data="back_to_settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(query, text, parse_mode="Markdown", reply_markup=reply_markup)
        return

    page_size = 5
    total_users = len(users)
    current_users = users[offset:offset + page_size]

    text = "� *User Management*\n\nSelect a user to manage:\n"
    keyboard = []
    
    for user in current_users:
        status = "🚫 Blocked" if user["is_blocked"] else "👑 Admin" if user["is_admin"] else "✅ User"
        button_text = f"{user['username']} (ID: {user['telegram_id']}) - {status}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"manage_user_{user['telegram_id']}")])

    keyboard.append([InlineKeyboardButton("➕ Create new Overseerr User", callback_data="create_user")])

    # Navigation buttons
    navigation_buttons = []
    if offset > 0:
        navigation_buttons.append(InlineKeyboardButton("⬅️ Back", callback_data=f"users_page_{offset - page_size}"))
    if offset + page_size < total_users:
        navigation_buttons.append(InlineKeyboardButton("➡️ More", callback_data=f"users_page_{offset + page_size}"))
    navigation_buttons.append(InlineKeyboardButton("⬅️ Back to Settings", callback_data="back_to_settings"))
    keyboard.append(navigation_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await safe_edit_message(query, text, parse_mode="Markdown", reply_markup=reply_markup)

async def manage_specific_user(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, user_id: str):
    """Manage a specific user (block, unblock, promote, demote)."""
    config = load_config()
    telegram_user_id = query.from_user.id

    # Check if current user is admin
    user_id_str = str(telegram_user_id)
    if not config["users"].get(user_id_str, {}).get("is_admin", False):
        await query.edit_message_text("❌ Only admins can manage users.")
        return

    # Get user info
    user = config["users"].get(user_id, {})
    username = user.get("username", "Unknown")
    is_admin = user.get("is_admin", False)
    is_blocked = user.get("is_blocked", False)

    text = (
        f"👤 *Manage User: {username}*\n"
        f"🆔 ID: {user_id}\n"
        f"🔖 Status: {'Blocked' if is_blocked else 'Admin' if is_admin else 'User'}\n\n"
        "Choose an action:"
    )

    keyboard = []
    if is_blocked:
        keyboard.append([InlineKeyboardButton("✅ Unblock User", callback_data=f"unblock_user_{user_id}")])
    else:
        keyboard.append([InlineKeyboardButton("🚫 Block User", callback_data=f"block_user_{user_id}")])
    
    if is_admin and user_id != user_id_str:
        keyboard.append([InlineKeyboardButton("👇 Demote to User", callback_data=f"demote_user_{user_id}")])
    elif not is_admin and not is_blocked:
        keyboard.append([InlineKeyboardButton("👑 Promote to Admin", callback_data=f"promote_user_{user_id}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back to User List", callback_data="manage_users")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await safe_edit_message(query, text, parse_mode="Markdown", reply_markup=reply_markup)

async def handle_user_promotion(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, user_id: str, promote: bool):
    """Handle user promotion/demotion."""
    config = load_config()
    telegram_user_id = query.from_user.id

    # Check if current user is admin
    user_id_str = str(telegram_user_id)
    if not config["users"].get(user_id_str, {}).get("is_admin", False):
        await query.edit_message_text("❌ Only admins can manage users.")
        return

    # Prevent demoting self
    if not promote and user_id == user_id_str:
        await query.edit_message_text("❌ Cannot demote the main admin.")
        return

    # Update user status
    if promote:
        config["users"][user_id]["is_admin"] = True
        config["users"][user_id]["is_authorized"] = True
        config["users"][user_id]["is_blocked"] = False
    else:
        config["users"][user_id]["is_admin"] = False

    save_config(config)
    
    # Return to user management view
    await manage_specific_user(query, context, user_id)

async def handle_user_block(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, user_id: str, block: bool):
    """Handle user blocking/unblocking."""
    config = load_config()
    telegram_user_id = query.from_user.id

    # Check if current user is admin
    user_id_str = str(telegram_user_id)
    if not config["users"].get(user_id_str, {}).get("is_admin", False):
        await query.edit_message_text("❌ Only admins can manage users.")
        return

    # Prevent blocking self if admin
    if block and config["users"].get(user_id, {}).get("is_admin", False) and user_id == user_id_str:
        await query.edit_message_text("❌ Cannot block the main admin.")
        return

    # Update user status
    if block:
        config["users"][user_id]["is_blocked"] = True
        config["users"][user_id]["is_authorized"] = False
    else:
        config["users"][user_id]["is_blocked"] = False
        config["users"][user_id]["is_authorized"] = True

    save_config(config)
    
    # Return to user management view
    await manage_specific_user(query, context, user_id)

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
        await safe_edit_message(query, "❌ No search results to return to.")

async def handle_season_toggle(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, media_id: int, season_num: int):
    """Handle season selection toggle."""
    await query.answer(f"Season {season_num} toggled")
    
    # Toggle season in user's selection
    selected_seasons = set(context.user_data.get('selected_seasons', []))
    if season_num in selected_seasons:
        selected_seasons.remove(season_num)
    else:
        selected_seasons.add(season_num)
    context.user_data['selected_seasons'] = selected_seasons
    
    # Find the selected result and refresh the view inline (edit the existing message)
    search_results = context.user_data.get("search_results", [])
    selected_result = None
    for result in search_results:
        if result.get('id') == media_id:
            selected_result = result
            break
    
    if selected_result:
        # Update the selected result in context
        context.user_data["selected_result"] = selected_result
        
        # Get the selected seasons list for display
        selected_seasons = set(context.user_data.get('selected_seasons', []))
        
        # Check if we're in request_more mode by checking if we have cached seasons
        is_request_more_mode = f"seasons_{media_id}" in context.user_data
        
        # Rebuild the media details with updated season buttons inline
        from handlers.ui_handlers import build_media_details_message
        media_text, keyboard = await build_media_details_message(selected_result, context, selected_seasons, request_more_mode=is_request_more_mode)
        
        # Edit the existing message caption with updated buttons
        try:
            await query.edit_message_caption(
                caption=media_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Failed to edit message caption: {e}")
            # If editing fails, fall back to creating new message
            from handlers.ui_handlers import process_user_selection
            selection_index = search_results.index(selected_result)
            await process_user_selection(query, context, selection_index, query.from_user.id)

async def handle_season_request(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, media_id: int):
    """Handle multi-season request with TV/Anime selection."""
    selected_seasons = context.user_data.get('selected_seasons', [])
    if not selected_seasons:
        await query.answer("No seasons selected.", show_alert=True)
        return

    # Find the selected result
    search_results = context.user_data.get("search_results", [])
    selected_result = None
    for result in search_results:
        if result.get('id') == media_id:
            selected_result = result
            break
    
    if not selected_result:
        await query.edit_message_text("❌ Media not found.")
        return

    # Only for TV media - prompt for TV/Anime selection
    if selected_result["mediaType"] == "tv":
        # Store the multi-season context
        context.user_data["pending_multi_request"] = {
            "media_id": media_id,
            "seasons": list(selected_seasons),
            "title": selected_result["title"],
            "media_type": "tv"
        }

        # Build inline keyboard with TV/Anime choice
        keyboard = [
            [
                InlineKeyboardButton("📺 TV Series", callback_data="sonarr_multi_tv"),
                InlineKeyboardButton("🎴 Anime", callback_data="sonarr_multi_anime")
            ],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_to_multi_selection")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = (
            f"*{selected_result['title']}* – {len(selected_seasons)} Seasons Selected\n"
            f"Seasons: {', '.join(map(str, sorted(selected_seasons)))}\n\n"
            "Is this TV Series or Anime?"
        )
        
        await safe_edit_message(query, message_text, reply_markup=reply_markup)

async def handle_issue_report_start(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, media_id: int):
    """Handle issue report start - show issue types."""
    context.user_data["reporting_issue"] = {
        "media_id": media_id,
        "step": "select_type"
    }
    
    keyboard = [
        [InlineKeyboardButton(text=ISSUE_TYPES[1], callback_data=f"issue_type_{1}")],
        [InlineKeyboardButton(text=ISSUE_TYPES[2], callback_data=f"issue_type_{2}")],
        [InlineKeyboardButton(text=ISSUE_TYPES[3], callback_data=f"issue_type_{3}")],
        [InlineKeyboardButton(text=ISSUE_TYPES[4], callback_data=f"issue_type_{4}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_issue_report")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = "🛠 *Report Issue*\n\nWhat type of issue are you experiencing?"
    
    await safe_edit_message(query, message_text, reply_markup=reply_markup)

async def handle_issue_type_selection(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, issue_type: int):
    """Handle issue type selection and prompt for description."""
    reporting_issue = context.user_data.get("reporting_issue", {})
    if not reporting_issue:
        await safe_edit_message(query, "❌ Issue reporting session expired.")
        return

    # Store the selected issue type
    issue_type_name = ISSUE_TYPES.get(issue_type, "Unknown")
    reporting_issue["issue_type"] = issue_type
    reporting_issue["issue_type_name"] = issue_type_name
    reporting_issue["step"] = "await_description"
    context.user_data["reporting_issue"] = reporting_issue

    await safe_edit_message(
        query,
        f"🛠 *Report Issue - {issue_type_name}*\n\n"
        "Please describe the issue you're experiencing with this media.\n\n"
        "💬 *Send your description as a message.*"
    )

async def show_manage_notifications_menu(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """Show notification management menu."""
    telegram_user_id = query.from_user.id
    
    # Which Overseerr user is selected?
    overseerr_telegram_user_id = context.user_data.get("overseerr_user_id")
    overseerr_user_name = context.user_data.get("overseerr_user_name", "Unknown User")

    if not overseerr_telegram_user_id:
        await query.edit_message_text("❌ No Overseerr user selected. Use /settings to pick a user first.")
        return

    # Fetch current notification settings from Overseerr
    current_settings = get_user_notification_settings(overseerr_telegram_user_id)
    if not current_settings:
        await query.edit_message_text(f"❌ Failed to retrieve notification settings for Overseerr user {overseerr_telegram_user_id}.")
        return

    # Extract relevant fields
    notification_types = current_settings.get("notificationTypes", {})
    telegram_bitmask = notification_types.get("telegram", 0)
    telegram_silent = current_settings.get("telegramSendSilently", False)

    # We interpret telegram_bitmask > 0 to mean "enabled"
    telegram_is_enabled = (telegram_bitmask != 0)

    # Build the display text (escape special Markdown characters in username)
    safe_user_name = escape_markdown(overseerr_user_name)
    
    text = (
        "🔔 *Notification Settings*\n"
        "Manage how Overseerr sends you updates via Telegram.\n\n"
        f"👤 *User Information:*\n"
        f"   - Name: *{safe_user_name}* (ID: `{overseerr_telegram_user_id}`)\n\n"
        "⚙️ *Current Telegram Settings:*\n"
        f"   - Notifications: {'*Enabled* ✅' if telegram_is_enabled else '*Disabled* ❌'}\n"
        f"   - Silent Mode: {'*On* 🤫' if telegram_silent else '*Off* 🔊'}\n\n"
        "🔄 *Actions:*\n"
    )

    keyboard = []
    
    # Toggle notification button
    if telegram_is_enabled:
        keyboard.append([InlineKeyboardButton("🔕 Disable Notifications", callback_data="toggle_user_notifications")])
    else:
        keyboard.append([InlineKeyboardButton("🔔 Enable Notifications", callback_data="toggle_user_notifications")])
    
    # Toggle silent mode button
    if telegram_silent:
        keyboard.append([InlineKeyboardButton("🔊 Disable Silent Mode", callback_data="toggle_user_silent")])
    else:
        keyboard.append([InlineKeyboardButton("🤫 Enable Silent Mode", callback_data="toggle_user_silent")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back to Settings", callback_data="back_to_settings")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await safe_edit_message(query, text, parse_mode="Markdown", reply_markup=reply_markup)

async def toggle_user_notifications(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """Toggle user notifications on/off."""
    overseerr_telegram_user_id = context.user_data.get("overseerr_user_id")
    
    if not overseerr_telegram_user_id:
        await query.edit_message_text("❌ No Overseerr user selected.")
        return

    # Get current settings
    current_settings = get_user_notification_settings(overseerr_telegram_user_id)
    if not current_settings:
        await query.edit_message_text("❌ Failed to retrieve notification settings.")
        return

    # Toggle telegram notifications
    notification_types = current_settings.get("notificationTypes", {})
    telegram_bitmask = notification_types.get("telegram", 0)
    
    # If enabled (> 0), disable (set to 0). If disabled (0), enable (set to same as email notifications)
    if telegram_bitmask > 0:
        new_bitmask = 0  # Disable
        action = "disabled"
    else:
        # Use same bitmask as email notifications, or 8190 as fallback (comprehensive notifications)
        email_bitmask = notification_types.get("email", 8190)
        new_bitmask = email_bitmask if email_bitmask > 0 else 8190
        action = "enabled"

    # Update the setting
    bot_info = await context.bot.get_me()
    success = update_telegram_settings_for_user(
        overseerr_user_id=overseerr_telegram_user_id,
        telegram_enabled=(new_bitmask > 0),
        telegram_bot_username=bot_info.username,
        telegram_bot_api=context.bot.token,
        telegram_chat_id=str(query.message.chat_id),
        telegram_send_silently=False,
        notification_types_bitmask=new_bitmask
    )
    
    if success:
        await query.answer(f"Notifications {action}!", show_alert=True)
        # Return to notification menu
        await show_manage_notifications_menu(query, context)
    else:
        await query.edit_message_text(f"❌ Failed to {action.replace('ed', '')} notifications.")

async def toggle_user_silent(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """Toggle silent mode on/off."""
    overseerr_telegram_user_id = context.user_data.get("overseerr_user_id")
    
    if not overseerr_telegram_user_id:
        await query.edit_message_text("❌ No Overseerr user selected.")
        return

    # Get current settings
    current_settings = get_user_notification_settings(overseerr_telegram_user_id)
    if not current_settings:
        await query.edit_message_text("❌ Failed to retrieve notification settings.")
        return

    # Toggle silent mode
    current_silent = current_settings.get("telegramSendSilently", False)
    new_silent = not current_silent
    action = "enabled" if new_silent else "disabled"

    # Get current notification settings for complete update
    notification_types = current_settings.get("notificationTypes", {})
    telegram_bitmask = notification_types.get("telegram", 0)

    # Update the setting with all required parameters
    bot_info = await context.bot.get_me()
    success = update_telegram_settings_for_user(
        overseerr_user_id=overseerr_telegram_user_id,
        telegram_enabled=current_settings.get("telegramEnabled", True),
        telegram_bot_username=bot_info.username,
        telegram_bot_api=context.bot.token,
        telegram_chat_id=str(query.message.chat_id),
        telegram_send_silently=new_silent,
        notification_types_bitmask=telegram_bitmask
    )
    
    if success:
        await query.answer(f"Silent mode {action}!", show_alert=True)
        # Return to notification menu
        await show_manage_notifications_menu(query, context)
    else:
        await query.edit_message_text(f"❌ Failed to {action.replace('ed', '')} silent mode.")

async def handle_group_mode_toggle(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """Handle group mode toggle."""
    telegram_user_id = query.from_user.id
    config = load_config()
    
    # Check if user is admin
    user_id_str = str(telegram_user_id)
    if not config["users"].get(user_id_str, {}).get("is_admin", False):
        await query.edit_message_text("❌ Only admins can toggle Group Mode.")
        return
    
    # Toggle group mode
    config["group_mode"] = not config["group_mode"]
    if not config["group_mode"]:
        config["primary_chat_id"] = {"chat_id": None, "message_thread_id": None}
        logger.info("Group Mode disabled, reset primary_chat_id to null")
    
    save_config(config)
    logger.info(f"Group Mode set to {config['group_mode']} by user {telegram_user_id}")
    
    # Return to settings menu
    from handlers.ui_handlers import show_settings_menu
    await show_settings_menu(query, context, is_admin=True)

async def handle_tv_anime_selection(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, selection: str):
    """Handle TV/Anime selection for multi-season requests."""
    from api.overseerr_api import request_media
    
    pending = context.user_data.pop("pending_multi_request", {})
    if not pending:
        await query.answer("Request expired or missing data.", show_alert=True)
        return
    
    # Map callback to Overseerr serverId & root folder
    SONARR_MAP = {
        "sonarr_multi_tv": {
            "serverId": 1,              # TV Sonarr service ID
            "rootFolder": "/tv"         # TV root folder
        },
        "sonarr_multi_anime": {
            "serverId": 0,              # Anime Sonarr service ID  
            "rootFolder": "/anime"      # Anime root folder
        }
    }
    chosen = SONARR_MAP[selection]

    # Get session info based on current mode
    session_cookie = None
    requested_by = None

    if CURRENT_MODE == BotMode.NORMAL:
        if "session_data" not in context.user_data:
            await query.edit_message_text("Please log in first (/settings).")
            return
        session_cookie = context.user_data["session_data"]["cookie"]
    elif CURRENT_MODE == BotMode.SHARED:
        shared_session = context.application.bot_data.get("shared_session")
        if not shared_session:
            await query.edit_message_text("Shared session expired.")
            return
        session_cookie = shared_session["cookie"]
    elif CURRENT_MODE == BotMode.API:
        requested_by = context.user_data.get("overseerr_user_id", 1)

    # Build payload with ALL seasons in one request
    extra_opts = {
        "serverId": chosen["serverId"],
        "rootFolderOverride": chosen["rootFolder"]
    }

    # Make ONE request with ALL selected seasons
    try:
        logger.info(f"Making request for {pending['title']} with seasons: {pending['seasons']}")
        success, msg = request_media(
            media_id=pending["media_id"],
            media_type=pending["media_type"],
            requested_by=requested_by,
            is4k=False,
            session_cookie=session_cookie,
            seasons=pending["seasons"],  # Pass the list of all seasons
            **extra_opts
        )
    except Exception as e:
        logger.error(f"Error in request_media: {e}")
        success, msg = False, f"Request failed with error: {str(e)}"

    # Clear the season selections
    context.user_data.pop("selected_seasons", [])

    # Create status message
    choice_type = "TV Series" if selection == "sonarr_multi_tv" else "Anime"
    season_text = f"Seasons {', '.join(map(str, sorted(pending['seasons'])))}"
    
    if success:
        status_message = (
            f"✅ **{pending['title']}** ({choice_type})\n"
            f"📥 {season_text} requested successfully!\n\n"
            f"{msg}"
        )
    else:
        status_message = (
            f"❌ **{pending['title']}** ({choice_type})\n"
            f"📥 Failed to request {season_text}\n\n"
            f"Error: {msg}"
        )
    
    await safe_edit_message(query, status_message)

async def handle_back_to_multi_selection(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to multi-season selection."""
    pending = context.user_data.get("pending_multi_request", {})
    if not pending:
        await query.edit_message_text("❌ No pending selection found.")
        return
    
    # Find the selected result and go back to media selection
    search_results = context.user_data.get("search_results", [])
    selected_result = None
    for result in search_results:
        if result.get('id') == pending['media_id']:
            selected_result = result
            break
    
    if selected_result:
        from handlers.ui_handlers import process_user_selection
        selection_index = search_results.index(selected_result)
        await process_user_selection(query, context, selection_index, query.from_user.id)

async def handle_season_request_individual(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, season_number: int):
    """Handle individual season request with TV/Anime choice."""
    selected_result = context.user_data.get("selected_result")
    if not selected_result:
        await query.edit_message_text("❌ No media selected.")
        return
    
    if selected_result["mediaType"] == "tv":
        # Store context for TV/Anime choice
        context.user_data["pending_request"] = {
            "media_id": selected_result["id"],
            "season": season_number,
            "title": selected_result["title"],
            "media_type": "tv"
        }

        # Build two-button inline keyboard for TV vs Anime choice
        keyboard = [
            [
                InlineKeyboardButton("📺 TV Series", callback_data="sonarr_tv"),
                InlineKeyboardButton("🎴 Anime", callback_data="sonarr_anime")
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_media_details")]
        ]
        
        await query.edit_message_caption(
            caption=f"*{selected_result['title']}*\n\nSeason {season_number}\n\n"
                   f"📁 Choose the content type for this request:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        # For movies, just make the request directly
        await handle_media_request(query, context, selected_result["id"], is4k=False)

async def handle_individual_tv_anime_selection(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle TV vs Anime selection for individual season requests."""
    pending = context.user_data.pop("pending_request", {})
    if not pending:
        await query.answer("Request expired or missing data.", show_alert=True)
        return

    # Map callback to Overseerr serverId & root folder
    SONARR_MAP = {
        "sonarr_tv": {
            "serverId": 1,              # Sonarr (TV) service ID
            "rootFolder": "/tv"         # TV root folder
        },
        "sonarr_anime": {
            "serverId": 0,              # Sonarr (Anime) service ID
            "rootFolder": "/anime"      # Anime root folder
        }
    }
    chosen = SONARR_MAP[data]

    # Get session info based on current mode
    session_cookie = None
    requested_by = None

    if CURRENT_MODE == BotMode.NORMAL:
        session_data = context.user_data.get("session_data")
        if session_data:
            session_cookie = session_data.get("cookie")
    elif CURRENT_MODE == BotMode.SHARED:
        shared_session = context.application.bot_data.get("shared_session")
        if shared_session:
            session_cookie = shared_session.get("cookie")
    elif CURRENT_MODE == BotMode.API:
        requested_by = context.user_data.get("overseerr_user_id", 1)

    # Build payload additions
    extra_opts = {
        "serverId": chosen["serverId"],
        "rootFolderOverride": chosen["rootFolder"]
    }

    # Submit request with overrides
    success, msg = request_media(
        media_id=pending["media_id"],
        media_type=pending["media_type"],
        requested_by=requested_by,
        is4k=False,
        session_cookie=session_cookie,
        seasons=pending["season"],
        **extra_opts
    )

    # Create proper status message for poster caption
    choice_type = "TV Series" if data == "sonarr_tv" else "Anime"
    status_msg = (
        f"*Request Status for {pending['title']}*\n"
        f"Season {pending['season']} ({choice_type})\n\n"
        f"{'✅ Request successful' if success else f'❌ {msg}'}"
    )
    
    await query.edit_message_caption(
        caption=status_msg,
        parse_mode="Markdown"
    )

async def handle_all_tv_anime_selection(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle TV vs Anime selection for 'All in 1080p/4K' requests."""
    pending = context.user_data.pop("pending_all_request", {})
    if not pending:
        await query.answer("Request expired or missing data.", show_alert=True)
        return

    # Map callback to Overseerr serverId & root folder
    SONARR_MAP = {
        "all_sonarr_tv": {
            "serverId": 1,              # Sonarr (TV) service ID
            "rootFolder": "/tv"         # TV root folder
        },
        "all_sonarr_anime": {
            "serverId": 0,              # Sonarr (Anime) service ID
            "rootFolder": "/anime"      # Anime root folder
        }
    }
    chosen = SONARR_MAP[data]

    # Get session info based on current mode
    session_cookie = None
    requested_by = None

    if CURRENT_MODE == BotMode.NORMAL:
        session_data = context.user_data.get("session_data")
        if session_data:
            session_cookie = session_data.get("cookie")
    elif CURRENT_MODE == BotMode.SHARED:
        shared_session = context.application.bot_data.get("shared_session")
        if shared_session:
            session_cookie = shared_session.get("cookie")
    elif CURRENT_MODE == BotMode.API:
        requested_by = context.user_data.get("overseerr_user_id", 1)

    # Build payload additions
    extra_opts = {
        "serverId": chosen["serverId"],
        "rootFolderOverride": chosen["rootFolder"]
    }

    # Submit request with overrides (all seasons)
    success, msg = request_media(
        media_id=pending["media_id"],
        media_type=pending["media_type"],
        requested_by=requested_by,
        is4k=pending["is4k"],
        session_cookie=session_cookie,
        seasons=None,  # None means all seasons
        **extra_opts
    )

    # Create proper status message for poster caption
    choice_type = "TV Series" if data == "all_sonarr_tv" else "Anime"
    quality = "4K" if pending["is4k"] else "1080p"
    status_msg = (
        f"*Request Status for {pending['title']}*\n"
        f"All Seasons in {quality} ({choice_type})\n\n"
        f"{'✅ Request successful' if success else f'❌ {msg}'}"
    )
    
    await query.edit_message_caption(
        caption=status_msg,
        parse_mode="Markdown"
    )

async def handle_request_more_seasons(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, media_id: int):
    """Handle 'Request More' button - show season selection for unavailable seasons only."""
    from api.overseerr_api import get_requestable_seasons
    
    try:
        # Get list of requestable seasons
        requestable_seasons = await get_requestable_seasons(media_id)
        
        if not requestable_seasons:
            await query.answer("No more seasons available to request.", show_alert=True)
            return
        
        # Find the selected result from search results
        search_results = context.user_data.get("search_results", [])
        selected_result = None
        for result in search_results:
            if result.get('id') == media_id:
                selected_result = result
                break
        
        if not selected_result:
            await query.edit_message_text("❌ Media not found.")
            return
        
        # Clear any previous season selections
        context.user_data.pop('selected_seasons', None)
        
        # Cache the requestable seasons so the toggle mechanism works
        context.user_data[f"seasons_{media_id}"] = requestable_seasons
        
        # Update the selected result in context
        context.user_data["selected_result"] = selected_result
        
        # Build media details message with only requestable seasons shown
        from handlers.ui_handlers import build_media_details_message
        media_text, keyboard = await build_media_details_message(selected_result, context, set(), request_more_mode=True)
        
        try:
            await query.edit_message_caption(
                caption=media_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Failed to edit message caption: {e}")
            # If editing fails, fall back to editing text
            try:
                await query.edit_message_text(
                    media_text,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e2:
                logger.error(f"Failed to edit message text: {e2}")
                await query.answer("Failed to update interface", show_alert=True)
                
    except Exception as e:
        logger.error(f"Error in handle_request_more_seasons: {e}")
        await query.answer("Failed to load more seasons", show_alert=True)

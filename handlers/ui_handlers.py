"""
UI handlers for settings menus, user management, and media display.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes

from config.config_manager import load_config, save_config, is_command_allowed, user_is_authorized
from config.constants import (
    CURRENT_MODE, BotMode, PASSWORD, OVERSEERR_API_URL, DEFAULT_POSTER_URL, ISSUE_TYPES
)
from session.session_manager import (
    load_user_session, get_saved_user_for_telegram_id, load_shared_session
)
from utils.telegram_utils import send_message, interpret_status, can_request_resolution, is_reportable
from api.overseerr_api import get_overseerr_users, user_can_request_4k, get_tv_show_seasons
from notifications.notification_manager import get_user_notification_settings

logger = logging.getLogger(__name__)

async def show_settings_menu(update_or_query, context: ContextTypes.DEFAULT_TYPE, is_admin=False):
    """
    Displays the settings menu tailored for users or admins with conditional buttons.
    In Shared mode, only the admin can access settings. Manage Notifications button is only shown if an Overseerr user is selected.
    """
    if isinstance(update_or_query, Update):
        telegram_user_id = update_or_query.effective_user.id
        chat_id = update_or_query.effective_chat.id
        message_thread_id = getattr(update_or_query.message, "message_thread_id", None)
    elif isinstance(update_or_query, CallbackQuery):
        telegram_user_id = update_or_query.from_user.id
        chat_id = update_or_query.message.chat_id
        message_thread_id = getattr(update_or_query.message, "message_thread_id", None)
    else:
        logger.error("Invalid argument type passed to show_settings_menu")
        return

    config = load_config()

    # Check if command/query is allowed
    if not is_command_allowed(chat_id, message_thread_id, config, telegram_user_id):
        return

    user_id_str = str(telegram_user_id)
    user = config["users"].get(user_id_str, {})
    is_admin = user.get("is_admin", False)

    # In Shared mode, only the admin can access settings
    if CURRENT_MODE == BotMode.SHARED and not is_admin:
        logger.info(f"Non-admin {telegram_user_id} attempted to access settings in Shared mode; ignoring.")
        return

    # Restrict access if unauthorized
    if PASSWORD and not user_is_authorized(telegram_user_id):
        await send_message(
            context,
            chat_id,
            "🔒 *Access Denied*\nPlease enter the bot's password via /start to access settings.",
            message_thread_id=message_thread_id
        )
        return

    # Refresh user data based on CURRENT_MODE
    context.user_data.pop("overseerr_telegram_user_id", None)
    context.user_data.pop("overseerr_user_name", None)
    context.user_data.pop("session_data", None)

    if CURRENT_MODE == BotMode.NORMAL:
        session_data = load_user_session(telegram_user_id)
        if session_data and "cookie" in session_data:
            context.user_data["session_data"] = session_data
            context.user_data["overseerr_telegram_user_id"] = session_data["overseerr_telegram_user_id"]
            context.user_data["overseerr_user_name"] = session_data.get("overseerr_user_name", "Unknown")
            logger.info(f"Loaded Normal mode session for user {telegram_user_id}: {session_data['overseerr_telegram_user_id']}")
    elif CURRENT_MODE == BotMode.API:
        overseerr_user_id, overseerr_user_name = get_saved_user_for_telegram_id(telegram_user_id)
        if overseerr_user_id:
            context.user_data["overseerr_telegram_user_id"] = overseerr_user_id
            context.user_data["overseerr_user_name"] = overseerr_user_name
            logger.info(f"Loaded API mode user selection for {telegram_user_id}: {overseerr_user_id} ({overseerr_user_name})")
    elif CURRENT_MODE == BotMode.SHARED:
        shared_session = load_shared_session()
        if shared_session and "cookie" in shared_session:
            context.application.bot_data["shared_session"] = shared_session
            context.user_data["overseerr_telegram_user_id"] = shared_session["overseerr_telegram_user_id"]
            context.user_data["overseerr_user_name"] = shared_session.get("overseerr_user_name", "Shared User")
            logger.info(f"Loaded Shared mode session for user {telegram_user_id}: {shared_session['overseerr_telegram_user_id']}")

    # Get current Overseerr user info (if any)
    overseerr_user_name = context.user_data.get("overseerr_user_name", "None selected")
    overseerr_telegram_user_id = context.user_data.get("overseerr_telegram_user_id", "N/A")
    user_info = f"{overseerr_user_name} ({overseerr_telegram_user_id}) ✅" if overseerr_telegram_user_id != "N/A" else "Not set ❌"

    group_mode_status = "🟢 On" if config["group_mode"] else "🔴 Off"

    if is_admin:
        mode_symbols = {
            BotMode.NORMAL: "🌟",
            BotMode.API: "🔑",
            BotMode.SHARED: "👥"
        }
        mode_symbol = mode_symbols.get(CURRENT_MODE, "❓")
        text = (
            "⚙️ *Admin Settings*\n\n"
            f"🤖 *Bot Mode:* {mode_symbol} *{CURRENT_MODE.value.capitalize()}*\n"
            f"👤 *Current User:* {user_info}\n"
            f"👥 *Group Mode:* {group_mode_status}\n\n"
            "Select an option below to manage your settings:\n"
        )
    else:
        text = (
            "⚙️ *Settings - Current User:*\n\n"
            f"👤 {user_info}\n\n"
            "Select an option below to manage your settings:\n"
        )

    keyboard = []
    account_buttons = []
    if CURRENT_MODE == BotMode.API:
        account_buttons.append(InlineKeyboardButton("🔄 Change User", callback_data="change_user"))
    elif CURRENT_MODE == BotMode.NORMAL:
        if context.user_data.get("session_data"):
            account_buttons.append(InlineKeyboardButton("🔓 Logout", callback_data="logout"))
        else:
            account_buttons.append(InlineKeyboardButton("🔑 Login", callback_data="login"))
    elif CURRENT_MODE == BotMode.SHARED and is_admin:
        if context.application.bot_data.get("shared_session"):
            account_buttons.append(InlineKeyboardButton("🔓 Logout", callback_data="logout"))
        else:
            account_buttons.append(InlineKeyboardButton("🔑 Login", callback_data="login"))
    if account_buttons:
        keyboard.append(account_buttons)

    if is_admin:
        keyboard.extend([
            [InlineKeyboardButton("🔧 Change Mode", callback_data="mode_select")],
            [InlineKeyboardButton(f"👥 Group Mode: {group_mode_status}", callback_data="toggle_group_mode")],
            [InlineKeyboardButton("👤 Manage Users", callback_data="manage_users")]
        ])
    
    # Show Manage Notifications only if an Overseerr user is selected
    if overseerr_telegram_user_id != "N/A":
        keyboard.append([InlineKeyboardButton("🔔 Manage Notifications", callback_data="manage_notifications")])

    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_settings")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if isinstance(update_or_query, Update):
        await send_message(context, chat_id, text, reply_markup=reply_markup, message_thread_id=message_thread_id)
    else:
        await update_or_query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)

async def display_results_with_buttons(update, context: ContextTypes.DEFAULT_TYPE, results, offset=0, search_query="", telegram_user_id=None):
    """
    Display search results with pagination buttons.
    """
    if not results:
        await update.message.reply_text("No results to display.")
        return

    total_results = len(results)
    results_to_show = results[offset:offset + 5]

    # Just show the header - no duplicate text list
    results_text = f"🔍 *Search results for:* {search_query}\n\n📊 *Showing {offset + 1}-{min(offset + 5, total_results)} of {total_results} results*\n\nSelect a result below:"

    # Build keyboard
    keyboard = []
    for idx, result in enumerate(results_to_show):
        button_text = f"{offset + idx + 1}. {result['title']} ({result['year']})"
        callback_data = f"select_{offset + idx}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    # Navigation buttons
    nav_buttons = []
    if offset > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Back", callback_data=f"page_{offset - 5}"))
    
    nav_buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="cancel_search"))
    
    if offset + 5 < total_results:
        nav_buttons.append(InlineKeyboardButton("➡️ More", callback_data=f"page_{offset + 5}"))
    
    keyboard.append(nav_buttons)
    reply_markup = InlineKeyboardMarkup(keyboard)

    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(
            results_text, parse_mode="Markdown", reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            results_text, parse_mode="Markdown", reply_markup=reply_markup
        )

def build_media_details_message(result, context: ContextTypes.DEFAULT_TYPE, selected_seasons=None):
    """
    Build media details message text and keyboard.
    Returns tuple of (media_text, keyboard).
    """
    if selected_seasons is None:
        selected_seasons = set()
    
    # Build detailed media info
    media_text = f"🎬 *{result['title']}* ({result['year']})\n\n"
    media_text += f"📺 *Type:* {result['mediaType'].upper()}\n"
    media_text += f"🗓 *Release:* {result.get('release_date_full', 'Unknown')}\n\n"
    media_text += f"📖 *Description:*\n{result['description'][:300]}{'...' if len(result['description']) > 300 else ''}\n\n"
    
    # Status information
    hd_status = interpret_status(result['status_hd'])
    k4_status = interpret_status(result['status_4k'])
    media_text += f"📊 *Availability:*\n"
    media_text += f"   • HD (1080p): {hd_status}\n"
    media_text += f"   • 4K (UHD): {k4_status}\n"

    # Build action buttons
    keyboard = []
    back_button = InlineKeyboardButton("⬅️ Back", callback_data="back_to_results")

    overseerr_telegram_user_id = context.user_data.get("overseerr_telegram_user_id")
    if overseerr_telegram_user_id:
        # Request buttons
        if can_request_resolution(result['status_hd']):
            if result['mediaType'] == 'tv':
                # Get seasons from cache
                seasons = context.user_data.get(f"seasons_{result['id']}")
                if seasons and len(seasons) > 1:
                    # Multiple seasons - show season selection
                    for sn in seasons:
                        is_selected = sn in selected_seasons
                        emoji = "✅" if is_selected else "⭕"
                        keyboard.append([
                            InlineKeyboardButton(f"{emoji} Season {sn}", 
                                               callback_data=f"toggle_season_{result['id']}_{sn}")
                        ])
                    if selected_seasons:
                        keyboard.append([
                            InlineKeyboardButton("📥 Request Selected Seasons", 
                                               callback_data=f"finalize_seasons_{result['id']}")
                        ])
                
                btn_1080p = InlineKeyboardButton("📥 All in 1080p", callback_data=f"confirm_1080p_{result['id']}")
            else:
                btn_1080p = InlineKeyboardButton("📥 1080p", callback_data=f"confirm_1080p_{result['id']}")
            
            keyboard.append([btn_1080p])

        if can_request_resolution(result['status_4k']) and user_can_request_4k(overseerr_telegram_user_id, result['mediaType']):
            if result['mediaType'] == 'tv':
                btn_4k = InlineKeyboardButton("📥 All in 4K", callback_data=f"confirm_4k_{result['id']}")
            else:
                btn_4k = InlineKeyboardButton("📥 4K", callback_data=f"confirm_4k_{result['id']}")
            keyboard.append([btn_4k])

        # Report issue button
        if is_reportable(result['status_hd']) or is_reportable(result['status_4k']):
            overseerr_media_id = result.get('overseerr_id')
            if overseerr_media_id:
                report_button = InlineKeyboardButton("🛠 Report Issue", callback_data=f"report_{overseerr_media_id}")
                keyboard.append([report_button])

    keyboard.append([back_button])
    return media_text, keyboard

async def process_user_selection(update_or_query, context: ContextTypes.DEFAULT_TYPE, selection_index, telegram_user_id):
    """
    Process when user selects a specific media item from search results.
    Can be called with either Update (from command) or CallbackQuery (from button).
    """
    # Handle both Update and CallbackQuery inputs
    if hasattr(update_or_query, 'callback_query'):
        # It's an Update object
        query = update_or_query.callback_query
        await query.answer()
    else:
        # It's already a CallbackQuery
        query = update_or_query
        await query.answer()
    
    search_results = context.user_data.get("search_results", [])
    if selection_index >= len(search_results):
        await query.edit_message_text("❌ Invalid selection. Please search again.")
        return

    result = search_results[selection_index]
    context.user_data["selected_result"] = result

    # Clear any previous season selections when viewing a new media item
    previous_result = context.user_data.get("selected_result")
    if not previous_result or previous_result.get('id') != result.get('id'):
        context.user_data.pop('selected_seasons', None)

    # Load authentication data based on current mode
    config = load_config()
    user_id_str = str(telegram_user_id)
    user = config["users"].get(user_id_str, {})

    # Initialize user authentication data
    context.user_data.pop("overseerr_telegram_user_id", None)
    context.user_data.pop("overseerr_user_name", None)
    context.user_data.pop("session_data", None)

    if CURRENT_MODE == BotMode.NORMAL:
        session_data = load_user_session(telegram_user_id)
        if session_data and "cookie" in session_data:
            context.user_data["session_data"] = session_data
            context.user_data["overseerr_telegram_user_id"] = session_data["overseerr_telegram_user_id"]
            context.user_data["overseerr_user_name"] = session_data.get("overseerr_user_name", "Unknown")
    elif CURRENT_MODE == BotMode.API:
        overseerr_user_id, overseerr_user_name = get_saved_user_for_telegram_id(telegram_user_id)
        if overseerr_user_id:
            context.user_data["overseerr_telegram_user_id"] = overseerr_user_id
            context.user_data["overseerr_user_name"] = overseerr_user_name
    elif CURRENT_MODE == BotMode.SHARED:
        shared_session = load_shared_session()
        if shared_session and "cookie" in shared_session:
            context.application.bot_data["shared_session"] = shared_session
            context.user_data["overseerr_telegram_user_id"] = shared_session["overseerr_telegram_user_id"]
            context.user_data["overseerr_user_name"] = shared_session.get("overseerr_user_name", "Shared User")

    # Cache seasons data for TV shows if not already cached
    if result['mediaType'] == 'tv':
        seasons_key = f"seasons_{result['id']}"
        if seasons_key not in context.user_data:
            seasons = await get_tv_show_seasons(result['id'])
            if seasons and len(seasons) > 1:
                context.user_data[seasons_key] = seasons

    # Get selected seasons for display
    selected_seasons = set(context.user_data.get('selected_seasons', []))
    
    # Build media details using the new function
    media_text, keyboard = build_media_details_message(result, context, selected_seasons)
    
    # Check if user is authenticated - if not, show authentication message
    overseerr_telegram_user_id = context.user_data.get("overseerr_telegram_user_id")
    if not overseerr_telegram_user_id:
        auth_message = "🔐 *Authentication Required*\n\n"
        auth_message += f"To request *{result['title']}*, please authenticate first using /settings"
        
        keyboard = [[InlineKeyboardButton("⚙️ Settings", callback_data="show_settings")]]
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_results")])
        media_text += f"\n\n{auth_message}"
    
    poster_url = f"https://image.tmdb.org/t/p/w500{result['poster']}" if result['poster'] else DEFAULT_POSTER_URL
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send media info with poster using send_photo
    try:
        # Check if we're editing an existing message or creating new one
        if hasattr(query, 'message') and query.message.photo:
            # Edit existing photo message caption
            msg = await query.edit_message_caption(
                caption=media_text, parse_mode="Markdown", reply_markup=reply_markup
            )
        else:
            # Delete the old message and send new photo message
            try:
                await query.message.delete()
            except:
                pass  # Ignore if deletion fails
            
            msg = await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=poster_url,
                caption=media_text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        context.user_data["media_message_id"] = msg.message_id
    except Exception as e:
        logger.error(f"Failed to send photo with media details: {e}")
        # Fallback to text message if photo fails
        try:
            # Delete the old message first
            try:
                await query.message.delete()
            except:
                pass
            
            msg = await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=media_text,
                parse_mode="Markdown", 
                reply_markup=reply_markup
            )
            context.user_data["media_message_id"] = msg.message_id
        except Exception as e2:
            logger.error(f"Failed to send message with media details: {e2}")
            await query.message.reply_text(
                media_text, parse_mode="Markdown", reply_markup=reply_markup
            )

async def handle_change_user(update_or_query, context: ContextTypes.DEFAULT_TYPE, is_initial=False, offset=0):
    """
    Display a paginated list of Overseerr users for API mode user selection.
    """
    if isinstance(update_or_query, Update):
        telegram_user_id = update_or_query.effective_user.id
        chat_id = update_or_query.effective_chat.id
        message_thread_id = getattr(update_or_query.message, "message_thread_id", None)
    else:  # CallbackQuery
        telegram_user_id = update_or_query.from_user.id
        chat_id = update_or_query.message.chat_id
        message_thread_id = getattr(update_or_query.message, "message_thread_id", None)

    config = load_config()
    if not is_command_allowed(chat_id, message_thread_id, config, telegram_user_id):
        return

    if CURRENT_MODE != BotMode.API:
        error_text = "User selection is only available in API Mode."
        if isinstance(update_or_query, Update):
            await send_message(context, chat_id, error_text, message_thread_id=message_thread_id)
        else:
            await update_or_query.edit_message_text(error_text)
        return

    users = get_overseerr_users()
    if not users:
        error_text = "❌ Unable to fetch users from Overseerr. Please check your API configuration."
        if isinstance(update_or_query, Update):
            await send_message(context, chat_id, error_text, message_thread_id=message_thread_id)
        else:
            await update_or_query.edit_message_text(error_text)
        return

    page_size = 8
    total_users = len(users)
    current_users = users[offset:offset + page_size]

    current_user_id, current_user_name = get_saved_user_for_telegram_id(telegram_user_id)
    
    if is_initial and current_user_id:
        message_text = (
            f"🔄 *Change Overseerr User*\n\n"
            f"Current: *{current_user_name}* (ID: {current_user_id})\n\n"
            f"Select a new user from the list below:\n"
        )
    else:
        message_text = f"👤 *Select Overseerr User*\n\nChoose from {total_users} available users:\n"

    keyboard = []
    for user in current_users:
        user_id = user["id"]
        display_name = user.get("displayName") or user.get("email", f"User {user_id}")
        
        # Mark current user
        if user_id == current_user_id:
            button_text = f"✅ {display_name} (Current)"
        else:
            button_text = display_name
            
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_user_{user_id}")])

    # Navigation buttons
    nav_buttons = []
    if offset > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Back", callback_data=f"users_page_{offset - page_size}"))
    if offset + page_size < total_users:
        nav_buttons.append(InlineKeyboardButton("➡️ More", callback_data=f"users_page_{offset + page_size}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_user_selection")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if isinstance(update_or_query, Update):
        await send_message(context, chat_id, message_text, reply_markup=reply_markup, message_thread_id=message_thread_id)
    elif isinstance(update_or_query, CallbackQuery):
        await update_or_query.edit_message_text(message_text, parse_mode="Markdown", reply_markup=reply_markup)

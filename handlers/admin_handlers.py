"""
Admin command handlers for request approval functionality.
Handles admin-only commands and callback queries for request management.
Enhanced with better error handling and improved user experience.
"""
import logging
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.config_manager import load_config
from api.request_manager import RequestManager
from utils.telegram_utils import send_message
from utils.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


async def send_pending_requests_with_posters(bot, chat_id, pending_requests, context=None):
    """Send pending requests as individual photo messages with posters and details"""
    # Store message IDs for potential cleanup
    message_ids = []
    
    if not pending_requests:
        no_requests_msg = await bot.send_message(
            chat_id,
            "🎬 *No pending requests found*\n\nAll caught up! No requests need approval at the moment.",
            parse_mode='Markdown'
        )
        if context:
            context.user_data['pending_message_ids'] = [no_requests_msg.message_id]
        return

    # Send header message
    header_text = f"🎬 *Admin Review Required*\n\n**{len(pending_requests)} pending request(s)** need your approval:"
    header_msg = await bot.send_message(chat_id, header_text, parse_mode='Markdown')
    message_ids.append(header_msg.message_id)

    # Get enhanced media details for each request
    request_manager = RequestManager()
    
    # Process each request individually with enhanced details
    for i, request in enumerate(pending_requests):
        try:
            # Get enhanced request details with poster
            req_info = request_manager.get_media_details_from_request(request)
            
            # Get the media emoji (fix: use 'media_type' key from RequestManager)
            media_type = req_info.get('media_type', 'unknown')
            emoji = get_media_emoji(media_type)
            
            # Build caption with rich details (fix: extract requester info properly)
            title = req_info.get('title', 'Unknown Title')
            
            # Extract requester from the nested structure
            requester_info = req_info.get('requested_by', {})
            requester = requester_info.get('display_name', 'Unknown User')
            
            request_id = req_info.get('request_id', 'N/A')
            
            caption = f"{emoji} **{title}**\n"
            caption += f"👤 Requested by: {requester}\n"
            caption += f"🆔 Request ID: {request_id}\n"
            
            # Add extra details if available
            if 'rating' in req_info and req_info['rating']:
                caption += f"⭐ Rating: {req_info['rating']}\n"
            if 'runtime' in req_info and req_info['runtime']:
                caption += f"⏱️ Runtime: {req_info['runtime']} min\n"
            if 'genres' in req_info and req_info['genres']:
                genres_text = ', '.join(req_info['genres'][:3])  # Limit to 3 genres
                caption += f"🎭 Genres: {genres_text}\n"
            if 'overview' in req_info and req_info['overview']:
                # Truncate overview to keep caption readable
                overview = req_info['overview']
                if len(overview) > 200:
                    overview = overview[:197] + "..."
                caption += f"\n📋 {overview}"

            # Create buttons for this specific request
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_{request_id}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{request_id}")
                ]
            ])

            # Send photo with poster if available
            poster_url = req_info.get('poster_url')
            if poster_url:
                msg = await bot.send_photo(
                    chat_id,
                    photo=poster_url,
                    caption=caption,
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
                message_ids.append(msg.message_id)
            else:
                # Fallback to text message if no poster
                msg = await bot.send_message(
                    chat_id,
                    f"📷 *No poster available*\n\n{caption}",
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
                message_ids.append(msg.message_id)
        
        except Exception as e:
            logger.error(f"Error sending request #{i+1} (ID: {request.get('id', 'unknown')}): {e}")
            # Send a fallback message for this request using original request data
            request_id = request.get('id', 'N/A')
            
            # Extract basic info from original request
            media = request.get('media', {})
            title = media.get('title', 'Unknown Title')
            media_type = media.get('mediaType', 'unknown')  # Fix: use 'mediaType' from API
            emoji = get_media_emoji(media_type)
            
            # Get requester name from the request (fix: proper extraction)
            requestedBy = request.get('requestedBy', {})
            requester = requestedBy.get('displayName', requestedBy.get('plexUsername', 'Unknown'))
            
            fallback_text = f"{emoji} **{title}**\n"
            fallback_text += f"👤 Requested by: {requester}\n"
            fallback_text += f"🆔 Request ID: {request_id}\n"
            fallback_text += f"\n⚠️ *Unable to load enhanced details*"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_{request_id}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{request_id}")
                ]
            ])
            fallback_msg = await bot.send_message(chat_id, fallback_text, parse_mode='Markdown', reply_markup=keyboard)
            message_ids.append(fallback_msg.message_id)

    # Send footer with refresh and cancel buttons
    footer_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Refresh List", callback_data="admin_refresh_requests"),
            InlineKeyboardButton("❌ Cancel", callback_data="admin_cancel_requests")
        ]
    ])
    
    footer_text = "✨ Review complete! Use refresh to update the list or cancel to clear the chat."
    footer_msg = await bot.send_message(chat_id, footer_text, reply_markup=footer_keyboard)
    message_ids.append(footer_msg.message_id)
    
    # Store message IDs in context for cleanup
    if context:
        context.user_data['pending_message_ids'] = message_ids


async def pending_requests_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /pending command to display pending requests for admin approval.
    Admin-only command that works only in private chats.
    """
    try:
        telegram_user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        chat_type = update.effective_chat.type
        
        # Verify admin permissions
        if not is_admin_user(telegram_user_id):
            await send_message(
                context, 
                chat_id, 
                "❌ **Access denied.** This command is restricted to administrators only."
            )
            return
        
        # Verify private chat
        if chat_type != 'private':
            await send_message(
                context,
                chat_id,
                "🔒 **Private chat required.** Please use this command in a private chat with the bot for security."
            )
            return
        
        # Show loading message with enhanced UX
        loading_message = await context.bot.send_message(
            chat_id=chat_id,
            text="🔄 **Fetching pending requests...** This may take a moment.",
            parse_mode='Markdown'
        )
        
        # Fetch pending requests with enhanced error handling
        try:
            request_manager = RequestManager()
        except ValueError as e:
            logger.error(f"Failed to initialize RequestManager: {e}")
            error_message = (
                "❌ **Configuration Error**\n\n"
                "The Overseerr API configuration is missing or invalid. "
                "Please ensure the following environment variables are properly set:\n"
                "• `OVERSEERR_API_URL` - Your Overseerr server URL\n"
                "• `OVERSEERR_API_KEY` - Your Overseerr API key\n\n"
                "Contact your administrator if this issue persists."
            )
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=loading_message.message_id,
                text=error_message,
                parse_mode='Markdown'
            )
            return
        
        # Get pending requests with improved error feedback
        try:
            pending_result = request_manager.get_pending_requests()
            
            # Handle both tuple and dict returns for backward compatibility
            if isinstance(pending_result, tuple):
                success, pending_data, error_message = pending_result
                if not success:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=loading_message.message_id,
                        text=f"❌ **API Request Failed**\n\n{error_message}\n\nPlease try again or contact your administrator if the issue persists.",
                        parse_mode='Markdown'
                    )
                    return
            else:
                # Backward compatibility with old format
                pending_data = pending_result
                if not pending_data:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=loading_message.message_id,
                        text="❌ **Connection Failed**\n\nUnable to connect to Overseerr API. Please check:\n• Overseerr server is running and accessible\n• API URL is correct and reachable\n• API key has valid permissions\n• Network connectivity is stable",
                        parse_mode='Markdown'
                    )
                    return
        
        except Exception as e:
            logger.error(f"Unexpected error in pending_requests_command: {e}")
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=loading_message.message_id,
                text="❌ **Unexpected Error**\n\nAn unexpected error occurred while fetching pending requests. Please try again later.",
                parse_mode='Markdown'
            )
            return
        
        results = pending_data.get('results', [])
        
        # Delete the loading message
        await context.bot.delete_message(chat_id=chat_id, message_id=loading_message.message_id)
        
        # Send requests using the new poster-based layout
        await send_pending_requests_with_posters(context.bot, chat_id, results, context)
        
    except Exception as e:
        logger.error(f"Error in pending_requests_command: {e}")
        # Try to send error message
        try:
            await send_message(
                context,
                chat_id,
                "❌ **Unexpected error occurred.** Please try again later."
            )
        except:
            # Fallback if send_message also fails
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ **Unexpected error occurred.** Please try again later."
            )


async def handle_admin_approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle callback queries for admin approval actions.
    Processes approve/reject button clicks and confirmation dialogs.
    """
    try:
        query = update.callback_query
        telegram_user_id = query.from_user.id
        callback_data = query.data
        
        # Verify admin permissions
        if not is_admin_user(telegram_user_id):
            await query.answer("❌ Admin access required", show_alert=True)
            return
        
        # Parse callback data
        if callback_data.startswith('admin_approve_'):
            request_id = int(callback_data.replace('admin_approve_', ''))
            await handle_approve_request(query, context, request_id)
            
        elif callback_data.startswith('admin_reject_'):
            request_id = int(callback_data.replace('admin_reject_', ''))
            await handle_reject_request(query, context, request_id)
            
        elif callback_data.startswith('admin_confirm_approve_'):
            request_id = int(callback_data.replace('admin_confirm_approve_', ''))
            await execute_approve_request(query, context, request_id)
            
        elif callback_data.startswith('admin_confirm_reject_'):
            request_id = int(callback_data.replace('admin_confirm_reject_', ''))
            await execute_reject_request(query, context, request_id)
            
        elif callback_data == 'admin_pending_all':
            # Refresh pending list
            await refresh_pending_requests(query, context)
            
        elif callback_data == 'admin_refresh_requests':
            # Refresh pending list (same as admin_pending_all)
            await refresh_pending_requests(query, context)
            
        elif callback_data == 'admin_cancel_requests':
            # Cancel and clear the chat
            await cancel_pending_requests(query, context)
            
        elif callback_data.startswith('admin_cancel_'):
            # Cancel confirmation dialog - delete message and send confirmation
            await query.message.delete()
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text="⚪ **Action cancelled.** No changes made.",
                parse_mode='Markdown'
            )
            await query.answer("❌ Action cancelled")
            
        else:
            await query.answer("❌ Unknown action", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error handling admin callback: {e}")
        await query.answer("❌ Error processing request", show_alert=True)


async def handle_approve_request(query, context: ContextTypes.DEFAULT_TYPE, request_id: int):
    """Show confirmation dialog for request approval."""
    try:
        # Get request details using the raw API first
        request_manager = RequestManager()
        request_details = request_manager.get_request_details(request_id)
        
        if not request_details:
            await query.answer("❌ Request not found", show_alert=True)
            return
        
        # Use our enhanced media details extraction for proper title and info
        enhanced_details = request_manager.get_media_details_from_request(request_details)
        
        # Extract request information from enhanced details
        title = enhanced_details.get('title', 'Unknown Title')
        media_type = enhanced_details.get('media_type', 'unknown')
        
        # Get emoji for media type
        emoji = get_media_emoji(media_type)
        
        # Get requester info
        requester_info = enhanced_details.get('requested_by', {})
        requester = requester_info.get('display_name', 'Unknown User')
        
        # Quality info (keep original logic for 4K detection)
        quality = '4K' if request_details.get('is4k', False) else 'HD'
        
        # Create confirmation message with proper title and emoji
        confirmation_text = f"""⚠️ **Confirm Approval**

{emoji} **{title}** ({quality})
👤 **Requested by:** {requester}
🆔 **Request ID:** {request_id}

This will immediately approve the request in Overseerr.

Are you sure you want to proceed?"""
        
        # Create confirmation keyboard
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes, Approve", 
                                   callback_data=f"admin_confirm_approve_{request_id}"),
                InlineKeyboardButton("❌ Cancel", 
                                   callback_data=f"admin_cancel_{request_id}")
            ]
        ]

        # Delete the original photo message and send confirmation as text message
        # This works better than trying to edit photo message text
        await query.message.delete()
        
        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text=confirmation_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        await query.answer()
        
    except Exception as e:
        logger.error(f"Error showing approval confirmation: {e}")
        await query.answer("❌ Error showing confirmation", show_alert=True)


async def handle_reject_request(query, context: ContextTypes.DEFAULT_TYPE, request_id: int):
    """Show confirmation dialog for request rejection."""
    try:
        # Get request details using the raw API first
        request_manager = RequestManager()
        request_details = request_manager.get_request_details(request_id)
        
        if not request_details:
            await query.answer("❌ Request not found", show_alert=True)
            return
        
        # Use our enhanced media details extraction for proper title and info
        enhanced_details = request_manager.get_media_details_from_request(request_details)
        
        # Extract request information from enhanced details
        title = enhanced_details.get('title', 'Unknown Title')
        media_type = enhanced_details.get('media_type', 'unknown')
        
        # Get emoji for media type
        emoji = get_media_emoji(media_type)
        
        # Get requester info
        requester_info = enhanced_details.get('requested_by', {})
        requester = requester_info.get('display_name', 'Unknown User')
        
        # Quality info (keep original logic for 4K detection)
        quality = '4K' if request_details.get('is4k', False) else 'HD'
        
        # Create confirmation message with proper title and emoji
        confirmation_text = f"""⚠️ **Confirm Rejection**

{emoji} **{title}** ({quality})
👤 **Requested by:** {requester}
🆔 **Request ID:** {request_id}

This will decline the request in Overseerr.

Are you sure you want to proceed?"""
        
        # Create confirmation keyboard
        keyboard = [
            [
                InlineKeyboardButton("❌ Yes, Reject", 
                                   callback_data=f"admin_confirm_reject_{request_id}"),
                InlineKeyboardButton("⚪ Cancel", 
                                   callback_data=f"admin_cancel_{request_id}")
            ]
        ]
        
        # Delete the original photo message and send confirmation as text message
        # This works better than trying to edit photo message text
        await query.message.delete()
        
        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text=confirmation_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        await query.answer()
        
    except Exception as e:
        logger.error(f"Error showing rejection confirmation: {e}")
        await query.answer("❌ Error showing confirmation", show_alert=True)


async def execute_approve_request(query, context: ContextTypes.DEFAULT_TYPE, request_id: int):
    """Execute the approval of a request."""
    try:
        request_manager = RequestManager()
        result = request_manager.approve_request(request_id)
        
        if result:
            success_text = f"""✅ **Request Approved Successfully!**

The request has been approved in Overseerr and will be processed shortly.

Request ID: #{request_id}"""
            
            # Create keyboard to view pending requests
            keyboard = [[InlineKeyboardButton("📋 View Pending Requests", callback_data="admin_pending_all")]]
            
            await query.edit_message_text(
                text=success_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            await query.answer("✅ Request approved!")
            
        else:
            await query.edit_message_text(
                text="❌ **Approval Failed**\n\nUnable to approve the request. Please check the Overseerr connection and try again.",
                parse_mode='Markdown'
            )
            await query.answer("❌ Approval failed", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error executing approval: {e}")
        await query.answer("❌ Error processing approval", show_alert=True)


async def execute_reject_request(query, context: ContextTypes.DEFAULT_TYPE, request_id: int):
    """Execute the rejection of a request."""
    try:
        request_manager = RequestManager()
        result = request_manager.reject_request(request_id)
        
        if result:
            success_text = f"""❌ **Request Rejected Successfully**

The request has been declined in Overseerr.

Request ID: #{request_id}"""
            
            # Create keyboard to view pending requests
            keyboard = [[InlineKeyboardButton("📋 View Pending Requests", callback_data="admin_pending_all")]]
            
            await query.edit_message_text(
                text=success_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            await query.answer("❌ Request rejected")
            
        else:
            await query.edit_message_text(
                text="❌ **Rejection Failed**\n\nUnable to reject the request. Please check the Overseerr connection and try again.",
                parse_mode='Markdown'
            )
            await query.answer("❌ Rejection failed", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error executing rejection: {e}")
        await query.answer("❌ Error processing rejection", show_alert=True)


async def refresh_pending_requests(query, context: ContextTypes.DEFAULT_TYPE):
    """Refresh the pending requests display with enhanced error handling."""
    try:
        # Show loading state
        await query.edit_message_text("🔄 **Refreshing pending requests...** Please wait.")
        
        # Fetch fresh data
        try:
            request_manager = RequestManager()
            pending_result = request_manager.get_pending_requests()
            
            # Handle both tuple and dict returns for backward compatibility
            if isinstance(pending_result, tuple):
                success, pending_data, error_message = pending_result
                if not success:
                    await query.edit_message_text(
                        f"❌ **API Request Failed**\n\n{error_message}\n\nPlease try again or contact your administrator."
                    )
                    return
            else:
                # Backward compatibility with old format
                pending_data = pending_result
                if not pending_data:
                    await query.edit_message_text(
                        "❌ **API Connection Error**\n\nCannot connect to Overseerr API. Please check:\n• Overseerr server is running\n• API URL is correct\n• API key has proper permissions\n• Network connectivity"
                    )
                    return
                
        except Exception as e:
            logger.error(f"Error fetching data during refresh: {e}")
            await query.edit_message_text(
                "❌ **Error during refresh**\n\nPlease try again later."
            )
            return
        
        results = pending_data.get('results', [])
        
        # Get chat info and stored message IDs
        chat_id = query.message.chat.id
        message_ids = context.user_data.get('pending_message_ids', [])
        
        # Delete ALL previous pending request messages (like cancel does)
        deleted_count = 0
        if message_ids:
            for message_id in message_ids:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                    deleted_count += 1
                except Exception as delete_error:
                    # Some messages might already be deleted or not found
                    logger.debug(f"Could not delete message {message_id} during refresh: {delete_error}")
        else:
            # Fallback: delete just the current message if no message IDs were stored
            await query.message.delete()
        
        # Clear old message IDs
        context.user_data.pop('pending_message_ids', None)
        
        # Send fresh updated list with new message IDs tracking
        await send_pending_requests_with_posters(context.bot, chat_id, results, context)
        await query.answer(f"🔄 Refreshed - cleared {deleted_count} old messages" if deleted_count > 0 else "🔄 List refreshed")
        
    except Exception as e:
        logger.error(f"Error refreshing pending requests: {e}")
        await query.answer("❌ Error refreshing list", show_alert=True)


async def cancel_pending_requests(query, context: ContextTypes.DEFAULT_TYPE):
    """Cancel and delete all pending request messages from the chat."""
    try:
        chat_id = query.message.chat.id
        deleted_count = 0
        
        # Get stored message IDs
        message_ids = context.user_data.get('pending_message_ids', [])
        
        if message_ids:
            # Delete all tracked messages
            for message_id in message_ids:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                    deleted_count += 1
                except Exception as delete_error:
                    # Some messages might already be deleted or not found
                    logger.debug(f"Could not delete message {message_id}: {delete_error}")
            
            # Clear the stored message IDs
            context.user_data.pop('pending_message_ids', None)
            
            # Send confirmation message
            confirmation_text = (
                f"🗑️ **Chat cleared successfully**\n\n"
                f"Deleted {deleted_count} pending request messages.\n"
                f"Use `/pending` to view requests again when needed."
            )
        else:
            # Fallback if no message IDs were stored
            await query.message.delete()
            confirmation_text = (
                "🗑️ **Pending requests session ended**\n\n"
                "This session has been cancelled.\n"
                "Use `/pending` to view requests again when needed."
            )
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=confirmation_text,
            parse_mode='Markdown'
        )
        
        await query.answer(f"🗑️ Cleared {deleted_count} messages" if deleted_count > 0 else "🗑️ Session ended")
        
    except Exception as e:
        logger.error(f"Error cancelling pending requests: {e}")
        await query.answer("❌ Error clearing chat", show_alert=True)


def is_admin_user(telegram_user_id: int) -> bool:
    """Check if user has admin privileges."""
    try:
        config = load_config()
        user_id_str = str(telegram_user_id)
        user = config.get("users", {}).get(user_id_str, {})
        
        return (user.get("is_admin", False) and 
                user.get("is_authorized", False) and 
                not user.get("is_blocked", False))
                
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False


def format_pending_requests_message(requests: list) -> tuple[str, InlineKeyboardMarkup]:
    """
    Format pending requests into an enhanced display message with action buttons.
    
    Args:
        requests: List of request data from Overseerr API
        
    Returns:
        Tuple of (message_text, inline_keyboard)
    """
    try:
        # Get enhanced media details for each request with error handling
        request_manager = RequestManager()
        enhanced_requests = []
        failed_requests = 0
        
        for request in requests[:5]:  # Limit to 5 requests for optimal UI
            try:
                enhanced_info = request_manager.get_media_details_from_request(request)
                enhanced_requests.append(enhanced_info)
            except Exception as e:
                logger.error(f"Failed to enhance request {request.get('id', 'unknown')}: {e}")
                failed_requests += 1
                # Add basic fallback info
                enhanced_requests.append({
                    'request_id': request.get('id'),
                    'title': 'Unknown Title',
                    'year': 'Unknown Year',
                    'media_type': request.get('media', {}).get('mediaType', 'unknown'),
                    'overview': 'Details unavailable due to API error',
                    'genres': [],
                    'quality': '4K' if request.get('is4k', False) else 'HD',
                    'requested_by': {'display_name': 'Unknown User', 'username': ''},
                    'requested_at': request.get('createdAt')
                })
        
        # Build enhanced message with status indicators
        total_count = len(requests)
        displayed_count = len(enhanced_requests)
        
        header = f"📋 **Pending Requests ({total_count})**"
        if failed_requests > 0:
            header += f"\n⚠️ *{failed_requests} requests had loading errors*"
        if total_count > displayed_count:
            header += f"\n📄 *Showing first {displayed_count} of {total_count} requests*"
        
        message_lines = [header, ""]
        keyboard_buttons = []
        
        for i, req_info in enumerate(enhanced_requests):
            # Enhanced media type display with better emojis
            media_emoji = get_media_emoji(req_info['media_type'])  # Use existing function
            media_type_display = get_media_type_display(req_info['media_type'])  # Use existing function
            
            # Format genres with fallback
            genres_text = ', '.join(req_info['genres'][:2]) if req_info['genres'] else 'Genre info unavailable'
            
            # Format requester
            requester = req_info['requested_by']
            requester_display = f"@{requester['username']}" if requester['username'] else requester['display_name']
            
            # Format time
            time_text = format_request_time(req_info['requested_at'])
            
            # Truncate overview for better display
            overview = req_info['overview']
            if len(overview) > 100:
                overview = overview[:97] + "..."
            
            # Format request entry
            message_lines.extend([
                f"{media_emoji} **{req_info['title']} ({req_info['year']})** - {media_type_display}",
                f"🎭 {genres_text}",
                f"📝 {overview}",
                f"� {requester_display} • 💿 {req_info['quality']} • ⏰ {time_text}",
                ""
            ])
            
            # Add action buttons for this request (clean, aligned format)
            keyboard_buttons.append([
                InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_{req_info['request_id']}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{req_info['request_id']}")
            ])
        
        # Add refresh button
        keyboard_buttons.append([
            InlineKeyboardButton("🔄 Refresh", callback_data="admin_pending_all")
        ])
        
        message_text = '\n'.join(message_lines)
        if len(requests) > 5:
            message_text += f"\n*... and {len(requests) - 5} more requests*"
        
        return message_text, InlineKeyboardMarkup(keyboard_buttons)
        
    except Exception as e:
        logger.error(f"Error formatting pending requests: {e}")
        return "❌ Error formatting requests", None


def extract_media_title(media: dict) -> str:
    """Extract media title from media data."""
    return (media.get('title') or 
            media.get('name') or 
            media.get('originalTitle') or 
            media.get('originalName') or 
            'Unknown Title')


def extract_media_year(media: dict) -> str:
    """Extract media year from media data."""
    release_date = media.get('releaseDate') or media.get('firstAirDate', '')
    if release_date and '-' in release_date:
        return release_date.split('-')[0]
    return 'Unknown Year'


def get_media_type_display(media_type: str) -> str:
    """Get display name for media type."""
    type_map = {
        'movie': 'Movie',
        'tv': 'TV Series', 
        'anime': 'Anime',
        'unknown': 'Media'
    }
    return type_map.get(media_type.lower(), 'Media')


def get_media_emoji(media_type: str) -> str:
    """Get appropriate emoji for media type with enhanced icons."""
    emoji_map = {
        'movie': '🍿',
        'tv': '📺', 
        'anime': '⛩️',
        'unknown': '❓'
    }
    return emoji_map.get(media_type.lower(), '❓')


def format_request_time(created_at: str) -> str:
    """Format request timestamp for display."""
    try:
        if not created_at:
            return "Unknown time"
        
        # Parse ISO timestamp
        from datetime import datetime
        request_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        now = datetime.now(request_time.tzinfo)
        
        # Calculate time difference
        diff = now - request_time
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"
            
    except Exception:
        return "Unknown time"

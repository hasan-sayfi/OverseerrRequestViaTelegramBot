"""
Admin notification system for Overseerr request management.
Handles sending notifications to admin users when new requests are submitted.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config.config_manager import load_config
from utils.telegram_utils import send_message

logger = logging.getLogger(__name__)


class AdminNotificationManager:
    """Manages admin notifications for new media requests."""
    
    def __init__(self, bot_instance):
        """Initialize with bot instance for sending messages."""
        self.bot = bot_instance
    
    def get_admin_users(self) -> List[Dict[str, Any]]:
        """
        Get list of admin users from bot configuration.
        
        Returns:
            List of admin user dictionaries with user_id and username
        """
        try:
            config = load_config()
            users = config.get("users", {})
            
            admin_users = []
            for user_id_str, user_data in users.items():
                if (user_data.get("is_admin", False) and 
                    user_data.get("is_authorized", False) and 
                    not user_data.get("is_blocked", False)):
                    admin_users.append({
                        "user_id": int(user_id_str),
                        "username": user_data.get("username", "Unknown"),
                        "chat_id": int(user_id_str)  # For private chat notifications
                    })
            
            logger.info(f"Found {len(admin_users)} active admin users")
            return admin_users
            
        except Exception as e:
            logger.error(f"Error getting admin users: {e}")
            return []
    
    async def process_new_request_webhook(self, webhook_data: Dict[str, Any]) -> None:
        """
        Process webhook data for new requests and send admin notifications.
        
        Args:
            webhook_data: Webhook data from Overseerr
        """
        try:
            # Extract notification type and event
            notification_type = webhook_data.get('notification_type', '')
            event = webhook_data.get('event', '')
            
            # Check if this is a new request event
            if not self.is_new_request_event(notification_type, event):
                logger.debug(f"Ignoring non-request event: {notification_type}/{event}")
                return
            
            # Extract request information
            request_info = self.extract_request_info(webhook_data)
            if not request_info:
                logger.warning("Could not extract request information from webhook")
                return
            
            # Get admin users
            admin_users = self.get_admin_users()
            if not admin_users:
                logger.warning("No admin users found for notification")
                return
            
            # Format notification message
            message_text, inline_keyboard = self.format_admin_notification(request_info)
            
            # Send notifications to all admin users
            await self.send_admin_notifications(admin_users, message_text, inline_keyboard)
            
        except Exception as e:
            logger.error(f"Error processing new request webhook: {e}")
    
    def is_new_request_event(self, notification_type: str, event: str) -> bool:
        """
        Determine if webhook represents a new request that needs admin notification.
        
        Args:
            notification_type: The notification type from webhook
            event: The event type from webhook
            
        Returns:
            True if this is a new request event, False otherwise
        """
        # Based on Overseerr webhook documentation
        new_request_indicators = [
            "MEDIA_PENDING",
            "request.new", 
            "request.pending"
        ]
        
        return (notification_type in new_request_indicators or 
                event in new_request_indicators)
    
    def extract_request_info(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract structured request information from webhook data.
        
        Args:
            webhook_data: Raw webhook data from Overseerr
            
        Returns:
            Dictionary with structured request information, or None on error
        """
        try:
            media = webhook_data.get('media', {})
            request = webhook_data.get('request', {})
            
            # Extract basic information
            request_info = {
                'request_id': request.get('id'),
                'media_type': media.get('media_type', 'unknown'),
                'title': self.extract_title(media),
                'year': self.extract_year(media),
                'poster_path': media.get('posterPath'),
                'overview': media.get('overview', 'No description available'),
                'genres': [g.get('name', '') for g in media.get('genres', [])],
                'quality': '4K' if request.get('is4k', False) else 'HD',
                'requested_by': self.extract_requester_info(request),
                'requested_at': request.get('createdAt'),
                'tmdb_id': media.get('tmdbId')
            }
            
            # Validate required fields
            if not request_info['request_id'] or not request_info['title']:
                logger.warning("Missing required request information")
                return None
            
            return request_info
            
        except Exception as e:
            logger.error(f"Error extracting request info: {e}")
            return None
    
    def extract_title(self, media: Dict[str, Any]) -> str:
        """Extract media title from media data."""
        return (media.get('title') or 
                media.get('name') or 
                media.get('originalTitle') or 
                media.get('originalName') or 
                'Unknown Title')
    
    def extract_year(self, media: Dict[str, Any]) -> str:
        """Extract release year from media data."""
        release_date = media.get('releaseDate') or media.get('firstAirDate', '')
        if release_date and '-' in release_date:
            return release_date.split('-')[0]
        return 'Unknown Year'
    
    def extract_requester_info(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Extract requester information from request data."""
        requested_by = request.get('requestedBy', {})
        return {
            'id': requested_by.get('id'),
            'display_name': requested_by.get('displayName', 'Unknown User'),
            'username': requested_by.get('username', ''),
            'email': requested_by.get('email', '')
        }
    
    def format_admin_notification(self, request_info: Dict[str, Any]) -> tuple[str, InlineKeyboardMarkup]:
        """
        Format admin notification message with rich content and action buttons.
        
        Args:
            request_info: Structured request information
            
        Returns:
            Tuple of (message_text, inline_keyboard)
        """
        try:
            # Media type emoji
            media_emoji = self.get_media_emoji(request_info['media_type'])
            
            # Format genres
            genres_text = ', '.join(request_info['genres'][:3]) if request_info['genres'] else 'Unknown'
            
            # Format requester display name
            requester = request_info['requested_by']
            requester_display = f"@{requester['username']}" if requester['username'] else requester['display_name']
            
            # Format timestamp
            time_text = self.format_request_time(request_info['requested_at'])
            
            # Build message
            message_lines = [
                "🔔 **New Request Notification**",
                f"👤 {requester_display} has requested:",
                "",
                f"{media_emoji} **{request_info['title']} ({request_info['year']})** - {genres_text}",
                f"📝 {request_info['overview'][:150]}{'...' if len(request_info['overview']) > 150 else ''}",
                f"💿 Quality: {request_info['quality']}",
                f"📅 Requested: {time_text}",
                "",
                "Choose an action:"
            ]
            
            message_text = '\n'.join(message_lines)
            
            # Create inline keyboard
            keyboard = [
                [
                    InlineKeyboardButton("✅ Quick Approve", 
                                       callback_data=f"admin_approve_{request_info['request_id']}"),
                    InlineKeyboardButton("❌ Quick Reject", 
                                       callback_data=f"admin_reject_{request_info['request_id']}")
                ],
                [
                    InlineKeyboardButton("📋 View All Pending", 
                                       callback_data="admin_pending_all")
                ]
            ]
            
            inline_keyboard = InlineKeyboardMarkup(keyboard)
            
            return message_text, inline_keyboard
            
        except Exception as e:
            logger.error(f"Error formatting admin notification: {e}")
            return "❌ Error formatting notification", None
    
    def get_media_emoji(self, media_type: str) -> str:
        """Get appropriate emoji for media type."""
        emoji_map = {
            'movie': '🎬',
            'tv': '📺', 
            'anime': '🌸',
            'unknown': '📽️'
        }
        return emoji_map.get(media_type.lower(), '📽️')
    
    def format_request_time(self, created_at: str) -> str:
        """Format request timestamp for display."""
        try:
            if not created_at:
                return "Unknown time"
            
            # Parse ISO timestamp
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
    
    async def send_admin_notifications(self, admin_users: List[Dict[str, Any]], 
                                     message_text: str, 
                                     inline_keyboard: Optional[InlineKeyboardMarkup]) -> None:
        """
        Send notification messages to all admin users.
        
        Args:
            admin_users: List of admin user information
            message_text: Formatted notification message
            inline_keyboard: Inline keyboard with action buttons
        """
        successful_sends = 0
        failed_sends = 0
        
        for admin_user in admin_users:
            try:
                chat_id = admin_user['chat_id']
                logger.info(f"Sending admin notification to user {admin_user['user_id']} ({admin_user['username']})")
                
                # Send message using existing utility
                await send_message(
                    self.bot,
                    chat_id,
                    message_text,
                    reply_markup=inline_keyboard,
                    parse_mode='Markdown'
                )
                
                successful_sends += 1
                
            except Exception as e:
                logger.error(f"Failed to send notification to admin {admin_user['user_id']}: {e}")
                failed_sends += 1
        
        logger.info(f"Admin notifications sent: {successful_sends} successful, {failed_sends} failed")

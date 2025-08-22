"""
Polling-based notification system for Overseerr request status changes.
"""
import logging
import asyncio
import json
import os
from typing import Dict, List, Any
from datetime import datetime

from api.overseerr_api import get_user_requests, get_request_details
from config.constants import CURRENT_MODE, BotMode

logger = logging.getLogger(__name__)

class RequestStatusMonitor:
    def __init__(self, bot_instance):
        """Initialize the request status monitor."""
        self.bot = bot_instance
        self.status_file = "data/request_status.json"
        self.check_interval = 300  # 5 minutes
        self.running = False
        
    def load_tracked_requests(self) -> Dict:
        """Load tracked request statuses from file."""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading tracked requests: {e}")
        return {}
    
    def save_tracked_requests(self, requests: Dict):
        """Save tracked request statuses to file."""
        try:
            os.makedirs(os.path.dirname(self.status_file), exist_ok=True)
            with open(self.status_file, 'w') as f:
                json.dump(requests, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving tracked requests: {e}")
    
    def track_request(self, request_id: int, chat_id: int, initial_status: str = "pending"):
        """Start tracking a request for status changes."""
        tracked_requests = self.load_tracked_requests()
        
        tracked_requests[str(request_id)] = {
            "chat_id": chat_id,
            "status": initial_status,
            "tracked_since": datetime.now().isoformat(),
            "last_checked": datetime.now().isoformat()
        }
        
        self.save_tracked_requests(tracked_requests)
        logger.info(f"Now tracking request {request_id} for chat {chat_id}")
    
    async def check_request_status_changes(self):
        """Check all tracked requests for status changes."""
        if CURRENT_MODE != BotMode.API:
            logger.debug("Request monitoring only available in API mode")
            return
            
        tracked_requests = self.load_tracked_requests()
        if not tracked_requests:
            return
        
        changes_made = False
        
        for request_id_str, request_info in tracked_requests.items():
            try:
                request_id = int(request_id_str)
                chat_id = request_info["chat_id"]
                old_status = request_info["status"]
                
                # Get current request details from Overseerr
                request_details = await self.get_request_status(request_id)
                if not request_details:
                    continue
                    
                new_status = request_details.get("status", "unknown")
                
                # Check if status changed
                if new_status != old_status:
                    logger.info(f"Status change detected for request {request_id}: {old_status} -> {new_status}")
                    
                    # Send notification
                    await self.send_status_notification(chat_id, request_details, old_status, new_status)
                    
                    # Update tracked status
                    request_info["status"] = new_status
                    request_info["last_checked"] = datetime.now().isoformat()
                    changes_made = True
                    
                    # Remove from tracking if completed or declined
                    if new_status in ["available", "declined"]:
                        logger.info(f"Request {request_id} completed, removing from tracking")
                        del tracked_requests[request_id_str]
                        changes_made = True
                else:
                    # Just update last checked time
                    request_info["last_checked"] = datetime.now().isoformat()
                    changes_made = True
                    
            except Exception as e:
                logger.error(f"Error checking status for request {request_id_str}: {e}")
        
        if changes_made:
            self.save_tracked_requests(tracked_requests)
    
    async def get_request_status(self, request_id: int) -> Dict[str, Any]:
        """Get request details from Overseerr API."""
        try:
            # This would need to be implemented in the overseerr_api.py
            # For now, return None to indicate the feature needs API implementation
            logger.debug(f"Would check status for request {request_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting request status for {request_id}: {e}")
            return None
    
    async def send_status_notification(self, chat_id: int, request_details: Dict, old_status: str, new_status: str):
        """Send status change notification to Telegram."""
        try:
            title = request_details.get("media", {}).get("title", "Unknown Title")
            media_type = request_details.get("type", "unknown")
            request_id = request_details.get("id", "N/A")
            
            # Format message based on new status
            if new_status == "approved":
                emoji = "✅"
                message = f"**Request Approved**"
                details = f"Your request has been approved and will be processed soon."
            elif new_status == "declined":
                emoji = "❌"
                message = f"**Request Declined**" 
                details = f"Your request has been declined."
            elif new_status == "available":
                emoji = "🎉"
                message = f"**Media Available**"
                details = f"Your requested media is now available for viewing!"
            else:
                emoji = "ℹ️"
                message = f"**Status Update**"
                details = f"Request status changed from {old_status} to {new_status}"
            
            media_emoji = "🎬" if media_type == "movie" else "📺"
            
            notification_text = f"""{emoji} {message}

{media_emoji} **{title}**
🆔 Request ID: #{request_id}

{details}"""
            
            await self.bot.send_message(
                chat_id=chat_id, 
                text=notification_text, 
                parse_mode='Markdown'
            )
            logger.info(f"Sent status notification to chat {chat_id}")
            
        except Exception as e:
            logger.error(f"Error sending notification to chat {chat_id}: {e}")
    
    async def start_monitoring(self):
        """Start the background monitoring loop."""
        if self.running:
            return
            
        self.running = True
        logger.info(f"Starting request status monitoring (check interval: {self.check_interval}s)")
        
        while self.running:
            try:
                await self.check_request_status_changes()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    def stop_monitoring(self):
        """Stop the background monitoring."""
        self.running = False
        logger.info("Stopped request status monitoring")

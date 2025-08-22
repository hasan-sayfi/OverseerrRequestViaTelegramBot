"""
Lightweight webhook handler for receiving Overseerr notifications.
"""
import logging
import json
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from typing import Dict, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class WebhookHandler:
    def __init__(self, bot_instance):
        """Initialize webhook handler with bot instance."""
        self.bot = bot_instance
        self.server = None
        self.server_thread = None
        
    def create_request_handler(self):
        """Create request handler class with bot instance."""
        bot = self.bot
        
        class OverseerrWebhookHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                """Override to use our logger instead of stdout."""
                logger.info(format % args)
                
            def do_GET(self):
                """Handle GET requests (health check)."""
                parsed_path = urlparse(self.path)
                
                if parsed_path.path == '/webhook/health':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = json.dumps({"status": "healthy"})
                    self.wfile.write(response.encode())
                else:
                    self.send_response(404)
                    self.end_headers()
                    
            def do_POST(self):
                """Handle POST requests (webhook notifications)."""
                parsed_path = urlparse(self.path)
                
                if parsed_path.path == '/webhook/overseerr':
                    try:
                        # Read request body
                        content_length = int(self.headers.get('Content-Length', 0))
                        post_data = self.rfile.read(content_length)
                        
                        # Parse JSON
                        webhook_data = json.loads(post_data.decode('utf-8'))
                        logger.info(f"Received Overseerr webhook: {json.dumps(webhook_data, indent=2)}")
                        
                        # Process webhook in background
                        asyncio.create_task(self.process_webhook(webhook_data))
                        
                        # Return success response
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        response = json.dumps({"status": "success"})
                        self.wfile.write(response.encode())
                        
                    except Exception as e:
                        logger.error(f"Error processing webhook: {e}")
                        self.send_response(500)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        response = json.dumps({"error": "Internal server error"})
                        self.wfile.write(response.encode())
                else:
                    self.send_response(404)
                    self.end_headers()
                    
            async def process_webhook(self, webhook_data: Dict[str, Any]):
                """Process webhook data and send Telegram notification."""
                try:
                    notification_type = webhook_data.get('notification_type', 'unknown')
                    subject = webhook_data.get('subject', 'Unknown')
                    message = webhook_data.get('message', '')
                    media = webhook_data.get('media', {})
                    request_data = webhook_data.get('request', {})
                    
                    # Extract media information
                    media_type = media.get('media_type', 'unknown')
                    title = subject  # Use subject as title fallback
                    
                    # Extract request information
                    requested_by = request_data.get('requestedBy', {}).get('displayName', 'Unknown User')
                    request_id = request_data.get('id', 'N/A')
                    
                    # Format notification message
                    telegram_message = self.format_notification_message(
                        notification_type, subject, message, title, media_type, 
                        requested_by, request_id
                    )
                    
                    # Send to Telegram
                    await self.send_to_telegram(telegram_message, webhook_data)
                    
                except Exception as e:
                    logger.error(f"Error in webhook processing: {e}")
                    
            def format_notification_message(self, notification_type: str, subject: str, message: str, 
                                          title: str, media_type: str, requested_by: str, 
                                          request_id: str) -> str:
                """Format notification message for Telegram."""
                
                # Media type emoji
                media_emoji = "🎬" if media_type == "movie" else "📺" if media_type == "tv" else "📽️"
                
                # Notification type specific formatting
                if notification_type == 'MEDIA_APPROVED':
                    status_emoji = "✅"
                    status_text = "**Request Approved**"
                    action = f"Your request has been approved and will be processed soon."
                    
                elif notification_type == 'MEDIA_DECLINED':
                    status_emoji = "❌" 
                    status_text = "**Request Declined**"
                    action = f"Your request has been declined."
                    
                elif notification_type == 'MEDIA_AUTO_APPROVED':
                    status_emoji = "🤖"
                    status_text = "**Request Auto-Approved**"
                    action = f"Your request has been automatically approved and will be processed soon."
                    
                elif notification_type == 'MEDIA_AVAILABLE':
                    status_emoji = "🎉"
                    status_text = "**Media Available**"
                    action = f"Your requested media is now available for viewing!"
                    
                elif notification_type == 'MEDIA_FAILED':
                    status_emoji = "⚠️"
                    status_text = "**Processing Failed**"
                    action = f"Failed to process your request. Please check the system."
                    
                else:
                    status_emoji = "ℹ️"
                    status_text = f"**{notification_type.replace('_', ' ').title()}**"
                    action = message or f"Update for your request"
                
                # Build the message
                formatted_message = f"""{status_emoji} {status_text}

{media_emoji} **{title}**
👤 Requested by: {requested_by}
🆔 Request ID: #{request_id}

{action}"""

                if message and message != action:
                    formatted_message += f"\n\n💬 {message}"
                    
                return formatted_message
                
            async def send_to_telegram(self, message: str, webhook_data: Dict[str, Any]):
                """Send notification to Telegram."""
                try:
                    # Try to extract chat ID from webhook data
                    chat_id = None
                    
                    # Check various possible locations for chat ID
                    notification_agent = webhook_data.get('notificationAgent', {})
                    if notification_agent:
                        options = notification_agent.get('options', {})
                        chat_id = options.get('chatId') or options.get('chat_id')
                    
                    # If no chat ID in webhook, you might want to use a default
                    # or get it from your bot configuration
                    if not chat_id:
                        logger.warning("No chat ID found in webhook data, notification not sent")
                        return
                        
                    # Send message
                    await bot.send_message(
                        chat_id=chat_id, 
                        text=message, 
                        parse_mode='Markdown'
                    )
                    logger.info(f"Notification sent to chat {chat_id}")
                    
                except Exception as e:
                    logger.error(f"Error sending Telegram notification: {e}")
                    
        return OverseerrWebhookHandler
    
    def start_webhook_server(self, host='0.0.0.0', port=8080):
        """Start the webhook server in a separate thread."""
        def run_server():
            try:
                handler_class = self.create_request_handler()
                self.server = HTTPServer((host, port), handler_class)
                logger.info(f"Starting webhook server on {host}:{port}")
                logger.info(f"Webhook URL: http://{host}:{port}/webhook/overseerr")
                logger.info(f"Health check: http://{host}:{port}/webhook/health")
                self.server.serve_forever()
            except Exception as e:
                logger.error(f"Webhook server error: {e}")
        
        self.server_thread = Thread(target=run_server, daemon=True)
        self.server_thread.start()
        logger.info("Webhook server started in background thread")
        
        return self.server_thread
    
    def stop_webhook_server(self):
        """Stop the webhook server."""
        if self.server:
            self.server.shutdown()
            logger.info("Webhook server stopped")

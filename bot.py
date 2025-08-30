#!/usr/bin/env python3
"""
Overseerr Telegram Bot - Main entry point
A Telegram bot for interacting with Overseerr media requests.

Version: 4.0.2
Build: 2025.08.22.0750
"""

import logging
import os
import atexit
import signal
import sys
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Import configuration and handlers
from config.constants import VERSION, BUILD, TELEGRAM_TOKEN, CURRENT_MODE, BotMode
from config.config_manager import ensure_data_directory, load_config
from session.session_manager import load_shared_session
from utils.user_loader import user_data_loader
from utils.health_check import health_checker
from handlers.command_handlers import start_command, check_media
from handlers.text_handlers import handle_text_input
from handlers.ui_handlers import show_settings_menu
from handlers.callback_handlers import button_handler
from handlers.admin_handlers import pending_requests_command, handle_admin_approval_callback

logger.info(f"Bot Version: {VERSION} BUILD: {BUILD}")

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    health_checker.stop_health_monitor()
    health_checker.cleanup_health_file()
    sys.exit(0)

def main():
    """Main entry point for the bot."""
    global CURRENT_MODE
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Register cleanup function for normal exits
    atexit.register(lambda: (health_checker.stop_health_monitor(), health_checker.cleanup_health_file()))
    
    ensure_data_directory()
    config = load_config()
    mode_from_config = config.get("mode", "normal")
    
    try:
        CURRENT_MODE = BotMode[mode_from_config.upper()]
    except KeyError:
        logger.warning(f"Invalid mode {mode_from_config} in config, defaulting to NORMAL")
        CURRENT_MODE = BotMode.NORMAL
    
    logger.info(f"Bot started in mode: {CURRENT_MODE.value}")

    # Start health monitoring
    health_checker.start_health_monitor()
    logger.info("Health monitoring started")

    # Build the application
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Set up bot commands for autocomplete menu
    async def set_bot_commands():
        """Set up bot commands for Telegram's autocomplete menu
        
        Alternative manual setup via BotFather:
        1. Message @BotFather on Telegram
        2. Send /setcommands
        3. Select your bot
        4. Send this list:
        start - Start the bot and see welcome message
        check - Check media availability in Overseerr  
        settings - Configure bot settings and preferences
        pending - View pending requests (Admin only)
        """
        from telegram import BotCommand
        commands = [
            BotCommand("start", "Start the bot and see welcome message"),
            BotCommand("check", "Check media availability in Overseerr"),
            BotCommand("settings", "Configure bot settings and preferences"),
            BotCommand("pending", "View pending requests (Admin only)")
        ]
        await app.bot.set_my_commands(commands)
        logger.info("Bot commands set up for autocomplete menu")

    # Load shared session if in shared mode
    if CURRENT_MODE == BotMode.SHARED:
        shared_session = load_shared_session()
        if shared_session:
            app.bot_data["shared_session"] = shared_session
            logger.info("Loaded shared session for Shared mode")

    # Register handlers
    app.add_handler(MessageHandler(filters.ALL, user_data_loader), group=-999)
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("settings", show_settings_menu))
    app.add_handler(CommandHandler("check", check_media))
    app.add_handler(CommandHandler("pending", pending_requests_command))  # NEW: Admin command
    app.add_handler(CallbackQueryHandler(handle_admin_approval_callback, pattern="^admin_"))  # NEW: Admin callbacks
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    # Set up bot commands using post_init hook
    async def post_init(application):
        """Set up bot commands after application initialization"""
        await set_bot_commands()
    
    app.post_init = post_init

    logger.info("Starting bot polling...")
    app.run_polling()

if __name__ == "__main__":
    main()

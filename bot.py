#!/usr/bin/env python3
"""
Overseerr Telegram Bot - Main entry point
A Telegram bot for interacting with Overseerr media requests.

Version information is loaded dynamically from pyproject.toml
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
from config.constants import VERSION, TELEGRAM_TOKEN, CURRENT_MODE, BotMode
from config.config_manager import ensure_data_directory, load_config
from session.session_manager import load_shared_session
from utils.user_loader import user_data_loader
from utils.health_check import health_checker
from handlers.command_handlers import start_command, check_media
from handlers.text_handlers import handle_text_input
from handlers.ui_handlers import show_settings_menu
from handlers.callback_handlers import button_handler

logger.info(f"Bot Version: {VERSION}")

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
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    logger.info("Starting bot polling...")
    app.run_polling()

if __name__ == "__main__":
    main()

"""
Health check utilities for Docker container monitoring.
"""
import os
import time
import threading
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class HealthChecker:
    """Manages health check file for Docker container monitoring."""
    
    def __init__(self, health_file_path="data/bot_health.txt"):
        self.health_file_path = health_file_path
        self.update_interval = 30  # Update every 30 seconds
        self.is_running = False
        self.thread = None
        self._ensure_health_file_directory()
    
    def _ensure_health_file_directory(self):
        """Ensure the directory for health file exists."""
        health_dir = os.path.dirname(self.health_file_path)
        if health_dir and not os.path.exists(health_dir):
            os.makedirs(health_dir, exist_ok=True)
    
    def create_health_file(self):
        """Create or update the health file with current timestamp."""
        try:
            with open(self.health_file_path, 'w') as f:
                f.write(f"Bot is healthy at {datetime.now(timezone.utc).isoformat()}\n")
            logger.debug(f"Health file updated: {self.health_file_path}")
        except Exception as e:
            logger.error(f"Failed to update health file: {e}")
    
    def start_health_monitor(self):
        """Start the health monitoring thread."""
        if self.is_running:
            logger.warning("Health monitor is already running")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._health_monitor_loop, daemon=True)
        self.thread.start()
        logger.info("Health monitor started")
        
        # Create initial health file
        self.create_health_file()
    
    def stop_health_monitor(self):
        """Stop the health monitoring thread."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Health monitor stopped")
    
    def _health_monitor_loop(self):
        """Main loop for health monitoring."""
        while self.is_running:
            try:
                self.create_health_file()
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in health monitor loop: {e}")
                time.sleep(5)  # Short sleep on error
    
    def cleanup_health_file(self):
        """Remove the health file on shutdown."""
        try:
            if os.path.exists(self.health_file_path):
                os.remove(self.health_file_path)
                logger.info("Health file cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup health file: {e}")

# Global health checker instance
health_checker = HealthChecker()

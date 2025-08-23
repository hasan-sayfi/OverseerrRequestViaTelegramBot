"""
Configuration constants and enums for the Overseerr Telegram Bot.
"""
import os
from enum import Enum

# Load .env file if it exists
def load_env_file():
    """Load environment variables from .env file"""
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Try to load with python-dotenv first, fallback to manual loading
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, use manual loading
    load_env_file()

###############################################################################
#                              BOT VERSION
###############################################################################
# Import version information from centralized location
from utils.version import VERSION

###############################################################################
#                    LOAD CONFIG OR ENVIRONMENT VARIABLES
###############################################################################
try:
    OVERSEERR_API_URL = (
        os.environ.get("OVERSEERR_API_URL")
        or getattr(__import__("config"), "OVERSEERR_API_URL", None)
    )
    OVERSEERR_API_KEY = (
        os.environ.get("OVERSEERR_API_KEY")
        or getattr(__import__("config"), "OVERSEERR_API_KEY", None)
    )
    TELEGRAM_TOKEN = (
        os.environ.get("TELEGRAM_TOKEN")
        or getattr(__import__("config"), "TELEGRAM_TOKEN", None)
    )
    # password initialization - check environment first, then config.py
    PASSWORD = os.environ.get("PASSWORD") or os.environ.get("BOT_PASSWORD")
    if PASSWORD is None:
        try:
            # Try loading from config.py as fallback
            config_module = __import__("config")
            PASSWORD = getattr(config_module, "PASSWORD", None)
        except ImportError:
            # config.py not found, use None as fallback
            PASSWORD = None
            
except Exception as e:
    print(f"Failed to load config: {e}")

###############################################################################
#                          OVERSEERR CONSTANTS
###############################################################################
STATUS_UNKNOWN = 1
STATUS_PENDING = 2
STATUS_PROCESSING = 3
STATUS_PARTIALLY_AVAILABLE = 4
STATUS_AVAILABLE = 5

ISSUE_TYPES = {
    1: "Video",
    2: "Audio",
    3: "Subtitle",
    4: "Other"
}

# Operating modes as enum
class BotMode(Enum):
    NORMAL = "normal"
    API = "api"
    SHARED = "shared"

# Define CURRENT_MODE globally
CURRENT_MODE = BotMode.NORMAL  # Default mode

# Contains the authorisation bit for 4K
PERMISSION_4K_MOVIE = 2048
PERMISSION_4K_TV = 4096

DEFAULT_POSTER_URL = "https://raw.githubusercontent.com/sct/overseerr/refs/heads/develop/public/images/overseerr_poster_not_found.png"

###############################################################################
#                              FILE PATHS
###############################################################################
CONFIG_FILE = "data/bot_config.json"
USER_SELECTION_FILE = "data/api_mode_selections.json"  # For API mode
USER_SESSIONS_FILE = "data/normal_mode_sessions.json"  # For Normal mode
SHARED_SESSION_FILE = "data/shared_mode_session.json"  # For Shared mode

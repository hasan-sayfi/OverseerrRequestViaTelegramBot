# Refactored Overseerr Telegram Bot

This is a refactored version of the Overseerr Telegram Bot that has been broken down into smaller, more manageable modules while maintaining all original features and functionality.

## Project Structure

```
OverseerrRequestViaTelegramBot/
├── bot.py                          # Main entry point
├── config/                         # Configuration management
│   ├── __init__.py
│   ├── constants.py                # Bot constants and environment variables
│   └── config_manager.py           # Configuration loading/saving utilities
├── session/                        # Session management for different modes
│   ├── __init__.py
│   └── session_manager.py          # Normal, API, and Shared mode sessions
├── api/                           # Overseerr API integration
│   ├── __init__.py
│   └── overseerr_api.py           # All Overseerr API functions
├── notifications/                 # Notification management
│   ├── __init__.py
│   └── notification_manager.py    # Telegram notifications with Overseerr
├── utils/                         # Utility functions
│   ├── __init__.py
│   ├── telegram_utils.py          # Telegram messaging utilities
│   └── user_loader.py             # User data loading middleware
├── handlers/                      # Telegram bot handlers
│   ├── __init__.py
│   ├── command_handlers.py        # /start, /check, /settings commands
│   ├── text_handlers.py           # Text input handling (login, passwords, issues)
│   ├── ui_handlers.py             # UI menus and media display
│   └── callback_handlers.py       # Button callback handling
├── data/                          # Data storage (created at runtime)
│   ├── bot_config.json            # Bot configuration
│   ├── api_mode_selections.json   # API mode user selections
│   ├── normal_mode_sessions.json  # Normal mode user sessions
│   └── shared_mode_session.json   # Shared mode session
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Docker configuration
├── docker-compose.yml             # Docker Compose configuration
└── README_REFACTORED.md           # This file
```

## Key Improvements

### 1. Modular Architecture
- **Separation of Concerns**: Each module has a specific responsibility
- **Single Responsibility Principle**: Functions are focused and easier to understand
- **Maintainability**: Easier to find, debug, and modify specific functionality

### 2. Organized by Feature
- **Configuration**: All config-related functions in one place
- **API Integration**: Overseerr API calls separated from business logic
- **Session Management**: Different modes (Normal/API/Shared) clearly separated
- **Handlers**: Command, text, and callback handlers organized by type

### 3. Better Code Organization
- **Constants**: All environment variables and constants centralized
- **Utilities**: Reusable helper functions extracted
- **Error Handling**: Consistent error handling patterns
- **Logging**: Proper logging throughout all modules

## Module Descriptions

### `config/`
- **constants.py**: Bot version, API URLs, file paths, enums, and environment variables
- **config_manager.py**: Configuration loading, saving, and user authorization functions

### `session/`
- **session_manager.py**: Handles user sessions for all three bot modes (Normal, API, Shared)

### `api/`
- **overseerr_api.py**: All Overseerr API interactions including search, requests, authentication, and user management

### `notifications/`
- **notification_manager.py**: Telegram notification setup and management with Overseerr

### `utils/`
- **telegram_utils.py**: Telegram messaging utilities and status interpretation
- **user_loader.py**: Middleware for loading user data at the start of each request

### `handlers/`
- **command_handlers.py**: Handles `/start`, `/check`, and `/settings` commands
- **text_handlers.py**: Processes text input for login, passwords, and issue reporting
- **ui_handlers.py**: Manages settings menus, search results display, and user selection
- **callback_handlers.py**: Handles all button clicks and callback queries

## Original Features Preserved

All original functionality has been maintained:

### ✅ Core Features
- **Three Operation Modes**: Normal, API, and Shared modes
- **Media Search**: `/check` command with full search functionality
- **Media Requests**: HD/4K requests with season selection for TV shows
- **Issue Reporting**: Full issue reporting system with all issue types
- **User Management**: Admin controls for user promotion, blocking, etc.
- **Notification Management**: Telegram notification settings integration
- **Group Mode**: Restriction to specific chats/threads
- **Password Protection**: Optional password authentication

### ✅ Advanced Features
- **Session Management**: Persistent sessions across restarts
- **Pagination**: Search results and user lists with navigation
- **4K Permissions**: Proper 4K request permission checking
- **Season Selection**: Multi-season TV show request handling
- **Admin Controls**: Mode switching, user management, configuration
- **Error Handling**: Comprehensive error handling and logging

## Benefits of Refactoring

1. **Easier Maintenance**: Bug fixes and feature additions are more straightforward
2. **Better Testing**: Each module can be tested independently
3. **Code Reusability**: Functions can be easily reused across different parts
4. **Team Development**: Multiple developers can work on different modules
5. **Documentation**: Clearer code structure makes documentation easier
6. **Debugging**: Issues can be isolated to specific modules
7. **Extensibility**: New features can be added without affecting existing code

## Running the Refactored Bot

The bot runs exactly the same as before:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python bot.py
```

Or using Docker:

```bash
docker-compose up -d
```

## Migration from Original

No migration is needed! The refactored bot:
- Uses the same data files and configuration
- Maintains the same environment variables
- Preserves all user sessions and settings
- Provides identical functionality to users

## Development Guidelines

When adding new features:

1. **Place API calls in** `api/overseerr_api.py`
2. **Add UI components to** `handlers/ui_handlers.py`
3. **Put callback handlers in** `handlers/callback_handlers.py`
4. **Add utility functions to** `utils/`
5. **Keep constants in** `config/constants.py`
6. **Follow the existing error handling patterns**
7. **Add appropriate logging statements**

This refactored structure makes the codebase much more maintainable while preserving every feature of the original bot!

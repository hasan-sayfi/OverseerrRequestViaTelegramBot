# Project Structure Documentation

## Directory Organization

### Core Application
- `api/` - Overseerr API integration modules
- `config/` - Configuration management and constants
- `handlers/` - Telegram bot event handlers
- `notifications/` - Notification system management
- `session/` - User session management
- `utils/` - Utility functions and helpers

### Supporting Directories
- `docker/` - Docker configuration and deployment scripts
- `tests/` - Unit tests and test utilities
- `data/` - Runtime data and session storage

### Documentation
- `README.md` - Main project documentation
- `LICENSE` - Project license information

### Configuration
- `requirements.txt` - Python dependencies
- `bot_config.py.template` - Configuration template
- `.gitignore` - Git ignore patterns

## Usage

1. Copy `bot_config.py.template` to `bot_config.py`
2. Configure your settings in `bot_config.py`
3. Install dependencies: `pip install -r requirements.txt`
4. Run the bot: `python bot.py`

## Docker Deployment

See `docker/README.md` for Docker deployment instructions.

## Testing

Run tests with: `python -m pytest tests/`

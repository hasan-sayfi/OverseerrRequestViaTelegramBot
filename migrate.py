#!/usr/bin/env python3
"""
Migration script to backup the original file and set up the refactored structure.
"""
import os
import shutil
from datetime import datetime

def create_backup():
    """Create a backup of the original file."""
    original_file = "telegram_overseerr_bot.py"
    if os.path.exists(original_file):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"telegram_overseerr_bot_backup_{timestamp}.py"
        shutil.copy2(original_file, backup_file)
        print(f"✅ Created backup: {backup_file}")
        return True
    else:
        print("⚠️ Original file not found - no backup needed")
        return False

def ensure_directories():
    """Ensure all required directories exist."""
    directories = [
        "config",
        "session", 
        "api",
        "notifications",
        "utils",
        "handlers",
        "data"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 Created directory: {directory}")
        else:
            print(f"✅ Directory exists: {directory}")

def check_files():
    """Check if all refactored files are present."""
    required_files = [
        "bot.py",
        "config/__init__.py",
        "config/constants.py",
        "config/config_manager.py",
        "session/__init__.py",
        "session/session_manager.py",
        "api/__init__.py",
        "api/overseerr_api.py",
        "notifications/__init__.py",
        "notifications/notification_manager.py",
        "utils/__init__.py",
        "utils/telegram_utils.py",
        "utils/user_loader.py",
        "handlers/__init__.py",
        "handlers/command_handlers.py",
        "handlers/text_handlers.py",
        "handlers/ui_handlers.py",
        "handlers/callback_handlers.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)
    
    return missing_files

def main():
    """Main migration function."""
    print("🚀 Overseerr Telegram Bot - Refactoring Migration")
    print("=" * 50)
    
    # Create backup
    print("\n1. Creating backup of original file...")
    create_backup()
    
    # Ensure directories
    print("\n2. Ensuring directory structure...")
    ensure_directories()
    
    # Check files
    print("\n3. Checking refactored files...")
    missing_files = check_files()
    
    print("\n" + "=" * 50)
    if missing_files:
        print(f"❌ Migration incomplete - {len(missing_files)} files missing:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease ensure all refactored files are created.")
    else:
        print("✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Test the refactored bot: python bot.py")
        print("2. Verify all features work as expected")
        print("3. Remove the original file when satisfied")
    
    print("\n📝 Note: All your existing data and configuration will be preserved!")

if __name__ == "__main__":
    main()

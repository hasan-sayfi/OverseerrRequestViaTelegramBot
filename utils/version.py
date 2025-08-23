"""
Version management utility for Overseerr Telegram Bot.
Reads version from pyproject.toml as the single source of truth.
"""
import os
import sys
from pathlib import Path

def get_project_root():
    """Get the project root directory."""
    current_file = Path(__file__)
    # Go up from utils/version.py to project root
    return current_file.parent.parent

def read_version_from_pyproject():
    """Read version from pyproject.toml file."""
    try:
        project_root = get_project_root()
        pyproject_path = project_root / "pyproject.toml"
        
        if not pyproject_path.exists():
            return "4.1.2"  # Fallback version
        
        with open(pyproject_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple parsing for version line
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('version = '):
                # Extract version from: version = "4.1.2"
                version = line.split('=')[1].strip().strip('"\'')
                return version
        
        return "4.1.2"  # Fallback if not found
        
    except Exception as e:
        print(f"Warning: Could not read version from pyproject.toml: {e}")
        return "4.1.2"  # Fallback version

# Export version information
VERSION = read_version_from_pyproject()

if __name__ == "__main__":
    print(f"Version: {VERSION}")

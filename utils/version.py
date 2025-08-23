"""
Standalone version reader for GitHub Actions workflows.
This file MUST NOT import any other local modules to avoid dependency issues.
"""

from pathlib import Path


def get_version():
    """Get version from pyproject.toml without any external dependencies"""
    try:
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        
        # Simple text parsing - most reliable for CI/CD
        with open(pyproject_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith('version = "') and line.endswith('"'):
                    # Extract version between quotes
                    return line.split('"')[1]
        
        return "0.0.0"  # Fallback if not found
        
    except Exception:
        return "0.0.0"  # Fallback on any error


# Export VERSION constant
VERSION = get_version()

if __name__ == "__main__":
    print(f"Current version: {VERSION}")
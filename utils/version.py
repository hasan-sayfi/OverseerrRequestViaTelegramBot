"""
Standalone version reader for GitHub Actions workflows.
This file MUST NOT import any other local modules to avoid dependency issues.
"""

import sys
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
        
        raise RuntimeError("version field not found in pyproject.toml")
        
    except Exception as e:
        raise RuntimeError(f"Could not read version from pyproject.toml: {e}")


# Export VERSION constant
VERSION = get_version()

import os
from pathlib import Path

def get_version():
    """
    Get the current version of the project from pyproject.toml.
    
    Returns:
        str: The version string (e.g., "4.1.3")
    """
    try:
        # Try to import tomllib (Python 3.11+)
        try:
            import tomllib
        except ImportError:
            # Fallback to tomli for older Python versions
            try:
                import tomli as tomllib
            except ImportError:
                # If neither is available, try toml package
                try:
                    import toml
                    
                    # Find pyproject.toml file
                    current_dir = Path(__file__).parent.parent
                    pyproject_path = current_dir / "pyproject.toml"
                    
                    if pyproject_path.exists():
                        with open(pyproject_path, 'r', encoding='utf-8') as f:
                            pyproject_data = toml.load(f)
                        return pyproject_data.get('project', {}).get('version', '0.0.0')
                except ImportError:
                    pass
                
                # Manual parsing as last resort
                current_dir = Path(__file__).parent.parent
                pyproject_path = current_dir / "pyproject.toml"
                
                if pyproject_path.exists():
                    with open(pyproject_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip().startswith('version = '):
                                # Extract version from line like: version = "4.1.3"
                                version_str = line.split('=', 1)[1].strip()
                                # Remove quotes
                                version_str = version_str.strip('"\'')
                                return version_str
                
                return "0.0.0"
        
        # Use tomllib (preferred method)
        current_dir = Path(__file__).parent.parent
        pyproject_path = current_dir / "pyproject.toml"
        
        if pyproject_path.exists():
            with open(pyproject_path, 'rb') as f:
                pyproject_data = tomllib.load(f)
            return pyproject_data.get('project', {}).get('version', '0.0.0')
        
        return "0.0.0"
        
    except Exception as e:
        # Fallback to hardcoded version if all else fails
        return "4.1.3"

if __name__ == "__main__":
    print(f"Current version: {get_version()}")

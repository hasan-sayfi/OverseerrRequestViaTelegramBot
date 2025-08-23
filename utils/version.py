"""Version utility module for reading project version from pyproject.toml"""

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

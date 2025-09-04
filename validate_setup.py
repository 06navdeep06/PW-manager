"""
Setup validation script for the Discord Personal Data Bot.
Checks all dependencies and configuration before starting the bot.
"""

import os
import sys
import logging
from typing import List, Tuple

def check_python_version() -> Tuple[bool, str]:
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        return False, f"Python 3.8+ required, found {version.major}.{version.minor}"
    return True, f"Python {version.major}.{version.minor}.{version.micro}"

def check_environment_variables() -> Tuple[bool, List[str]]:
    """Check required environment variables."""
    required_vars = ["DISCORD_BOT_TOKEN"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    return len(missing_vars) == 0, missing_vars

def check_optional_dependencies() -> Tuple[bool, List[str]]:
    """Check optional dependencies."""
    optional_deps = {
        "discord.py": "discord",
        "aiosqlite": "aiosqlite", 
        "Pillow": "PIL",
        "pytesseract": "pytesseract",
        "Flask": "flask"
    }
    
    missing_deps = []
    for name, module in optional_deps.items():
        try:
            __import__(module)
        except ImportError:
            missing_deps.append(name)
    
    return len(missing_deps) == 0, missing_deps

def check_tesseract() -> Tuple[bool, str]:
    """Check if Tesseract OCR is available."""
    try:
        import pytesseract
        # Try to get version
        version = pytesseract.get_tesseract_version()
        return True, f"Tesseract {version} found"
    except ImportError:
        return False, "pytesseract not installed"
    except Exception as e:
        return False, f"Tesseract not found: {e}"

def check_database_permissions() -> Tuple[bool, str]:
    """Check database file permissions."""
    db_path = os.getenv('DATABASE_PATH', 'user_data.db')
    
    try:
        # Try to create a test file
        test_path = f"{db_path}.test"
        with open(test_path, 'w') as f:
            f.write("test")
        os.remove(test_path)
        return True, f"Database directory writable: {os.path.dirname(os.path.abspath(db_path))}"
    except Exception as e:
        return False, f"Database directory not writable: {e}"

def check_discord_token() -> Tuple[bool, str]:
    """Validate Discord bot token format."""
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        return False, "DISCORD_BOT_TOKEN not set"
    
    # Basic token format validation
    if len(token) < 50:
        return False, "Discord token appears to be too short"
    
    if not token.count('.') >= 2:
        return False, "Discord token format appears invalid"
    
    return True, "Discord token format appears valid"

def run_validation() -> bool:
    """Run all validation checks."""
    print("🔍 Discord Personal Data Bot - Setup Validation")
    print("=" * 50)
    
    all_passed = True
    
    # Python version
    passed, message = check_python_version()
    print(f"Python Version: {'✅' if passed else '❌'} {message}")
    if not passed:
        all_passed = False
    
    # Environment variables
    passed, missing = check_environment_variables()
    print(f"Environment Variables: {'✅' if passed else '❌'} ", end="")
    if passed:
        print("All required variables set")
    else:
        print(f"Missing: {', '.join(missing)}")
        all_passed = False
    
    # Discord token validation
    passed, message = check_discord_token()
    print(f"Discord Token: {'✅' if passed else '❌'} {message}")
    if not passed:
        all_passed = False
    
    # Optional dependencies
    passed, missing = check_optional_dependencies()
    print(f"Dependencies: {'✅' if passed else '⚠️'} ", end="")
    if passed:
        print("All dependencies available")
    else:
        print(f"Missing: {', '.join(missing)}")
        print("  Note: Some features may not work without these dependencies")
    
    # Tesseract OCR
    passed, message = check_tesseract()
    print(f"Tesseract OCR: {'✅' if passed else '⚠️'} {message}")
    if not passed:
        print("  Note: Image OCR will not work without Tesseract")
    
    # Database permissions
    passed, message = check_database_permissions()
    print(f"Database Access: {'✅' if passed else '❌'} {message}")
    if not passed:
        all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("🎉 All critical checks passed! Bot should start successfully.")
        return True
    else:
        print("❌ Some critical checks failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)

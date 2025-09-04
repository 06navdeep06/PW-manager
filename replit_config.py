"""
Replit-specific configuration for the Discord Personal Data Bot.
"""

import os

# Replit environment variables
REPLIT_DB_URL = os.getenv('REPLIT_DB_URL', '')
REPLIT_USERNAME = os.getenv('REPLIT_USERNAME', '')

# Check if running on Replit
def is_replit():
    """Check if the bot is running on Replit."""
    return bool(REPLIT_DB_URL or REPLIT_USERNAME)

# Replit-specific settings
if is_replit():
    print("🤖 Running on Replit - Keep-alive server enabled")
    
    # Use Replit's database if available
    if REPLIT_DB_URL:
        print("📊 Using Replit database")
        # You can implement Replit DB integration here if needed
    else:
        print("💾 Using local SQLite database")
else:
    print("🖥️ Running locally")


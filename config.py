"""
Configuration file for the Discord Personal Data Bot.
"""

import os
from typing import Optional

class Config:
    """Configuration settings for the bot."""
    
    # Discord Bot Token (required)
    DISCORD_BOT_TOKEN: str = os.getenv('DISCORD_BOT_TOKEN', '')
    
    # Database settings
    DATABASE_PATH: str = os.getenv('DATABASE_PATH', 'user_data.db')
    
    # OCR settings
    TESSERACT_PATH: Optional[str] = os.getenv('TESSERACT_PATH', None)
    
    # Logging settings
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'bot.log')
    
    # Bot behavior settings
    MAX_RECENT_MESSAGES: int = int(os.getenv('MAX_RECENT_MESSAGES', '50'))
    MAX_SEARCH_RESULTS: int = int(os.getenv('MAX_SEARCH_RESULTS', '10'))
    MAX_NOTES_DISPLAY: int = int(os.getenv('MAX_NOTES_DISPLAY', '10'))
    
    # Security settings
    ENABLE_DATA_ENCRYPTION: bool = os.getenv('ENABLE_DATA_ENCRYPTION', 'false').lower() == 'true'
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present."""
        if not cls.DISCORD_BOT_TOKEN:
            print("ERROR: DISCORD_BOT_TOKEN environment variable is required!")
            return False
        return True
    
    @classmethod
    def print_config(cls):
        """Print current configuration (without sensitive data)."""
        print("Bot Configuration:")
        print(f"  Database Path: {cls.DATABASE_PATH}")
        print(f"  Tesseract Path: {cls.TESSERACT_PATH or 'Default'}")
        print(f"  Log Level: {cls.LOG_LEVEL}")
        print(f"  Log File: {cls.LOG_FILE}")
        print(f"  Max Recent Messages: {cls.MAX_RECENT_MESSAGES}")
        print(f"  Max Search Results: {cls.MAX_SEARCH_RESULTS}")
        print(f"  Data Encryption: {'Enabled' if cls.ENABLE_DATA_ENCRYPTION else 'Disabled'}")
        print(f"  Bot Token: {'Set' if cls.DISCORD_BOT_TOKEN else 'Not Set'}")

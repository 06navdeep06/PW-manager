#!/usr/bin/env python3
"""
Simple startup script for the Discord Personal Data Bot.
This script checks configuration and starts the bot.
"""

import os
import sys
from config import Config

def main():
    """Main startup function."""
    print("Discord Personal Data Bot")
    print("=" * 30)
    
    # Validate configuration
    if not Config.validate():
        print("\nPlease set the required environment variables:")
        print("  DISCORD_BOT_TOKEN=your_bot_token_here")
        print("\nOptional variables:")
        print("  TESSERACT_PATH=path_to_tesseract (Windows only)")
        print("  DATABASE_PATH=path_to_database_file")
        sys.exit(1)
    
    # Print configuration
    Config.print_config()
    print("\nStarting bot...")
    
    # Import and run the bot
    try:
        from bot import main as bot_main
        bot_main()
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        print(f"\nError starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

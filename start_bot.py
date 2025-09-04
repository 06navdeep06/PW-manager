#!/usr/bin/env python3
"""
Production startup script for the Discord Personal Data Bot.
Includes validation, monitoring, and graceful shutdown handling.
"""

import sys
import os
import signal
import logging
import asyncio
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def setup_logging():
    """Setup comprehensive logging."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler('logs/bot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logging.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

def main():
    """Main startup function."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🤖 Starting Discord Personal Data Bot")
    logger.info("=" * 50)
    
    try:
        # Import and run validation
        from validate_setup import run_validation
        logger.info("Running setup validation...")
        if not run_validation():
            logger.error("❌ Setup validation failed!")
            return 1
        logger.info("✅ Setup validation passed!")
        
        # Import and start the bot
        from bot import main as bot_main
        logger.info("Starting bot...")
        bot_main()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

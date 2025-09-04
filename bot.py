"""
Discord Bot for Personal Data Storage
Main entry point for the Discord bot that handles DMs and stores user data.
"""

import discord
from discord.ext import commands
import logging
import os
import asyncio
import threading
import time
from collections import defaultdict
from storage import UserStorage
from ocr import ImageOCR
from commands import CommandHandler
from config import Config
from keep_alive import start_keep_alive
from monitoring import monitor, record_operation

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

class PersonalDataBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None  # Disable default help command
        )
        self.storage = UserStorage(Config.DATABASE_PATH)
        self.ocr = ImageOCR(Config.TESSERACT_PATH)
        self.command_handler = CommandHandler(self.storage, self.ocr)
        
        # Rate limiting
        self.user_message_times = defaultdict(list)
        self.max_messages_per_minute = 10
        self.max_commands_per_minute = 5
        
        # Security measures
        self.blocked_users = set()
        self.suspicious_patterns = [
            r'<@!?\d+>',  # User mentions
            r'<#\d+>',    # Channel mentions
            r'<@&\d+>',   # Role mentions
            r'<a?:\w+:\d+>',  # Emojis
        ]
        
    async def on_ready(self):
        """Called when the bot is ready and connected to Discord."""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Initialize storage
        await self.storage.initialize()
        
        # Start keep-alive task for Replit
        self.loop.create_task(self.keep_alive())
        
    async def on_message(self, message):
        """Handle incoming messages."""
        # Ignore messages from the bot itself
        if message.author == self.user:
            return
            
        # Only process Direct Messages
        if not isinstance(message.channel, discord.DMChannel):
            return
        
        # Security checks
        if message.author.id in self.blocked_users:
            return
            
        # Rate limiting
        if not await self._check_rate_limit(message.author.id, message.content.startswith('!')):
            await message.reply("⚠️ Rate limit exceeded. Please slow down.")
            return
        
        # Content sanitization
        if await self._is_suspicious_content(message.content):
            logger.warning(f"Suspicious content from {message.author.name}: {message.content[:100]}")
            await message.reply("⚠️ Your message contains potentially harmful content and was blocked.")
            return
            
        logger.info(f"DM from {message.author.name} ({message.author.id}): {message.content[:100]}...")
        
        # Record message processing
        monitor.record_message()
        
        # Check for wake-up command first
        if message.content.lower().startswith('!wake') or message.content.lower().startswith('!hey'):
            await self._handle_wake_up(message)
            return
        
        # Store the message content
        await self.storage.store_message(
            user_id=message.author.id,
            content=message.content,
            message_type="text"
        )
        
        # Handle attachments (images)
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    logger.info(f"Processing image from {message.author.name}")
                    try:
                        # Check file size (limit to 10MB)
                        if attachment.size > 10 * 1024 * 1024:
                            await self.storage.store_message(
                                user_id=message.author.id,
                                content=f"[IMAGE ERROR] Image too large ({attachment.size} bytes). Maximum size is 10MB.",
                                message_type="error"
                            )
                            continue
                        
                        # Download and process image
                        image_data = await attachment.read()
                        extracted_text = await self.ocr.extract_text(image_data)
                        
                        if extracted_text:
                            # Store the original OCR text as a message
                            await self.storage.store_message(
                                user_id=message.author.id,
                                content=f"[IMAGE OCR] {extracted_text}",
                                message_type="image_ocr"
                            )
                            
                            # Process the extracted text through auto-categorization
                            # This will automatically detect and store passwords, emails, links, etc.
                            await self.command_handler._auto_categorize_and_store(
                                user_id=message.author.id,
                                content=extracted_text
                            )
                            
                            logger.info(f"OCR extracted and categorized text: {extracted_text[:100]}...")
                        else:
                            await self.storage.store_message(
                                user_id=message.author.id,
                                content=f"[IMAGE OCR] No text found in image",
                                message_type="image_ocr"
                            )
                    except Exception as e:
                        logger.error(f"Error processing image: {e}")
                        await self.storage.store_message(
                            user_id=message.author.id,
                            content=f"[IMAGE ERROR] Failed to process image: {str(e)}",
                            message_type="error"
                        )
        
        # Check for commands
        if message.content.startswith('!'):
            try:
                monitor.record_command()
                response = await self.command_handler.handle_command(
                    user_id=message.author.id,
                    command=message.content
                )
                if response:
                    await message.reply(response)
            except Exception as e:
                monitor.record_error("command_error", str(e))
                logger.error(f"Error handling command: {e}")
                await message.reply("Sorry, there was an error processing your command.")
        else:
            # Auto-categorize and store non-command messages
            try:
                await self.command_handler._auto_categorize_and_store(
                    user_id=message.author.id,
                    content=message.content
                )
            except Exception as e:
                logger.error(f"Error auto-categorizing message: {e}")
    
    async def _handle_wake_up(self, message):
        """Handle wake-up command and process entire conversation."""
        user_id = message.author.id
        logger.info(f"Wake-up command from {message.author.name}")
        
        # Get all messages from the user
        all_messages = await self.storage.get_recent_messages(user_id, 100)  # Get last 100 messages
        
        if not all_messages:
            await message.reply("👋 Hello! I'm awake and ready to help. No previous conversation found.")
            return
        
        # Process and categorize all messages
        await self._process_conversation_history(user_id, all_messages)
        
        # Generate a comprehensive response
        response = await self._generate_conversation_summary(user_id, all_messages)
        await message.reply(response)
    
    async def _process_conversation_history(self, user_id: str, messages: list):
        """Process entire conversation history and categorize content."""
        logger.info(f"Processing {len(messages)} messages for user {user_id}")
        
        # Track what we've already processed to avoid duplicates
        processed_content = set()
        
        for msg in messages:
            if msg['type'] not in ['text', 'image_ocr']:
                continue
                
            content = msg['content']
            if content.startswith('[IMAGE OCR]'):
                content = content[11:].strip()  # Remove prefix
            elif content.startswith('[IMAGE ERROR]'):
                continue  # Skip error messages
            elif content.startswith('!'):
                continue  # Skip commands
            
            # Skip if we've already processed this exact content
            content_hash = hash(content.strip())
            if content_hash in processed_content:
                continue
            processed_content.add(content_hash)
            
            # Auto-categorize the content
            await self.command_handler._auto_categorize_and_store(user_id, content)
    
    async def _generate_conversation_summary(self, user_id: str, messages: list) -> str:
        """Generate a comprehensive summary of the conversation."""
        # Get categorized data
        categories = await self.storage.get_all_categories(user_id)
        notes = await self.storage.get_notes(user_id)
        emails = await self.storage.get_emails(user_id)
        links = await self.storage.get_links(user_id)
        
        response = "🤖 **I'm awake and ready!** Here's what I found in our conversation:\n\n"
        
        # Summary of data
        response += "📊 **Your Data Summary:**\n"
        response += f"• 📝 Total Messages: {categories['total_messages']}\n"
        response += f"• 🔑 Passwords: {categories['passwords']}\n"
        response += f"• 👤 Credentials: {categories['credentials']}\n"
        response += f"• 📄 Notes: {categories['notes']}\n"
        response += f"• 📧 Emails: {categories['emails']}\n"
        response += f"• 🔗 Links: {categories['links']}\n\n"
        
        # Recent highlights
        credentials = await self.storage.get_all_credentials(user_id)
        if credentials:
            response += "👤 **Recent Credentials:**\n"
            for cred in credentials[:3]:  # Show 3 most recent
                response += f"• **{cred['label']}**: {cred['username']}\n"
            response += "\n"
        
        if notes:
            response += "📝 **Recent Notes:**\n"
            for note in notes[:3]:  # Show 3 most recent
                response += f"• {note[:100]}{'...' if len(note) > 100 else ''}\n"
            response += "\n"
        
        if emails:
            response += "📧 **Saved Emails:**\n"
            for email_data in emails[:3]:  # Show 3 most recent
                response += f"• {email_data['email']}\n"
            response += "\n"
        
        if links:
            response += "🔗 **Saved Links:**\n"
            for link_data in links[:3]:  # Show 3 most recent
                link_type = f" [{link_data['type']}]" if link_data['type'] else ""
                response += f"• {link_data['url']}{link_type}\n"
            response += "\n"
        
        # Available commands
        response += "💡 **Available Commands:**\n"
        response += "• `!get password <label>` - Get a saved password\n"
        response += "• `!get credentials` - Get all your credentials\n"
        response += "• `!get credential <label>` - Get specific credentials\n"
        response += "• `!get notes` - Get all your notes\n"
        response += "• `!get emails` - Get all your emails\n"
        response += "• `!get links` - Get all your links\n"
        response += "• `!search <term>` - Search through your data\n"
        response += "• `!recent [number]` - Show recent messages\n"
        response += "• `!list` - Show data summary\n"
        response += "• `!help` - Show all commands\n\n"
        
        response += "💬 **Just send me any message and I'll store it!** I'll categorize passwords, emails, links, and notes automatically."
        
        return response
    
    async def _check_rate_limit(self, user_id: int, is_command: bool = False) -> bool:
        """Check if user is within rate limits."""
        current_time = time.time()
        user_times = self.user_message_times[user_id]
        
        # Clean old entries (older than 1 minute)
        user_times[:] = [t for t in user_times if current_time - t < 60]
        
        # Check limits
        max_allowed = self.max_commands_per_minute if is_command else self.max_messages_per_minute
        
        if len(user_times) >= max_allowed:
            return False
        
        # Add current message time
        user_times.append(current_time)
        return True
    
    async def _is_suspicious_content(self, content: str) -> bool:
        """Check if content contains suspicious patterns."""
        import re
        
        # Check for suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, content):
                return True
        
        # Check for excessive length
        if len(content) > 2000:
            return True
        
        # Check for potential spam patterns
        if content.count('!') > 10:  # Too many commands
            return True
        
        return False
    
    async def keep_alive(self):
        """Keep the bot alive on Replit by pinging every 5 minutes."""
        while True:
            try:
                # Ping every 5 minutes to keep Replit alive
                await asyncio.sleep(300)  # 5 minutes
                logger.info("Keep-alive ping sent")
            except Exception as e:
                logger.error(f"Error in keep-alive: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

def main():
    """Main function to run the bot."""
    # Validate configuration
    if not Config.validate():
        return
    
    # Run setup validation
    try:
        from validate_setup import run_validation
        if not run_validation():
            logger.error("Setup validation failed. Please fix the issues and try again.")
            return
    except ImportError:
        logger.warning("Setup validation script not found, skipping validation")
    
    # Start keep-alive server for Replit
    start_keep_alive()
    
    # Create and run the bot
    bot = PersonalDataBot()
    
    try:
        logger.info("Starting Discord bot...")
        bot.run(Config.DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid Discord bot token!")
        monitor.record_error("login_failure", "Invalid bot token")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        monitor.record_error("bot_startup_error", str(e))

if __name__ == "__main__":
    main()

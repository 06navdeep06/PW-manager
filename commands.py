"""
Command Handler Module
Handles Discord bot commands and trigger words for user interactions.
"""

import re
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class CommandHandler:
    """Handles command processing and responses."""
    
    def __init__(self, storage, ocr):
        self.storage = storage
        self.ocr = ocr
        
        # Email regex pattern
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # URL regex pattern
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        
        # YouTube URL pattern
        self.youtube_pattern = re.compile(
            r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})'
        )
    
    async def handle_command(self, user_id: str, command: str) -> Optional[str]:
        """
        Handle incoming commands from users.
        
        Args:
            user_id: Discord user ID
            command: The command string
            
        Returns:
            Response message or None if no response needed
        """
        command = command.strip().lower()
        
        try:
            # Handle different command types
            if command.startswith('!get password'):
                return await self._handle_get_password(user_id, command)
            elif command.startswith('!get credentials'):
                return await self._handle_get_credentials(user_id)
            elif command.startswith('!get credential'):
                return await self._handle_get_credential(user_id, command)
            elif command.startswith('!get notes'):
                return await self._handle_get_notes(user_id)
            elif command.startswith('!get emails'):
                return await self._handle_get_emails(user_id)
            elif command.startswith('!get links'):
                return await self._handle_get_links(user_id)
            elif command.startswith('!list'):
                return await self._handle_list(user_id)
            elif command.startswith('!clear'):
                return await self._handle_clear(user_id)
            elif command.startswith('!help'):
                return await self._handle_help()
            elif command.startswith('!recent'):
                return await self._handle_recent(user_id, command)
            elif command.startswith('!search'):
                return await self._handle_search(user_id, command)
            else:
                # Auto-categorize and store the message
                await self._auto_categorize_and_store(user_id, command)
                return None
                
        except Exception as e:
            logger.error(f"Error handling command '{command}': {e}")
            return "Sorry, there was an error processing your command."
    
    async def _handle_get_password(self, user_id: str, command: str) -> str:
        """Handle !get password <label> command."""
        parts = command.split()
        if len(parts) < 3:
            return "Usage: `!get password <label>`"
        
        label = ' '.join(parts[2:])
        password = await self.storage.get_password(user_id, label)
        
        if password:
            return f"Password for '{label}': `{password}`"
        else:
            return f"No password found for label '{label}'"
    
    async def _handle_get_notes(self, user_id: str) -> str:
        """Handle !get notes command."""
        notes = await self.storage.get_notes(user_id)
        
        if not notes:
            return "No notes found."
        
        response = "**Your Notes:**\n"
        for i, note in enumerate(notes[:10], 1):  # Limit to 10 most recent
            response += f"{i}. {note}\n"
        
        if len(notes) > 10:
            response += f"\n... and {len(notes) - 10} more notes."
        
        return response
    
    async def _handle_get_credentials(self, user_id: str) -> str:
        """Handle !get credentials command."""
        credentials = await self.storage.get_all_credentials(user_id)
        
        if not credentials:
            return "No credentials found."
        
        response = "**Your Credentials:**\n"
        for i, cred in enumerate(credentials[:10], 1):  # Limit to 10 most recent
            response += f"{i}. **{cred['label']}**\n"
            response += f"   Username: `{cred['username']}`\n"
            response += f"   Password: `{cred['password']}`\n\n"
        
        if len(credentials) > 10:
            response += f"... and {len(credentials) - 10} more credentials."
        
        return response
    
    async def _handle_get_credential(self, user_id: str, command: str) -> str:
        """Handle !get credential <label> command."""
        parts = command.split()
        if len(parts) < 3:
            return "Usage: `!get credential <label>`"
        
        label = ' '.join(parts[2:])
        credential = await self.storage.get_credential(user_id, label)
        
        if credential:
            return f"**{label}:**\nUsername: `{credential['username']}`\nPassword: `{credential['password']}`"
        else:
            return f"No credentials found for label '{label}'"
    
    async def _handle_get_emails(self, user_id: str) -> str:
        """Handle !get emails command."""
        emails = await self.storage.get_emails(user_id)
        
        if not emails:
            return "No emails found."
        
        response = "**Your Emails:**\n"
        for i, email_data in enumerate(emails[:10], 1):  # Limit to 10 most recent
            label = f" ({email_data['label']})" if email_data['label'] else ""
            response += f"{i}. {email_data['email']}{label}\n"
        
        if len(emails) > 10:
            response += f"\n... and {len(emails) - 10} more emails."
        
        return response
    
    async def _handle_get_links(self, user_id: str) -> str:
        """Handle !get links command."""
        links = await self.storage.get_links(user_id)
        
        if not links:
            return "No links found."
        
        response = "**Your Links:**\n"
        for i, link_data in enumerate(links[:10], 1):  # Limit to 10 most recent
            link_type = f" [{link_data['type']}]" if link_data['type'] else ""
            response += f"{i}. {link_data['url']}{link_type}\n"
        
        if len(links) > 10:
            response += f"\n... and {len(links) - 10} more links."
        
        return response
    
    async def _handle_list(self, user_id: str) -> str:
        """Handle !list command."""
        categories = await self.storage.get_all_categories(user_id)
        
        response = "**Your Stored Data:**\n"
        response += f"📝 Total Messages: {categories['total_messages']}\n"
        response += f"🔑 Passwords: {categories['passwords']}\n"
        response += f"👤 Credentials: {categories['credentials']}\n"
        response += f"📄 Notes: {categories['notes']}\n"
        response += f"📧 Emails: {categories['emails']}\n"
        response += f"🔗 Links: {categories['links']}\n"
        
        if sum(categories.values()) == 0:
            response = "No data stored yet. Send me messages, passwords, notes, emails, or links!"
        
        return response
    
    async def _handle_clear(self, user_id: str) -> str:
        """Handle !clear command."""
        await self.storage.clear_user_data(user_id)
        return "✅ All your data has been cleared."
    
    async def _handle_help(self) -> str:
        """Handle !help command."""
        return """**Available Commands:**

`!wake` or `!hey` - Wake up the bot and get conversation summary
`!get password <label>` - Get a saved password
`!get credentials` - Get all your saved credentials (username/password)
`!get credential <label>` - Get specific credentials by label
`!get notes` - Get all your notes
`!get emails` - Get all your saved emails
`!get links` - Get all your saved links
`!list` - List all your stored data categories
`!clear` - Clear all your data
`!recent [number]` - Show recent messages (default: 5)
`!search <term>` - Search through your stored data
`!help` - Show this help message

**Auto-detection:**
- **Credentials**: `username: user password: pass` or `Gmail - username: user password: pass`
- **Passwords**: `password: <label> <password>`
- **Notes**: Just send any text
- **Emails**: Any email address will be saved
- **Links**: Any URL will be saved (YouTube, GitHub, etc.)
- **Images**: OCR text will be extracted and saved

**💡 Tip:** Use `!wake` to get a complete summary of our conversation!"""
    
    async def _handle_recent(self, user_id: str, command: str) -> str:
        """Handle !recent command."""
        parts = command.split()
        limit = 5
        
        if len(parts) > 1:
            try:
                limit = int(parts[1])
                limit = min(limit, 20)  # Cap at 20
            except ValueError:
                pass
        
        messages = await self.storage.get_recent_messages(user_id, limit)
        
        if not messages:
            return "No recent messages found."
        
        response = f"**Recent Messages ({len(messages)}):**\n"
        for i, msg in enumerate(messages, 1):
            content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            response += f"{i}. [{msg['type']}] {content}\n"
        
        return response
    
    async def _handle_search(self, user_id: str, command: str) -> str:
        """Handle !search command."""
        parts = command.split()
        if len(parts) < 2:
            return "Usage: `!search <term>`"
        
        search_term = ' '.join(parts[1:]).lower()
        messages = await self.storage.get_recent_messages(user_id, 50)  # Search in last 50 messages
        
        matches = []
        for msg in messages:
            if search_term in msg['content'].lower():
                matches.append(msg)
        
        if not matches:
            return f"No matches found for '{search_term}'"
        
        response = f"**Search Results for '{search_term}' ({len(matches)} matches):**\n"
        for i, msg in enumerate(matches[:10], 1):  # Limit to 10 results
            content = msg['content'][:150] + "..." if len(msg['content']) > 150 else msg['content']
            response += f"{i}. [{msg['type']}] {content}\n"
        
        if len(matches) > 10:
            response += f"\n... and {len(matches) - 10} more matches."
        
        return response
    
    async def _auto_categorize_and_store(self, user_id: str, content: str):
        """Automatically categorize and store different types of content."""
        if not content or not content.strip():
            return
            
        content_lower = content.lower()
        
        # Enhanced credential patterns - check for various username/password combinations
        credential_patterns = [
            # Pattern 1: "username: user password: pass" or "user: user pass: pass"
            r'(?:username|user|id|email|login):\s*([^\s]+)\s+(?:password|pass|pwd):\s*([^\s]+)',
            # Pattern 2: "label - username: user password: pass"
            r'([^:]+?)\s*[-–]\s*(?:username|user|id|email|login):\s*([^\s]+)\s+(?:password|pass|pwd):\s*([^\s]+)',
            # Pattern 3: "label: username/password" or "label: user:pass"
            r'([^:]+?):\s*(?:username|user|id|email|login):\s*([^\s/]+)[/\s]+(?:password|pass|pwd):\s*([^\s]+)',
            # Pattern 4: "label: user pass" (simple format)
            r'([^:]+?):\s*([^\s]+)\s+([^\s]+)',
            # Pattern 5: "username/password" or "user:pass" (no label)
            r'(?:username|user|id|email|login):\s*([^\s/]+)[/\s]+(?:password|pass|pwd):\s*([^\s]+)',
            # Pattern 6: "label - user:pass" format
            r'([^:]+?)\s*[-–]\s*([^\s]+):([^\s]+)',
        ]
        
        for pattern in credential_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    # Pattern 5: username/password without label
                    username, password = groups
                    label = f"Account_{username}"
                    await self.storage.store_credential(user_id, label, username, password)
                    logger.info(f"Stored credentials for user {user_id}: {label}")
                    return
                elif len(groups) == 3:
                    # Patterns 2, 3, 4, 6: label, username, password
                    label, username, password = groups
                    if label and username and password:
                        await self.storage.store_credential(user_id, label.strip(), username.strip(), password.strip())
                        logger.info(f"Stored credentials for user {user_id}: {label}")
                        return
        
        # Legacy password pattern: "password: <label> <password>"
        password_match = re.match(r'password:\s*([^:]+?)\s+(.+)', content, re.IGNORECASE)
        if password_match:
            label = password_match.group(1).strip()
            password = password_match.group(2).strip()
            if label and password:
                await self.storage.store_password(user_id, label, password)
                logger.info(f"Stored password for user {user_id} with label '{label}'")
            return
        
        # Check for email addresses
        emails = self.email_pattern.findall(content)
        for email in emails:
            if email and email.strip():
                await self.storage.store_email(user_id, email.strip())
                logger.info(f"Stored email for user {user_id}: {email}")
        
        # Check for URLs
        urls = self.url_pattern.findall(content)
        for url in urls:
            if url and url.strip():
                # Determine link type
                link_type = "general"
                url_lower = url.lower()
                if self.youtube_pattern.search(url):
                    link_type = "youtube"
                elif "github.com" in url_lower:
                    link_type = "github"
                elif "stackoverflow.com" in url_lower:
                    link_type = "stackoverflow"
                elif "youtube.com" in url_lower or "youtu.be" in url_lower:
                    link_type = "youtube"
                elif "reddit.com" in url_lower:
                    link_type = "reddit"
                elif "twitter.com" in url_lower or "x.com" in url_lower:
                    link_type = "twitter"
                
                await self.storage.store_link(user_id, url.strip(), link_type)
                logger.info(f"Stored {link_type} link for user {user_id}: {url}")
        
        # If it's not a command and contains text, store as a note
        if not content.startswith('!') and content.strip():
            # Don't store if it's just an email or URL (already stored above)
            if not emails and not urls:
                await self.storage.store_note(user_id, content.strip())
                logger.info(f"Stored note for user {user_id}")
    
    def is_valid_url(self, url: str) -> bool:
        """Check if a string is a valid URL."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

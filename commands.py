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
        
        # Basic content validation
        if len(content) > 10000:
            logger.warning(f"Content too long from user {user_id}, truncating")
            content = content[:10000]
        
        # Clean up content for better processing (especially important for OCR text)
        content = self._clean_text_content(content)
        content_lower = content.lower()
        
        # Enhanced credential patterns - check for various username/password combinations
        # These patterns are designed to handle OCR text which may have spacing issues
        credential_patterns = [
            # Pattern 1: "username: user password: pass" or "user: user pass: pass" (flexible spacing)
            r'(?:username|user|id|email|login)\s*:\s*([^\s:]+)\s+(?:password|pass|pwd)\s*:\s*([^\s]+)',
            # Pattern 2: "label - username: user password: pass" (flexible spacing and separators)
            r'([^:\n]+?)\s*[-–—]\s*(?:username|user|id|email|login)\s*:\s*([^\s:]+)\s+(?:password|pass|pwd)\s*:\s*([^\s]+)',
            # Pattern 3: "label: username user password pass" (colon format with flexible spacing)
            r'([^:\n]+?)\s*:\s*(?:username|user|id|email|login)\s+([^\s]+)\s+(?:password|pass|pwd)\s+([^\s]+)',
            # Pattern 4: "label user pass" (simple format, three words)
            r'([a-zA-Z][a-zA-Z0-9\s]{2,15})\s+([^\s]{3,})\s+([^\s]{3,})',
            # Pattern 5: "username user password pass" (no colon, flexible spacing)
            r'(?:username|user|id|email|login)\s+([^\s]{3,})\s+(?:password|pass|pwd)\s+([^\s]{3,})',
            # Pattern 6: "label - user:pass" or "label user:pass" format
            r'([^:\n]+?)\s*[-–—]?\s*([^\s:]+)\s*:\s*([^\s]+)',
            # Pattern 7: Line-based credentials (each on separate line)
            r'([a-zA-Z][a-zA-Z0-9\s]+)\n\s*([^\s\n]+)\n\s*([^\s\n]+)',
            # Pattern 8: Account/Service credentials with various formats
            r'(?:account|service|site|app|login)\s*[-–—:]?\s*([^:\n]+?)\s*[-–—:]\s*([^\s]+)\s*[-–—:]\s*([^\s]+)',
        ]
        
        for pattern in credential_patterns:
            try:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    if len(groups) == 2:
                        # Pattern 5: username/password without label
                        username, password = groups
                        if username and password and len(username) < 200 and len(password) < 500:
                            label = f"Account_{username}"
                            await self.storage.store_credential(user_id, label, username, password)
                            logger.info(f"Stored credentials for user {user_id}: {label}")
                            return
                    elif len(groups) == 3:
                        # Patterns 2, 3, 4, 6: label, username, password
                        label, username, password = groups
                        if (label and username and password and 
                            len(label) < 200 and len(username) < 200 and len(password) < 500):
                            await self.storage.store_credential(user_id, label.strip(), username.strip(), password.strip())
                            logger.info(f"Stored credentials for user {user_id}: {label}")
                            return
            except Exception as e:
                logger.error(f"Error processing credential pattern: {e}")
                continue
        
        # Legacy password pattern: "password: <label> <password>"
        password_match = re.match(r'password:\s*([^:]+?)\s+(.+)', content, re.IGNORECASE)
        if password_match:
            label = password_match.group(1).strip()
            password = password_match.group(2).strip()
            if label and password:
                await self.storage.store_password(user_id, label, password)
                logger.info(f"Stored password for user {user_id} with label '{label}'")
            return
        
        # Check for email addresses with enhanced patterns for OCR text
        email_patterns = [
            self.email_pattern,  # Original pattern
            # OCR-friendly pattern that handles common OCR mistakes
            re.compile(r'\b[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            # Pattern that handles spaces around @ and dots (common OCR errors)
            re.compile(r'\b[A-Za-z0-9._%-]+\s*@\s*[A-Za-z0-9.-]+\s*\.\s*[A-Z|a-z]{2,}\b'),
        ]
        
        emails_found = set()
        for pattern in email_patterns:
            emails = pattern.findall(content)
            for email in emails:
                # Clean up the email (remove spaces around @ and dots)
                clean_email = re.sub(r'\s*@\s*', '@', email)
                clean_email = re.sub(r'\s*\.\s*', '.', clean_email)
                
                if clean_email and clean_email.strip() and '@' in clean_email and '.' in clean_email:
                    emails_found.add(clean_email.strip())
        
        for email in emails_found:
            await self.storage.store_email(user_id, email)
            logger.info(f"Stored email for user {user_id}: {email}")
        
        # Check for URLs with enhanced patterns for OCR text
        url_patterns = [
            self.url_pattern,  # Original pattern
            # Pattern that handles spaces in URLs (common OCR error)
            re.compile(r'http[s]?\s*:\s*//\s*(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F])|\s)+'),
            # Pattern for URLs without http/https
            re.compile(r'\b(?:www\.)?[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}(?:/[^\s]*)?'),
        ]
        
        urls_found = set()
        for pattern in url_patterns:
            urls = pattern.findall(content)
            for url in urls:
                # Clean up the URL (remove spaces)
                clean_url = re.sub(r'\s+', '', url)
                
                # Add http:// if missing
                if clean_url and not clean_url.startswith(('http://', 'https://')):
                    clean_url = 'http://' + clean_url
                
                if clean_url and self.is_valid_url(clean_url):
                    urls_found.add(clean_url)
        
        for url in urls_found:
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
            
            await self.storage.store_link(user_id, url, link_type)
            logger.info(f"Stored {link_type} link for user {user_id}: {url}")
        
        # If it's not a command and contains text, store as a note
        if not content.startswith('!') and content.strip():
            # Don't store if it's just an email or URL (already stored above)
            # Also check if content was already processed as credentials
            content_has_structured_data = bool(emails_found or urls_found)
            
            # Only store as note if there's meaningful text beyond structured data
            if not content_has_structured_data or len(content.strip()) > 50:
                await self.storage.store_note(user_id, content.strip())
                logger.info(f"Stored note for user {user_id}")
    
    def _clean_text_content(self, content: str) -> str:
        """Clean and normalize text content, especially useful for OCR text."""
        if not content:
            return content
        
        # Remove excessive whitespace and normalize line breaks
        lines = []
        for line in content.split('\n'):
            cleaned_line = ' '.join(line.split())  # Remove extra spaces
            if cleaned_line:
                lines.append(cleaned_line)
        
        content = '\n'.join(lines)
        
        # Common OCR corrections
        replacements = {
            # Common OCR character misreads
            '0': 'O',  # zero to O in passwords/usernames
            '1': 'I',  # one to I
            '|': 'I',  # pipe to I
            '5': 'S',  # five to S
            # Normalize punctuation
            '"': '"',  # smart quotes
            '"': '"',
            ''': "'",
            ''': "'",
            '–': '-',  # em dash to hyphen
            '—': '-',
        }
        
        # Apply replacements only in contexts where they make sense
        # Be conservative to avoid corrupting actual data
        words = content.split()
        cleaned_words = []
        
        for word in words:
            # Only apply OCR corrections to likely username/password fields
            if any(keyword in content.lower() for keyword in ['username', 'password', 'user', 'pass', 'login', 'email']):
                for old, new in replacements.items():
                    if old in word and len(word) > 2:  # Only replace in longer words
                        word = word.replace(old, new)
            cleaned_words.append(word)
        
        return ' '.join(cleaned_words)
    
    def is_valid_url(self, url: str) -> bool:
        """Check if a string is a valid URL."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

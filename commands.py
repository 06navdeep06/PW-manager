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
        
        # Smart password and credential detection patterns
        # Detect any potential password-like content automatically
        potential_credentials = self._detect_credentials_intelligently(content)
        for cred in potential_credentials:
            try:
                if cred['type'] == 'credential':
                    await self.storage.store_credential(user_id, cred['label'], cred['username'], cred['password'])
                    logger.info(f"Auto-detected and stored credentials for user {user_id}: {cred['label']}")
                elif cred['type'] == 'password':
                    await self.storage.store_password(user_id, cred['label'], cred['password'])
                    logger.info(f"Auto-detected and stored password for user {user_id}: {cred['label']}")
            except Exception as e:
                logger.error(f"Error storing auto-detected credential: {e}")
                continue
        
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
    
    def _detect_credentials_intelligently(self, content: str) -> list:
        """
        Intelligently detect passwords and credentials from any text format.
        Uses multiple heuristics to identify password-like content.
        """
        credentials = []
        words = content.split()
        lines = content.split('\n')
        
        # Heuristic 1: Look for password-like strings (8+ chars with mixed case/numbers/symbols)
        potential_passwords = []
        for word in words:
            if self._looks_like_password(word):
                potential_passwords.append(word)
        
        # Heuristic 2: Context-based detection - look for words near password indicators
        password_indicators = ['password', 'pass', 'pwd', 'key', 'secret', 'token', 'auth', 'login']
        username_indicators = ['username', 'user', 'email', 'login', 'id', 'account']
        
        for i, word in enumerate(words):
            word_lower = word.lower()
            
            # Check if current word is a password indicator
            if any(indicator in word_lower for indicator in password_indicators):
                # Look for password in next few words
                for j in range(i+1, min(i+5, len(words))):
                    next_word = words[j]
                    if self._looks_like_password(next_word) or len(next_word) >= 6:
                        # Try to find a label (look backwards)
                        label = self._find_label_before(words, i)
                        credentials.append({
                            'type': 'password',
                            'label': label or 'Detected',
                            'password': next_word
                        })
                        break
            
            # Check for username/password pairs
            elif any(indicator in word_lower for indicator in username_indicators):
                # Look for username and password in next few words
                username = None
                password = None
                
                for j in range(i+1, min(i+6, len(words))):
                    if not username and self._looks_like_username(words[j]):
                        username = words[j]
                    elif username and self._looks_like_password(words[j]):
                        password = words[j]
                        break
                
                if username and password:
                    label = self._find_label_before(words, i) or username
                    credentials.append({
                        'type': 'credential',
                        'label': label,
                        'username': username,
                        'password': password
                    })
        
        # Heuristic 3: Line-based detection for structured data
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for "key: value" patterns
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower()
                    value = parts[1].strip()
                    
                    # Check if key suggests this is a password
                    if any(indicator in key for indicator in password_indicators) and value:
                        label = key.replace('password', '').replace('pass', '').replace('pwd', '').strip()
                        if not label:
                            label = 'Detected'
                        credentials.append({
                            'type': 'password',
                            'label': label.title(),
                            'password': value
                        })
        
        # Heuristic 4: Pattern-free detection - just look for password-like strings with context
        for i, word in enumerate(words):
            if self._looks_like_password(word):
                # Check if there's context around it
                context_words = []
                for j in range(max(0, i-3), min(len(words), i+4)):
                    if j != i:
                        context_words.append(words[j].lower())
                
                # If there's password-related context, store it
                if any(indicator in ' '.join(context_words) for indicator in password_indicators + username_indicators):
                    label = self._find_label_before(words, i) or 'Detected'
                    credentials.append({
                        'type': 'password',
                        'label': label,
                        'password': word
                    })
        
        # Remove duplicates based on password value
        seen_passwords = set()
        unique_credentials = []
        for cred in credentials:
            password = cred.get('password', '')
            if password not in seen_passwords:
                seen_passwords.add(password)
                unique_credentials.append(cred)
        
        return unique_credentials
    
    def _looks_like_password(self, word: str) -> bool:
        """Check if a word looks like a password."""
        if len(word) < 6:
            return False
        
        # Basic password characteristics
        has_upper = any(c.isupper() for c in word)
        has_lower = any(c.islower() for c in word)
        has_digit = any(c.isdigit() for c in word)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in word)
        
        # Strong password indicators
        if len(word) >= 8 and sum([has_upper, has_lower, has_digit, has_special]) >= 3:
            return True
        
        # Medium password indicators
        if len(word) >= 10 and sum([has_upper, has_lower, has_digit]) >= 2:
            return True
        
        # Look for common password patterns
        common_patterns = ['123', 'abc', 'qwerty', 'password', 'admin']
        if any(pattern in word.lower() for pattern in common_patterns):
            return len(word) >= 6
        
        return False
    
    def _looks_like_username(self, word: str) -> bool:
        """Check if a word looks like a username."""
        if len(word) < 3 or len(word) > 50:
            return False
        
        # Email-like usernames
        if '@' in word:
            return True
        
        # Alphanumeric with some special chars
        if re.match(r'^[a-zA-Z0-9._-]+$', word):
            return True
        
        return False
    
    def _find_label_before(self, words: list, index: int) -> str:
        """Find a suitable label before the given index."""
        # Look backwards for a potential label
        for i in range(index-1, max(0, index-4), -1):
            word = words[i]
            # Skip common words
            if word.lower() in ['for', 'the', 'my', 'is', 'to', 'and', 'or', ':', '-', '–', '—']:
                continue
            # Clean up the word and use it as label
            label = word.strip(':-–—').strip()
            if len(label) > 1 and len(label) < 50:
                return label.title()
        
        return None

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

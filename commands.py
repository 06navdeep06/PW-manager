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
            elif command.startswith('!store') or command.startswith('!save'):
                return await self._handle_quick_store(user_id, command)
            elif command.startswith('!add'):
                return await self._handle_add(user_id, command)
            elif command.startswith('!list'):
                return await self._handle_list(user_id)
            elif command.startswith('!clear duplicates'):
                return await self._handle_clear_duplicates(user_id)
            elif command.startswith('!clear'):
                return await self._handle_clear(user_id)
            elif command.startswith('!help'):
                return await self._handle_help()
            elif command.startswith('!recent'):
                return await self._handle_recent(user_id, command)
            elif command.startswith('!search'):
                return await self._handle_search(user_id, command)
            else:
                # Don't auto-categorize commands that start with ! but aren't recognized
                if command.startswith('!'):
                    return "❌ Unknown command. Type `!help` to see all available commands."
                else:
                    # Auto-categorize and store non-command messages
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
    
    async def _handle_clear_duplicates(self, user_id: str) -> str:
        """Handle !clear duplicates command."""
        try:
            await self.storage.clear_duplicates(user_id)
            return "✅ Duplicate entries have been removed from your data."
        except Exception as e:
            logger.error(f"Error clearing duplicates for user {user_id}: {e}")
            return "❌ Error clearing duplicates. Please try again."
    
    async def _handle_help(self) -> str:
        """Handle !help command."""
        return """**🤖 Personal Data Bot - Help**

**📥 QUICK STORAGE COMMANDS:**
`!store <service> <username> <password>` - Store credentials
`!store <service> <password>` - Store password only
`!save <service> <username> <password>` - Same as !store
`!add <anything>` - Smart auto-detection and storage

**📤 RETRIEVAL COMMANDS:**
`!get password <label>` - Get a saved password
`!get credentials` - Get all your saved credentials
`!get credential <label>` - Get specific credentials by label
`!get notes` - Get all your notes
`!get emails` - Get all your saved emails
`!get links` - Get all your saved links

**🔍 SEARCH & MANAGE:**
`!search <term>` - Search through your stored data
`!recent [number]` - Show recent messages (default: 5)
`!list` - List all your stored data categories
`!clear` - Clear all your data
`!wake` or `!hey` - Get conversation summary

**🎯 CONVENIENT INPUT FORMATS:**
• **Simple**: `gmail john@email.com mypass123`
• **With slash**: `Netflix: user123/pass456`
• **With keywords**: `user john password abc123 for Gmail`
• **Line format**: `Gmail\nuser: john\npass: abc123`
• **Quick password**: `password gmail: mypass123`
• **Two words**: `netflix mypassword123`

**🔄 AUTO-DETECTION:**
- **Emails**: Any email address will be saved
- **Links**: Any URL will be saved (YouTube, GitHub, etc.)
- **Images**: OCR text will be extracted and categorized
- **Notes**: Any other text becomes a note

**💡 Pro Tips:**
• Just send any message - I'll categorize it automatically!
• Use `!wake` to get a complete summary of our conversation
• Use quotes for services with spaces: `!store "My Bank" user pass`"""
    
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
    
    async def _handle_quick_store(self, user_id: str, command: str) -> str:
        """Handle !store and !save commands for quick credential storage."""
        # Remove the command prefix and get the content
        content = command[6:].strip() if command.startswith('!store') else command[5:].strip()
        
        if not content:
            return """**Quick Store Usage:**
`!store service username password` - Store credentials
`!store service password` - Store password only
`!save Gmail john@email.com mypass123` - Same as store
`!store Netflix mypassword` - Store password for Netflix

**Examples:**
• `!store Gmail john@email.com mypass123`
• `!save Netflix user123 pass456`
• `!store "My Bank" username123 secretpass`
• `!store Reddit mypassword123`"""
        
        # Try to parse the content using our convenient detection
        credentials = self._detect_convenient_formats(content)
        
        if not credentials:
            # Try a simple split approach
            parts = content.split()
            if len(parts) == 3:
                # service username password
                service, username, password = parts
                credentials = [{
                    'type': 'credential',
                    'label': service.strip('"\'').title(),
                    'username': username,
                    'password': password
                }]
            elif len(parts) == 2:
                # service password
                service, password = parts
                credentials = [{
                    'type': 'password',
                    'label': service.strip('"\'').title(),
                    'password': password
                }]
        
        if not credentials:
            return "❌ Could not parse your input. Use format: `!store service username password` or `!store service password`"
        
        # Store the detected credentials
        stored_count = 0
        for cred in credentials:
            try:
                if cred['type'] == 'credential':
                    await self.storage.store_credential(user_id, cred['label'], cred['username'], cred['password'])
                    stored_count += 1
                elif cred['type'] == 'password':
                    await self.storage.store_password(user_id, cred['label'], cred['password'])
                    stored_count += 1
            except Exception as e:
                logger.error(f"Error storing quick credential: {e}")
                continue
        
        if stored_count > 0:
            return f"✅ Successfully stored {stored_count} credential(s)!"
        else:
            return "❌ Failed to store credentials. Please check the format and try again."
    
    async def _handle_add(self, user_id: str, command: str) -> str:
        """Handle !add command for flexible data addition."""
        content = command[4:].strip()  # Remove "!add"
        
        if not content:
            return """**Add Command Usage:**
`!add <anything>` - Automatically categorize and store
• Passwords, credentials, emails, links, and notes
• Uses smart detection to categorize your data
• Same as just sending the message without !add

**Examples:**
• `!add Gmail john@email.com mypass123`
• `!add My important note about something`
• `!add https://github.com/myrepo`
• `!add user: john password: abc123 for Netflix`"""
        
        # Process the content using auto-categorization
        await self._auto_categorize_and_store(user_id, content)
        return "✅ Data processed and stored!"
    
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
        
        # Enhanced convenient detection patterns (only if no credentials were found above)
        if not potential_credentials:
            convenient_credentials = self._detect_convenient_formats(content)
            for cred in convenient_credentials:
                try:
                    if cred['type'] == 'credential':
                        await self.storage.store_credential(user_id, cred['label'], cred['username'], cred['password'])
                        logger.info(f"Stored convenient format credentials for user {user_id}: {cred['label']}")
                    elif cred['type'] == 'password':
                        await self.storage.store_password(user_id, cred['label'], cred['password'])
                        logger.info(f"Stored convenient format password for user {user_id}: {cred['label']}")
                except Exception as e:
                    logger.error(f"Error storing convenient format credential: {e}")
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
            content_has_structured_data = bool(emails_found or urls_found or potential_credentials)
            
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
                    # Skip if the next word is just another indicator
                    if next_word.lower() in password_indicators + username_indicators:
                        continue
                    # Explicit check to never store common keywords as passwords
                    if next_word.lower() in ['user', 'username', 'password', 'pass', 'pwd', 'email', 'login', 'id', 'account']:
                        continue
                    if self._looks_like_password(next_word) and len(next_word) >= 8:
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
                    candidate = words[j]
                    # Skip common keywords
                    if candidate.lower() in password_indicators + username_indicators:
                        continue
                    # Never process 'user' as username or password
                    if candidate.lower() in ['user', 'username', 'password', 'pass', 'pwd', 'email', 'login', 'id', 'account']:
                        continue
                    if not username and self._looks_like_username(candidate):
                        username = candidate
                    elif username and self._looks_like_password(candidate):
                        password = candidate
                        break
                
                if username and password and username != password:
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
                    if any(indicator in key for indicator in password_indicators) and value and value.lower() not in ['user', 'username', 'password', 'pass', 'pwd']:
                        label = key.replace('password', '').replace('pass', '').replace('pwd', '').strip()
                        if not label:
                            label = 'Detected'
                        # Never store blacklisted words
                        if value.lower() in ['user', 'username', 'password', 'pass', 'pwd', 'email', 'login', 'id', 'account']:
                            continue
                        # Only store if the value looks like an actual password
                        if self._looks_like_password(value) and len(value) >= 8:
                            credentials.append({
                                'type': 'password',
                                'label': label.title(),
                                'password': value
                            })
        
        # Heuristic 4: Pattern-free detection - just look for password-like strings with context
        for i, word in enumerate(words):
            if self._looks_like_password(word) and len(word) >= 8:
                # Check if there's context around it
                context_words = []
                for j in range(max(0, i-3), min(len(words), i+4)):
                    if j != i:
                        context_words.append(words[j].lower())
                
                # If there's password-related context, store it
                if any(indicator in ' '.join(context_words) for indicator in password_indicators + username_indicators):
                    label = self._find_label_before(words, i) or 'Detected'
                    # Don't store if it's just the word "user" or similar
                    if word.lower() not in ['user', 'username', 'password', 'pass', 'pwd', 'email', 'login']:
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
        if len(word) < 8:  # Increase minimum length
            return False
        
        # Skip common false positives - be very aggressive here
        false_positives = ['user', 'username', 'password', 'pass', 'pwd', 'gmail', 'email', 'login', 'account', 'id', 'name', 'label']
        if word.lower() in false_positives:
            return False
        
        # Don't consider anything that starts with common prefixes
        false_prefixes = ['user', 'email', 'login', 'account']
        if any(word.lower().startswith(prefix) for prefix in false_prefixes):
            return False
        
        # Basic password characteristics
        has_upper = any(c.isupper() for c in word)
        has_lower = any(c.islower() for c in word)
        has_digit = any(c.isdigit() for c in word)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in word)
        
        # Require at least 3 character types for passwords
        char_types = sum([has_upper, has_lower, has_digit, has_special])
        if char_types < 2:
            return False
        
        # Strong password indicators
        if len(word) >= 8 and char_types >= 3:
            return True
        
        # Medium password indicators
        if len(word) >= 12 and char_types >= 2:
            return True
        
        return False
    
    def _looks_like_username(self, word: str) -> bool:
        """Check if a word looks like a username."""
        if len(word) < 3 or len(word) > 50:
            return False
        
        # Never consider these as usernames
        blacklist = {'user', 'username', 'password', 'pass', 'pwd', 'email', 'login', 'account', 'id', 'name'}
        if word.lower() in blacklist:
            return False
        
        # Email-like usernames
        if '@' in word:
            return True
        
        # Alphanumeric with some special chars
        if re.match(r'^[a-zA-Z0-9._-]+$', word):
            return True
        
        return False
    
    def _find_label_before(self, words: list, index: int) -> Optional[str]:
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

    def _detect_convenient_formats(self, content: str) -> list:
        """
        Detect convenient input formats for ID/password combinations.
        Supports various natural input styles.
        """
        credentials = []
        lines = content.split('\n')
        content_lower = content.lower()
        
        # Pattern 1: Simple "service user pass" format
        # Examples: "gmail john@email.com mypassword123", "netflix user123 pass456"
        simple_pattern = re.compile(r'(\w+)\s+([^\s]+)\s+([^\s]+)', re.IGNORECASE)
        for match in simple_pattern.finditer(content):
            service, user, password = match.groups()
            # Better validation to avoid false positives
            if (len(password) >= 6 and len(user) >= 3 and 
                service.lower() not in ['user', 'username', 'password', 'pass', 'pwd'] and
                user.lower() not in ['user', 'username', 'password', 'pass', 'pwd'] and
                password.lower() not in ['user', 'username', 'password', 'pass', 'pwd']):
                credentials.append({
                    'type': 'credential',
                    'label': service.title(),
                    'username': user,
                    'password': password
                })
        
        # Pattern 2: "service: user/pass" format
        # Examples: "Netflix: user123/pass456", "Gmail: john@email.com/mypass"
        colon_slash_pattern = re.compile(r'([^:\n]+):\s*([^/\s]+)/([^\s\n]+)', re.IGNORECASE)
        for match in colon_slash_pattern.finditer(content):
            service, user, password = match.groups()
            credentials.append({
                'type': 'credential',
                'label': service.strip().title(),
                'username': user.strip(),
                'password': password.strip()
            })
        
        # Pattern 3: Line-by-line format
        # Examples: "Gmail\nuser: john@email.com\npass: mypass123"
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(lines) <= i + 2:
                continue
                
            # Check if this might be a service name
            if len(line.split()) <= 2 and len(line) < 50:
                next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                third_line = lines[i + 2].strip() if i + 2 < len(lines) else ""
                
                user_match = re.match(r'(?:user|username|id|email):\s*(.+)', next_line, re.IGNORECASE)
                pass_match = re.match(r'(?:pass|password|pwd):\s*(.+)', third_line, re.IGNORECASE)
                
                if user_match and pass_match:
                    credentials.append({
                        'type': 'credential',
                        'label': line.title(),
                        'username': user_match.group(1).strip(),
                        'password': pass_match.group(1).strip()
                    })
        
        # Pattern 4: Space-separated with keywords
        # Examples: "user john password mypass123 for Gmail"
        keyword_pattern = re.compile(r'(?:user|username|id)\s+([^\s]+)\s+(?:pass|password|pwd)\s+([^\s]+)(?:\s+for\s+([^\n]+))?', re.IGNORECASE)
        for match in keyword_pattern.finditer(content):
            user, password, service = match.groups()
            label = service.strip().title() if service else 'Account'
            credentials.append({
                'type': 'credential',
                'label': label,
                'username': user,
                'password': password
            })
        
        # Pattern 5: Quick password format
        # Examples: "pass for gmail: mypassword123", "password netflix: abc123"
        quick_pass_pattern = re.compile(r'(?:pass|password|pwd)\s+(?:for\s+)?([^:\n]+):\s*([^\s\n]+)', re.IGNORECASE)
        for match in quick_pass_pattern.finditer(content):
            service, password = match.groups()
            credentials.append({
                'type': 'password',
                'label': service.strip().title(),
                'password': password.strip()
            })
        
        # Pattern 6: Just service and password
        # Examples: "gmail mypassword123", "netflix abc123def" 
        if len(content.split()) == 2:
            parts = content.split()
            if len(parts[1]) >= 6 and not parts[0].lower() in ['user', 'username', 'password', 'pass', 'pwd', 'email']:  # Reasonable password length and not a keyword
                credentials.append({
                    'type': 'password',
                    'label': parts[0].title(),
                    'password': parts[1]
                })
        
        # Remove duplicates
        seen = set()
        unique_creds = []
        for cred in credentials:
            key = (cred['type'], cred['label'], cred.get('username', ''), cred['password'])
            if key not in seen:
                seen.add(key)
                unique_creds.append(cred)
        
        return unique_creds

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

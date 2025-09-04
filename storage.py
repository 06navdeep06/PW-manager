"""
User Data Storage Module
Handles persistent storage of user data using SQLite database.
"""

import logging
import re
from typing import List, Dict, Optional, Any
import aiosqlite

logger = logging.getLogger(__name__)

class UserStorage:
    """Handles storage and retrieval of user data."""
    
    def __init__(self, db_path: str = "user_data.db"):
        self.db_path = db_path
        # Maximum lengths for validation
        self.MAX_CONTENT_LENGTH = 10000
        self.MAX_LABEL_LENGTH = 200
        self.MAX_USERNAME_LENGTH = 200
        self.MAX_PASSWORD_LENGTH = 500
        self.MAX_EMAIL_LENGTH = 320
        self.MAX_URL_LENGTH = 2000
    
    def _validate_user_id(self, user_id: str) -> str:
        """Validate and sanitize user ID."""
        if not user_id or not isinstance(user_id, (str, int)):
            raise ValueError("Invalid user ID")
        return str(user_id).strip()
    
    def _validate_content(self, content: str, max_length: Optional[int] = None) -> str:
        """Validate and sanitize content."""
        if not content or not isinstance(content, str):
            raise ValueError("Invalid content")
        
        content = content.strip()
        max_len = max_length if max_length is not None else self.MAX_CONTENT_LENGTH
        
        if len(content) > max_len:
            raise ValueError(f"Content too long (max {max_len} characters)")
        
        # Remove potential SQL injection patterns
        content = re.sub(r'[;\'"\\]', '', content)
        return content
    
    def _validate_label(self, label: str) -> str:
        """Validate and sanitize label."""
        return self._validate_content(label, self.MAX_LABEL_LENGTH)
    
    def _validate_username(self, username: str) -> str:
        """Validate and sanitize username."""
        return self._validate_content(username, self.MAX_USERNAME_LENGTH)
    
    def _validate_password(self, password: str) -> str:
        """Validate and sanitize password."""
        return self._validate_content(password, self.MAX_PASSWORD_LENGTH)
    
    def _validate_email(self, email: str) -> str:
        """Validate and sanitize email."""
        email = self._validate_content(email, self.MAX_EMAIL_LENGTH)
        # Basic email validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError("Invalid email format")
        return email
    
    def _validate_url(self, url: str) -> str:
        """Validate and sanitize URL."""
        url = self._validate_content(url, self.MAX_URL_LENGTH)
        # Basic URL validation
        if not re.match(r'^https?://[^\s/$.?#].[^\s]*$', url):
            raise ValueError("Invalid URL format")
        return url
        
    async def initialize(self):
        """Initialize the database and create tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_passwords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    label TEXT NOT NULL,
                    password TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, label)
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    label TEXT NOT NULL,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, label)
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    note TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    label TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    link_type TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.commit()
            logger.info("Database initialized successfully")
    
    async def store_message(self, user_id: str, content: str, message_type: str = "text"):
        """Store a message from a user."""
        try:
            user_id = self._validate_user_id(user_id)
            content = self._validate_content(content)
            message_type = self._validate_content(message_type, 50)
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT INTO user_messages (user_id, content, message_type) VALUES (?, ?, ?)",
                    (user_id, content, message_type)
                )
                await db.commit()
        except ValueError as e:
            logger.warning(f"Validation error storing message for user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error storing message for user {user_id}: {e}")
    
    async def store_password(self, user_id: str, label: str, password: str):
        """Store a password for a user with a specific label."""
        try:
            user_id = self._validate_user_id(user_id)
            label = self._validate_label(label)
            password = self._validate_password(password)
            
            # Check if exact same password already exists
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT id FROM user_passwords WHERE user_id = ? AND label = ? AND password = ?",
                    (user_id, label, password)
                )
                existing = await cursor.fetchone()
                
                if not existing:
                    await db.execute(
                        """INSERT OR REPLACE INTO user_passwords (user_id, label, password) 
                           VALUES (?, ?, ?)""",
                        (user_id, label, password)
                    )
                    await db.commit()
        except ValueError as e:
            logger.warning(f"Validation error storing password for user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error storing password for user {user_id}: {e}")
    
    async def store_credential(self, user_id: str, label: str, username: str, password: str):
        """Store username and password credentials for a user."""
        try:
            user_id = self._validate_user_id(user_id)
            label = self._validate_label(label)
            username = self._validate_username(username)
            password = self._validate_password(password)
            
            # Check if exact same credential already exists
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT id FROM user_credentials WHERE user_id = ? AND label = ? AND username = ? AND password = ?",
                    (user_id, label, username, password)
                )
                existing = await cursor.fetchone()
                
                if not existing:
                    await db.execute(
                        """INSERT OR REPLACE INTO user_credentials (user_id, label, username, password) 
                           VALUES (?, ?, ?, ?)""",
                        (user_id, label, username, password)
                    )
                    await db.commit()
        except ValueError as e:
            logger.warning(f"Validation error storing credentials for user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error storing credentials for user {user_id}: {e}")
    
    async def get_credential(self, user_id: str, label: str) -> Optional[Dict[str, str]]:
        """Retrieve username and password credentials for a user by label."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT username, password FROM user_credentials WHERE user_id = ? AND label = ?",
                    (str(user_id), label)
                )
                result = await cursor.fetchone()
                if result:
                    return {"username": result[0], "password": result[1]}
                return None
        except Exception as e:
            logger.error(f"Error retrieving credentials for user {user_id}: {e}")
            return None
    
    async def get_all_credentials(self, user_id: str) -> List[Dict[str, str]]:
        """Retrieve all credentials for a user."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT label, username, password FROM user_credentials WHERE user_id = ? ORDER BY timestamp DESC",
                    (str(user_id),)
                )
                results = await cursor.fetchall()
                return [
                    {"label": row[0], "username": row[1], "password": row[2]}
                    for row in results
                ]
        except Exception as e:
            logger.error(f"Error retrieving all credentials for user {user_id}: {e}")
            return []
    
    async def get_password(self, user_id: str, label: str) -> Optional[str]:
        """Retrieve a password for a user by label."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT password FROM user_passwords WHERE user_id = ? AND label = ?",
                    (str(user_id), label)
                )
                result = await cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error retrieving password for user {user_id}: {e}")
            return None
    
    async def store_note(self, user_id: str, note: str):
        """Store a note for a user."""
        try:
            user_id = self._validate_user_id(user_id)
            note = self._validate_content(note)
            
            # Check for duplicates first (only for exact same notes)
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT id FROM user_notes WHERE user_id = ? AND note = ? AND timestamp > datetime('now', '-1 hour')",
                    (user_id, note)
                )
                existing = await cursor.fetchone()
                
                if not existing:
                    await db.execute(
                        "INSERT INTO user_notes (user_id, note) VALUES (?, ?)",
                        (user_id, note)
                    )
                    await db.commit()
        except ValueError as e:
            logger.warning(f"Validation error storing note for user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error storing note for user {user_id}: {e}")
    
    async def get_notes(self, user_id: str) -> List[str]:
        """Retrieve all notes for a user."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT note FROM user_notes WHERE user_id = ? ORDER BY timestamp DESC",
                    (str(user_id),)
                )
                results = await cursor.fetchall()
                return [row[0] for row in results]
        except Exception as e:
            logger.error(f"Error retrieving notes for user {user_id}: {e}")
            return []
    
    async def store_email(self, user_id: str, email: str, label: Optional[str] = None):
        """Store an email address for a user."""
        try:
            user_id = self._validate_user_id(user_id)
            email = self._validate_email(email)
            label = self._validate_label(label) if label is not None else None
            
            # Check for duplicates first
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT id FROM user_emails WHERE user_id = ? AND email = ?",
                    (user_id, email)
                )
                existing = await cursor.fetchone()
                
                if not existing:
                    await db.execute(
                        "INSERT INTO user_emails (user_id, email, label) VALUES (?, ?, ?)",
                        (user_id, email, label)
                    )
                    await db.commit()
        except ValueError as e:
            logger.warning(f"Validation error storing email for user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error storing email for user {user_id}: {e}")
    
    async def get_emails(self, user_id: str) -> List[Dict[str, str]]:
        """Retrieve all email addresses for a user."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT email, label FROM user_emails WHERE user_id = ? ORDER BY timestamp DESC",
                    (str(user_id),)
                )
                results = await cursor.fetchall()
                return [{"email": row[0], "label": row[1]} for row in results]
        except Exception as e:
            logger.error(f"Error retrieving emails for user {user_id}: {e}")
            return []
    
    async def store_link(self, user_id: str, url: str, link_type: Optional[str] = None):
        """Store a link for a user."""
        try:
            user_id = self._validate_user_id(user_id)
            url = self._validate_url(url)
            link_type = self._validate_content(link_type, 50) if link_type is not None else None
            
            # Check for duplicates first
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT id FROM user_links WHERE user_id = ? AND url = ?",
                    (user_id, url)
                )
                existing = await cursor.fetchone()
                
                if not existing:
                    await db.execute(
                        "INSERT INTO user_links (user_id, url, link_type) VALUES (?, ?, ?)",
                        (user_id, url, link_type)
                    )
                    await db.commit()
        except ValueError as e:
            logger.warning(f"Validation error storing link for user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error storing link for user {user_id}: {e}")
    
    async def get_links(self, user_id: str) -> List[Dict[str, str]]:
        """Retrieve all links for a user."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT url, link_type FROM user_links WHERE user_id = ? ORDER BY timestamp DESC",
                    (str(user_id),)
                )
                results = await cursor.fetchall()
                return [{"url": row[0], "type": row[1]} for row in results]
        except Exception as e:
            logger.error(f"Error retrieving links for user {user_id}: {e}")
            return []
    
    async def get_all_categories(self, user_id: str) -> Dict[str, int]:
        """Get counts of all data categories for a user."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                categories = {}
                
                # Count passwords
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM user_passwords WHERE user_id = ?",
                    (str(user_id),)
                )
                categories["passwords"] = (await cursor.fetchone())[0]
                
                # Count credentials
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM user_credentials WHERE user_id = ?",
                    (str(user_id),)
                )
                categories["credentials"] = (await cursor.fetchone())[0]
                
                # Count notes
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM user_notes WHERE user_id = ?",
                    (str(user_id),)
                )
                categories["notes"] = (await cursor.fetchone())[0]
                
                # Count emails
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM user_emails WHERE user_id = ?",
                    (str(user_id),)
                )
                categories["emails"] = (await cursor.fetchone())[0]
                
                # Count links
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM user_links WHERE user_id = ?",
                    (str(user_id),)
                )
                categories["links"] = (await cursor.fetchone())[0]
                
                # Count total messages
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM user_messages WHERE user_id = ?",
                    (str(user_id),)
                )
                categories["total_messages"] = (await cursor.fetchone())[0]
                
                return categories
        except Exception as e:
            logger.error(f"Error getting categories for user {user_id}: {e}")
            return {"passwords": 0, "credentials": 0, "notes": 0, "emails": 0, "links": 0, "total_messages": 0}
    
    async def clear_user_data(self, user_id: str):
        """Clear all data for a specific user."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                tables = ["user_messages", "user_passwords", "user_credentials", "user_notes", "user_emails", "user_links"]
                for table in tables:
                    await db.execute(f"DELETE FROM {table} WHERE user_id = ?", (str(user_id),))
                await db.commit()
                logger.info(f"Cleared all data for user {user_id}")
        except Exception as e:
            logger.error(f"Error clearing data for user {user_id}: {e}")
    
    async def get_recent_messages(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages for a user."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """SELECT content, message_type, timestamp 
                       FROM user_messages 
                       WHERE user_id = ? 
                       ORDER BY timestamp DESC 
                       LIMIT ?""",
                    (str(user_id), limit)
                )
                results = await cursor.fetchall()
                return [
                    {
                        "content": row[0],
                        "type": row[1],
                        "timestamp": row[2]
                    }
                    for row in results
                ]
        except Exception as e:
            logger.error(f"Error getting recent messages for user {user_id}: {e}")
            return []
    
    async def clear_duplicates(self, user_id: str):
        """Remove duplicate entries for a user."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Remove duplicate credentials (keep latest)
                await db.execute("""
                    DELETE FROM user_credentials 
                    WHERE user_id = ? AND id NOT IN (
                        SELECT MAX(id) FROM user_credentials 
                        WHERE user_id = ? 
                        GROUP BY label, username, password
                    )
                """, (str(user_id), str(user_id)))
                
                # Remove duplicate passwords (keep latest)
                await db.execute("""
                    DELETE FROM user_passwords 
                    WHERE user_id = ? AND id NOT IN (
                        SELECT MAX(id) FROM user_passwords 
                        WHERE user_id = ? 
                        GROUP BY label, password
                    )
                """, (str(user_id), str(user_id)))
                
                # Remove duplicate emails (keep latest)
                await db.execute("""
                    DELETE FROM user_emails 
                    WHERE user_id = ? AND id NOT IN (
                        SELECT MAX(id) FROM user_emails 
                        WHERE user_id = ? 
                        GROUP BY email
                    )
                """, (str(user_id), str(user_id)))
                
                # Remove duplicate links (keep latest)
                await db.execute("""
                    DELETE FROM user_links 
                    WHERE user_id = ? AND id NOT IN (
                        SELECT MAX(id) FROM user_links 
                        WHERE user_id = ? 
                        GROUP BY url
                    )
                """, (str(user_id), str(user_id)))
                
                await db.commit()
                logger.info(f"Cleared duplicates for user {user_id}")
        except Exception as e:
            logger.error(f"Error clearing duplicates for user {user_id}: {e}")

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class MessageStorage:
    def __init__(self, db_path: str = "bot_data.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        
    async def initialize(self):
        """Initialize the database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pending_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    message_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER PRIMARY KEY,
                    enabled BOOLEAN DEFAULT TRUE,
                    toxicity_threshold REAL DEFAULT 0.7,
                    locale TEXT DEFAULT 'en',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id INTEGER PRIMARY KEY,
                    total_prompts INTEGER DEFAULT 0,
                    continued_sending INTEGER DEFAULT 0,
                    edited_messages INTEGER DEFAULT 0,
                    cancelled_messages INTEGER DEFAULT 0,
                    last_prompt_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Clean up expired messages
            conn.execute("""
                DELETE FROM pending_messages 
                WHERE expires_at < CURRENT_TIMESTAMP
            """)
            
            conn.commit()
            logger.info("Database initialized successfully")
            
    async def store_pending_message(self, user_id: int, message_data: Dict[str, Any]) -> int:
        """Store a pending message and return its ID"""
        expires_at = datetime.utcnow().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO pending_messages (user_id, message_data, expires_at)
                VALUES (?, ?, datetime('now', '+1 hour'))
            """, (user_id, json.dumps(message_data)))
            
            conn.commit()
            return cursor.lastrowid
            
    async def get_pending_message(self, message_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a pending message by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT message_data FROM pending_messages 
                WHERE id = ? AND expires_at > CURRENT_TIMESTAMP
            """, (message_id,))
            
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None
            
    async def remove_pending_message(self, message_id: int):
        """Remove a pending message"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                DELETE FROM pending_messages WHERE id = ?
            """, (message_id,))
            conn.commit()
            
    async def cleanup_expired_messages(self):
        """Clean up expired pending messages"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM pending_messages 
                WHERE expires_at < CURRENT_TIMESTAMP
            """)
            conn.commit()
            return cursor.rowcount
            
    async def is_enabled(self, guild_id: int) -> bool:
        """Check if the bot is enabled for a guild"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT enabled FROM guild_settings WHERE guild_id = ?
            """, (guild_id,))
            
            row = cursor.fetchone()
            return row[0] if row else True  # Default to enabled
            
    async def set_enabled(self, guild_id: int, enabled: bool):
        """Enable or disable the bot for a guild"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO guild_settings (guild_id, enabled, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (guild_id, enabled))
            conn.commit()
            
    async def get_guild_settings(self, guild_id: int) -> Dict[str, Any]:
        """Get all settings for a guild"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM guild_settings WHERE guild_id = ?
            """, (guild_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            else:
                # Return defaults
                return {
                    'guild_id': guild_id,
                    'enabled': True,
                    'toxicity_threshold': 0.7,
                    'locale': 'en'
                }
                
    async def update_guild_settings(self, guild_id: int, **kwargs):
        """Update guild settings"""
        valid_fields = ['enabled', 'toxicity_threshold', 'locale']
        updates = {k: v for k, v in kwargs.items() if k in valid_fields}
        
        if not updates:
            return
            
        set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [guild_id]
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"""
                INSERT OR REPLACE INTO guild_settings 
                (guild_id, {', '.join(updates.keys())}, updated_at)
                VALUES (?, {', '.join('?' * len(updates))}, CURRENT_TIMESTAMP)
            """, values)
            conn.commit()
            
    async def record_user_action(self, user_id: int, action: str):
        """Record a user's decision for analytics"""
        action_columns = {
            'continued_sending': 'continued_sending',
            'edited_message': 'edited_messages', 
            'cancelled': 'cancelled_messages'
        }
        
        column = action_columns.get(action)
        if not column:
            return
            
        with sqlite3.connect(self.db_path) as conn:
            # Insert or update user stats
            conn.execute(f"""
                INSERT INTO user_stats (user_id, total_prompts, {column}, last_prompt_at)
                VALUES (?, 1, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    total_prompts = total_prompts + 1,
                    {column} = {column} + 1,
                    last_prompt_at = CURRENT_TIMESTAMP
            """, (user_id,))
            conn.commit()
            
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user statistics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM user_stats WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            else:
                return {
                    'user_id': user_id,
                    'total_prompts': 0,
                    'continued_sending': 0,
                    'edited_messages': 0,
                    'cancelled_messages': 0,
                    'last_prompt_at': None
                }
                
    async def get_guild_stats(self, guild_id: int) -> Dict[str, Any]:
        """Get aggregated statistics for a guild"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_users,
                    SUM(total_prompts) as total_prompts,
                    SUM(continued_sending) as total_continued,
                    SUM(edited_messages) as total_edited,
                    SUM(cancelled_messages) as total_cancelled
                FROM user_stats
                WHERE user_id IN (
                    SELECT DISTINCT user_id FROM pending_messages
                    UNION
                    SELECT DISTINCT user_id FROM user_stats
                )
            """)
            
            row = cursor.fetchone()
            if row:
                return {
                    'total_users': row[0] or 0,
                    'total_prompts': row[1] or 0,
                    'total_continued': row[2] or 0,
                    'total_edited': row[3] or 0,
                    'total_cancelled': row[4] or 0
                }
            else:
                return {
                    'total_users': 0,
                    'total_prompts': 0,
                    'total_continued': 0,
                    'total_edited': 0,
                    'total_cancelled': 0
                }
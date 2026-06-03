import sqlite3
import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Union, Any, List, Tuple

DB_PATH = Path("wwaijd.db")

def init_db():
    """
    Initialize the SQLite database with the shared_conversations and stats tables.

    Creates the tables if they do not already exist.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS shared_conversations (
            id TEXT PRIMARY KEY,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            passages TEXT,
            mode TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create stats table for general tracking
    c.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            value INTEGER DEFAULT 0
        )
    ''')

    # Create topic_overviews table for caching LLM topic summaries
    c.execute('''
        CREATE TABLE IF NOT EXISTS topic_overviews (
            topic TEXT PRIMARY KEY,
            summary TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create public_prayers table for the community prayer wall
    c.execute('''
        CREATE TABLE IF NOT EXISTS public_prayers (
            id TEXT PRIMARY KEY,
            title TEXT,
            request TEXT NOT NULL,
            pray_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create daily_devotionals table to cache LLM generated reflections daily
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_devotionals (
            date_str TEXT PRIMARY KEY,
            verse_ref TEXT NOT NULL,
            verse_text TEXT NOT NULL,
            reflection TEXT NOT NULL,
            prayer TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def get_topic_overview(topic: str) -> Optional[str]:
    """Retrieve cached topic summary."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT summary FROM topic_overviews WHERE topic = ?', (topic.lower(),))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def save_topic_overview(topic: str, summary: str):
    """Cache topic summary."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO topic_overviews (topic, summary)
        VALUES (?, ?)
    ''', (topic.lower(), summary))
    conn.commit()
    conn.close()

def save_conversation(
    question: str,
    answer: str,
    passages: Union[List[Dict[str, Any]], str],
    mode: str = 'balanced'
) -> str:
    """
    Save a conversation to the database and return its unique ID.

    Args:
        question: The user's question.
        answer: The AI generated answer.
        passages: The list of Bible passages used, or a JSON string of them.
        mode: The tone/mode used for the answer. Defaults to 'balanced'.

    Returns:
        str: The unique 8-character ID for the saved conversation.
    """
    share_id = str(uuid.uuid4())[:8]  # Use first 8 chars for shorter URLs
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Ensure passages is a JSON string
    passages_json = json.dumps(passages) if isinstance(passages, (list, dict)) else passages
    
    c.execute('''
        INSERT INTO shared_conversations (id, question, answer, passages, mode)
        VALUES (?, ?, ?, ?, ?)
    ''', (share_id, question, answer, passages_json, mode))
    
    conn.commit()
    conn.close()
    
    return share_id

def get_conversation(share_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a saved conversation by its ID.

    Args:
        share_id: The unique ID of the conversation to retrieve.

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing the conversation data
        (id, question, answer, passages, mode, created_at) if found,
        otherwise None.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT * FROM shared_conversations WHERE id = ?', (share_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_recent_shared_conversations(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve the most recently saved conversations.

    Args:
        limit: Maximum number of conversations to return.

    Returns:
        List[Dict[str, Any]]: List of conversation dictionaries.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('''
        SELECT id, question, mode, created_at
        FROM shared_conversations
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))

    rows = c.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def get_shared_conversations_paginated(page: int = 1, limit: int = 20) -> Tuple[List[Dict[str, Any]], int]:
    """
    Retrieve shared conversations with pagination, along with total count.

    Args:
        page: Page number (1-indexed).
        limit: Max items per page.

    Returns:
        Tuple[List[Dict[str, Any]], int]: List of conversations and total count.
    """
    offset = (page - 1) * limit
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get total count
    c.execute('SELECT COUNT(*) FROM shared_conversations')
    total_count = c.fetchone()[0]
    
    # Get page rows
    c.execute('''
        SELECT id, question, mode, created_at
        FROM shared_conversations
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    
    rows = c.fetchall()
    conn.close()
    
    return [dict(row) for row in rows], total_count

def save_public_prayer(title: str, request: str) -> str:
    """Save a prayer request to the public wall."""
    prayer_id = str(uuid.uuid4())[:8]
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO public_prayers (id, title, request)
        VALUES (?, ?, ?)
    ''', (prayer_id, title, request))
    conn.commit()
    conn.close()
    return prayer_id

def increment_prayer_count(prayer_id: str) -> int:
    """Increment pray_count for a public prayer."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE public_prayers SET pray_count = pray_count + 1 WHERE id = ?', (prayer_id,))
    c.execute('SELECT pray_count FROM public_prayers WHERE id = ?', (prayer_id,))
    row = c.fetchone()
    conn.commit()
    conn.close()
    return row[0] if row else 0

def get_public_prayers(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """Retrieve public prayers."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        SELECT id, title, request, pray_count, created_at
        FROM public_prayers
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_daily_devotional(date_str: str) -> Optional[Dict[str, Any]]:
    """Retrieve cached daily devotional for a specific date (YYYY-MM-DD)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM daily_devotionals WHERE date_str = ?', (date_str,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def save_daily_devotional(date_str: str, verse_ref: str, verse_text: str, reflection: str, prayer: str):
    """Cache the daily devotional."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO daily_devotionals (date_str, verse_ref, verse_text, reflection, prayer)
        VALUES (?, ?, ?, ?, ?)
    ''', (date_str, verse_ref, verse_text, reflection, prayer))
    conn.commit()
    conn.close()

def increment_visit_count():
    """
    Increment the global visit counter.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO stats (key, value) VALUES (?, ?)', ('visits', 0))
    c.execute('UPDATE stats SET value = value + 1 WHERE key = ?', ('visits',))
    conn.commit()
    conn.close()

def get_visit_count() -> int:
    """
    Get the current global visit count.

    Returns:
        int: The number of visits.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT value FROM stats WHERE key = ?', ('visits',))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

# Initialize DB on module load
init_db()

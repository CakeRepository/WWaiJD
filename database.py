import sqlite3
import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Union, Any, List

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

import sqlite3
import uuid
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path("wwaijd.db")

def init_db():
    """Initialize the database with the shared_conversations table."""
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
    conn.commit()
    conn.close()

def save_conversation(question, answer, passages, mode='balanced'):
    """Save a conversation and return its ID."""
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

def get_conversation(share_id):
    """Retrieve a conversation by ID."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT * FROM shared_conversations WHERE id = ?', (share_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

# Initialize DB on module load
init_db()

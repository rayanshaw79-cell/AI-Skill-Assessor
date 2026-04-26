import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'sessions.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            data TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_session(session_id: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT data FROM sessions WHERE session_id = ?', (session_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None

def save_session(session_id: str, data: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sessions (session_id, data) 
        VALUES (?, ?) 
        ON CONFLICT(session_id) DO UPDATE SET data=excluded.data
    ''', (session_id, json.dumps(data)))
    conn.commit()
    conn.close()

# Initialize DB on import
init_db()

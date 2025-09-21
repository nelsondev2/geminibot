import sqlite3
import json

def init_db():
    conn = sqlite3.connect("chat_history.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            chat_id TEXT PRIMARY KEY,
            title TEXT,
            prompt TEXT DEFAULT 'Eres un asistente útil que responde de manera clara y concisa.',
            audio_mode BOOLEAN DEFAULT 0,
            textfile_mode BOOLEAN DEFAULT 0,
            lang_code TEXT DEFAULT 'es',
            slow_audio BOOLEAN DEFAULT 0,
            memory_limit INTEGER DEFAULT 20,
            voice_name TEXT DEFAULT 'Kore',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            content TEXT,
            role TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats(chat_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending_retries (
            chat_id TEXT PRIMARY KEY,
            messages_json TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def get_chat_config(chat_id):
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT prompt, audio_mode, textfile_mode, voice_name FROM chats WHERE chat_id = ?",
            (str(chat_id),)
        )
        return cursor.fetchone()

def save_chat_config(chat_id, title, prompt, audio_mode, textfile_mode, voice_name):
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO chats 
            (chat_id, title, prompt, audio_mode, textfile_mode, voice_name) 
            VALUES (?, ?, ?, ?, ?, ?)""",
            (str(chat_id), title, prompt, audio_mode, textfile_mode, voice_name)
        )
        conn.commit()

def save_message(chat_id, content, role):
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (chat_id, content, role) VALUES (?, ?, ?)",
            (str(chat_id), content, role)
        )
        conn.commit()

def get_chat_history(chat_id, limit=20):
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT content, role FROM messages WHERE chat_id = ? ORDER BY timestamp DESC LIMIT ?",
            (str(chat_id), limit)
        )
        return cursor.fetchall()

def clear_chat_history(chat_id):
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE chat_id = ?", (str(chat_id),))
        cursor.execute("DELETE FROM pending_retries WHERE chat_id = ?", (str(chat_id),))
        conn.commit()

def save_pending_message(chat_id, messages):
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO pending_retries (chat_id, messages_json) VALUES (?, ?)",
            (str(chat_id), json.dumps(messages))
        )
        conn.commit()

def get_pending_message(chat_id):
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT messages_json FROM pending_retries WHERE chat_id = ?",
            (str(chat_id),))
        result = cursor.fetchone()
        return json.loads(result[0]) if result else None

def clear_pending_message(chat_id):
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM pending_retries WHERE chat_id = ?",
            (str(chat_id),))
        conn.commit()

# Inicializar la base de datos al importar
init_db()

# database.py
import sqlite3

class ChatDatabase:
    def __init__(self, db_path="chat_memory.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                sender TEXT,
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        ''')
        self.conn.commit()

    def get_or_create_conversation(self, session_id):
        self.cursor.execute("SELECT id FROM conversations WHERE session_id = ?", (session_id,))
        row = self.cursor.fetchone()
        if row:
            return row[0]
        self.cursor.execute("INSERT INTO conversations (session_id) VALUES (?)", (session_id,))
        self.conn.commit()
        return self.cursor.lastrowid

    def save_message(self, conversation_id, sender, message):
        self.cursor.execute(
            "INSERT INTO messages (conversation_id, sender, message) VALUES (?, ?, ?)",
            (conversation_id, sender, message)
        )
        self.conn.commit()

    def get_conversation_history(self, conversation_id):
        self.cursor.execute(
            "SELECT sender, message FROM messages WHERE conversation_id = ? ORDER BY timestamp",
            (conversation_id,)
        )
        return self.cursor.fetchall()


    def close(self):
        self.conn.close()

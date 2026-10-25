import sqlite3
from pathlib import Path
from backend.config import settings

def connect():
    path = Path(settings.database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
            role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        db.execute("""CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, chunk TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

def add_message(session_id, role, content):
    with connect() as db:
        db.execute("INSERT INTO messages(session_id,role,content) VALUES (?,?,?)",(session_id,role,content))

def get_history(session_id, limit=50):
    with connect() as db:
        rows = db.execute("SELECT role,content,created_at FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?",
                          (session_id, min(max(int(limit),1),100))).fetchall()
    return [dict(x) for x in reversed(rows)]

def delete_session(session_id):
    with connect() as db: db.execute("DELETE FROM messages WHERE session_id=?",(session_id,))

def add_document(name, chunk):
    with connect() as db:
        db.execute(
            "INSERT INTO documents(name,chunk) VALUES (?,?)",
            (name, chunk),
        )


def replace_document(name, chunks):
    with connect() as db:
        db.execute("DELETE FROM documents WHERE name = ?", (name,))
        db.executemany(
            "INSERT INTO documents(name,chunk) VALUES (?,?)",
            [(name, chunk) for chunk in chunks],
        )

def search_documents(query, limit=4):
    terms = [x for x in query.split() if len(x)>2][:8]
    if not terms: return []
    where = " OR ".join("chunk LIKE ?" for _ in terms)
    with connect() as db:
        rows = db.execute(f"SELECT id,name,chunk FROM documents WHERE {where} LIMIT ?",
                          [*(f"%{x}%" for x in terms),limit]).fetchall()
    return [dict(x) for x in rows]

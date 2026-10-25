import json
from contextlib import contextmanager
import math
import sqlite3
from pathlib import Path

from backend.config import settings


@contextmanager
def connect():
    path = Path(settings.database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    try:
        with db:
            yield db
    finally:
        db.close()


def init_db():
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                chunk TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        columns = {
            row["name"]
            for row in db.execute("PRAGMA table_info(documents)").fetchall()
        }
        if "embedding" not in columns:
            db.execute("ALTER TABLE documents ADD COLUMN embedding TEXT")


def add_message(session_id, role, content):
    with connect() as db:
        db.execute(
            "INSERT INTO messages(session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )


def get_history(session_id, limit=50):
    with connect() as db:
        rows = db.execute(
            """SELECT role, content, created_at FROM messages
               WHERE session_id = ? ORDER BY id DESC LIMIT ?""",
            (session_id, min(max(int(limit), 1), 100)),
        ).fetchall()
    return [dict(row) for row in reversed(rows)]


def delete_session(session_id):
    with connect() as db:
        db.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))


def _serialize_embedding(vector):
    if vector is None:
        return None
    if not isinstance(vector, (list, tuple)) or not vector:
        raise ValueError("Each embedding must be a non-empty vector.")
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        for value in vector
    ):
        raise ValueError("Embedding values must be finite numbers.")
    return json.dumps([float(value) for value in vector])


def add_document(name, chunk, embedding=None):
    encoded = _serialize_embedding(embedding)
    with connect() as db:
        db.execute(
            "INSERT INTO documents(name, chunk, embedding) VALUES (?, ?, ?)",
            (name, chunk, encoded),
        )


def replace_document(name, chunks, embeddings=None):
    chunks = list(chunks)
    if embeddings is not None:
        embeddings = list(embeddings)
        if len(embeddings) != len(chunks):
            raise ValueError("Embedding count must match chunk count.")
        encoded = [_serialize_embedding(vector) for vector in embeddings]
    else:
        encoded = [None] * len(chunks)

    with connect() as db:
        columns = {
            row["name"]
            for row in db.execute("PRAGMA table_info(documents)").fetchall()
        }
        if "embedding" not in columns:
            db.execute("ALTER TABLE documents ADD COLUMN embedding TEXT")

        db.execute("DELETE FROM documents WHERE name = ?", (name,))
        db.executemany(
            "INSERT INTO documents(name, chunk, embedding) VALUES (?, ?, ?)",
            [
                (name, chunk, vector)
                for chunk, vector in zip(chunks, encoded)
            ],
        )


def _decode_embedding(raw):
    try:
        vector = json.loads(raw)
    except (TypeError, ValueError):
        return None

    if not isinstance(vector, list) or not vector:
        return None
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        for value in vector
    ):
        return None
    return [float(value) for value in vector]


def _cosine_similarity(left, right):
    if len(left) != len(right):
        return None
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return None
    return dot / (left_norm * right_norm)


def search_documents(query, limit=4, query_embedding=None):
    limit = max(1, min(int(limit), 100))

    if query_embedding is not None:
        query_vector = _decode_embedding(json.dumps(query_embedding))
        if query_vector is not None:
            with connect() as db:
                rows = db.execute(
                    """SELECT id, name, chunk, embedding FROM documents
                       WHERE embedding IS NOT NULL"""
                ).fetchall()

            ranked = []
            for row in rows:
                vector = _decode_embedding(row["embedding"])
                if vector is None:
                    continue
                score = _cosine_similarity(query_vector, vector)
                if score is not None:
                    item = {
                        "id": row["id"],
                        "name": row["name"],
                        "chunk": row["chunk"],
                        "content": row["chunk"],
                        "score": score,
                    }
                    ranked.append(item)

            if ranked:
                ranked.sort(key=lambda item: item["score"], reverse=True)
                return ranked[:limit]

    terms = [term for term in query.split() if len(term) > 2][:8]
    if not terms:
        return []

    where = " OR ".join("chunk LIKE ?" for _ in terms)
    with connect() as db:
        rows = db.execute(
            f"""SELECT id, name, chunk FROM documents
                WHERE {where} LIMIT ?""",
            [*(f"%{term}%" for term in terms), limit],
        ).fetchall()

    return [
        {
            "id": row["id"],
            "name": row["name"],
            "chunk": row["chunk"],
            "content": row["chunk"],
        }
        for row in rows
    ]

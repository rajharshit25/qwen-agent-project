from backend.database import db as document_db


def test_readding_document_name_replaces_all_chunks(tmp_path, monkeypatch):
    test_db = tmp_path / "documents_test.db"
    monkeypatch.setattr(
        document_db,
        "settings",
        type("TestSettings", (), {"database_path": str(test_db)})(),
    )

    document_db.init_db()
    document_db.replace_document(
        "sample",
        ["Old document content."],
    )
    document_db.replace_document(
        "sample",
        ["New document chunk one.", "New document chunk two."],
    )

    with document_db.connect() as db:
        rows = db.execute(
            "SELECT name, chunk FROM documents WHERE name = ? ORDER BY id",
            ("sample",),
        ).fetchall()

    assert len(rows) == 2
    assert [row["chunk"] for row in rows] == [
        "New document chunk one.",
        "New document chunk two.",
    ]


def test_semantic_search_ranks_closest_embedding_first(tmp_path, monkeypatch):
    test_db = tmp_path / "semantic_documents_test.db"
    monkeypatch.setattr(
        document_db,
        "settings",
        type("TestSettings", (), {"database_path": str(test_db)})(),
    )

    document_db.init_db()
    document_db.replace_document(
        "sample.txt",
        [
            "Python programming uses functions.",
            "A kitten is a young domestic cat.",
        ],
        embeddings=[
            [0.0, 1.0],
            [0.99, 0.01],
        ],
    )

    results = document_db.search_documents(
        "Tell me about cats.",
        limit=2,
        query_embedding=[1.0, 0.0],
    )

    assert results
    assert "kitten" in results[0]["chunk"].lower()
    assert results[0]["content"] == results[0]["chunk"]
    assert results[0]["score"] > 0.9


def test_lexical_search_works_without_embeddings(tmp_path, monkeypatch):
    test_db = tmp_path / "lexical_documents_test.db"
    monkeypatch.setattr(
        document_db,
        "settings",
        type("TestSettings", (), {"database_path": str(test_db)})(),
    )

    document_db.init_db()
    document_db.replace_document(
        "python.txt",
        ["Python uses functions and variables."],
    )

    results = document_db.search_documents("Python", limit=5)

    assert results
    assert any("Python" in item["chunk"] for item in results)


def test_init_db_migrates_legacy_documents_table(tmp_path, monkeypatch):
    import sqlite3

    test_db = tmp_path / "legacy_documents_test.db"
    monkeypatch.setattr(
        document_db,
        "settings",
        type("TestSettings", (), {"database_path": str(test_db)})(),
    )

    with sqlite3.connect(test_db) as db:
        db.execute(
            """
            CREATE TABLE documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                chunk TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        db.execute(
            "INSERT INTO documents (name, chunk) VALUES (?, ?)",
            ("legacy.txt", "Existing legacy content."),
        )

    document_db.init_db()

    with document_db.connect() as db:
        columns = {
            row["name"]
            for row in db.execute("PRAGMA table_info(documents)").fetchall()
        }
        row = db.execute(
            "SELECT name, chunk, embedding FROM documents WHERE name = ?",
            ("legacy.txt",),
        ).fetchone()

    assert "embedding" in columns
    assert row["chunk"] == "Existing legacy content."
    assert row["embedding"] is None

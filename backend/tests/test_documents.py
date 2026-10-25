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

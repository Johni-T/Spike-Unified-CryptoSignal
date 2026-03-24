import sqlite3
from types import SimpleNamespace

from app.storage import db as db_module


def test_init_db_creates_signal_label_and_indexes(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "signals.db"
    test_settings = SimpleNamespace(db_path=str(db_path))
    monkeypatch.setattr(db_module, "settings", test_settings)

    db_module.init_db()

    with sqlite3.connect(db_path) as conn:
        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(signals)").fetchall()
        }
        indexes = {
            row[1] for row in conn.execute("PRAGMA index_list(signals)").fetchall()
        }

    assert "signal_label" in columns
    assert "bot_id" in columns
    assert "bot_version" in columns
    assert "signal_text" in columns
    assert "idx_signals_label_at" in indexes

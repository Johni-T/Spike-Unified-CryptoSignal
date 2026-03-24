import json
import os
import sqlite3
from contextlib import contextmanager

from app.config import settings


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS signals (
    id                  TEXT PRIMARY KEY,
    bot_id              TEXT NOT NULL,
    bot_version         TEXT NOT NULL DEFAULT 'legacy',
    signal_type         TEXT NOT NULL,
    signal_label        TEXT NOT NULL,
    strategy_version    TEXT NOT NULL,
    symbol              TEXT NOT NULL,
    timeframe           TEXT NOT NULL,
    baseline_method     TEXT NOT NULL DEFAULT 'median',
    signal_at           TIMESTAMP NOT NULL,
    closed_at           TIMESTAMP,
    direction           TEXT NOT NULL,
    entry_price         REAL NOT NULL,
    exit_price          REAL,
    outcome             TEXT,
    pnl_abs             REAL,
    pnl_pct             REAL,
    spike_multiplier    REAL,
    baseline_volume     REAL,
    spike_volume        REAL,
    confirmation_volume REAL,
    drop_pct            REAL,
    message_id          INTEGER,
    signal_text         TEXT,
    title               TEXT,
    notes               TEXT,
    meta_json           TEXT
);
"""

INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS idx_signals_type_at ON signals(signal_type, signal_at);
CREATE INDEX IF NOT EXISTS idx_signals_label_at ON signals(signal_label, signal_at);
CREATE INDEX IF NOT EXISTS idx_signals_market_at ON signals(symbol, timeframe, signal_at);
CREATE INDEX IF NOT EXISTS idx_signals_type_outcome_at ON signals(signal_type, outcome, signal_at);
"""

REQUIRED_COLUMNS = {
    "bot_id": "TEXT NOT NULL DEFAULT 'unified-sniper-bot'",
    "bot_version": "TEXT NOT NULL DEFAULT 'legacy'",
    "signal_type": "TEXT NOT NULL DEFAULT 'legacy'",
    "signal_label": "TEXT NOT NULL DEFAULT 'LEGACY'",
    "strategy_version": "TEXT NOT NULL DEFAULT 'legacy'",
    "timeframe": "TEXT NOT NULL DEFAULT '5m'",
    "baseline_method": "TEXT NOT NULL DEFAULT 'median'",
    "baseline_volume": "REAL",
    "spike_volume": "REAL",
    "confirmation_volume": "REAL",
    "signal_text": "TEXT",
    "title": "TEXT",
    "meta_json": "TEXT",
}


def init_db() -> None:
    os.makedirs(os.path.dirname(settings.db_path), exist_ok=True)
    with sqlite3.connect(settings.db_path, timeout=30) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=30000;")
        conn.executescript(CREATE_TABLE_SQL)
        existing = {
            row[1] for row in conn.execute("PRAGMA table_info(signals)").fetchall()
        }
        for column, ddl in REQUIRED_COLUMNS.items():
            if column not in existing:
                conn.execute(f"ALTER TABLE signals ADD COLUMN {column} {ddl}")
        conn.executescript(INDEXES_SQL)


@contextmanager
def connect():
    conn = sqlite3.connect(settings.db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def get_table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    return {
        row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    }


def dumps_meta(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True)

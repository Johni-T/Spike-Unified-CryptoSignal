import sqlite3
from datetime import datetime, timezone
from types import SimpleNamespace

from app.domain.enums import Direction, SignalType
from app.domain.models import Candle, OpenSignalEvent
from app.storage import db as db_module
from app.storage.db import init_db
from app.storage.signal_repository import SignalRepository


LEGACY_SCHEMA_SQL = """
CREATE TABLE signals (
    id                  TEXT PRIMARY KEY,
    bot_id              TEXT NOT NULL,
    bot_version         TEXT NOT NULL DEFAULT 'legacy',
    symbol              TEXT DEFAULT 'BTCUSDT',
    signal_at           TIMESTAMP,
    closed_at           TIMESTAMP,
    direction           TEXT,
    entry_price         REAL,
    exit_price          REAL,
    outcome             TEXT,
    pnl_abs             REAL,
    pnl_pct             REAL,
    spike_multiplier    REAL,
    drop_pct            REAL,
    volume              REAL,
    avg_volume          REAL,
    ratio               REAL,
    message_id          INTEGER,
    signal_text         TEXT,
    notes               TEXT
);
"""


def test_add_signal_supports_legacy_schema_with_required_bot_id(
    monkeypatch, tmp_path
) -> None:
    db_path = tmp_path / "signals.db"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(LEGACY_SCHEMA_SQL)

    test_settings = SimpleNamespace(
        db_path=str(db_path),
        bot_id="unified-sniper-bot",
        bot_version="1.0.0",
    )
    monkeypatch.setattr(db_module, "settings", test_settings)

    from app.storage import signal_repository as signal_repository_module

    monkeypatch.setattr(signal_repository_module, "settings", test_settings)
    init_db()

    event = OpenSignalEvent(
        signal_id="legacy-test-signal",
        signal_type=SignalType.EARLY_REVERSAL,
        strategy_version="1.0.0",
        symbol="BTCUSDT",
        timeframe="5m",
        direction=Direction.PUT,
        signal_at=datetime(2026, 3, 23, 13, 5, tzinfo=timezone.utc),
        entry_price=100.0,
        spike_multiplier=3.0,
        baseline_volume=10.0,
        spike_volume=30.0,
        chart_candles=[
            Candle(
                open_time=1,
                open=100.0,
                high=101.0,
                low=99.0,
                close=110.0,
                volume=30.0,
            )
        ],
        trigger_candle=Candle(
            open_time=1,
            open=100.0,
            high=101.0,
            low=99.0,
            close=110.0,
            volume=30.0,
        ),
        notes="compat test",
        meta={"baseline_method": "median"},
    )

    SignalRepository().add_signal(event, 12345, "EARLY SPIKE")

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT bot_id, bot_version, signal_type, signal_label, title, strategy_version, timeframe, ratio
            FROM signals
            WHERE id = ?
            """,
            (event.signal_id,),
        ).fetchone()

    assert row == (
        "unified-sniper-bot",
        "1.0.0",
        "early_reversal",
        "EARLY SPIKE",
        "EARLY SPIKE",
        "1.0.0",
        "5m",
        3.0,
    )

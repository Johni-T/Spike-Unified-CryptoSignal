import sqlite3
from types import SimpleNamespace

from app.storage import db as db_module
from app.storage.db import init_db
from app.storage.signal_repository import SignalRepository
from app.storage.stats_repository import StatsRepository


def test_stats_and_recent_support_multiple_signal_types(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "signals.db"
    test_settings = SimpleNamespace(
        db_path=str(db_path),
        bot_id="unified-sniper-bot",
        bot_version="1.0.0",
    )
    monkeypatch.setattr(db_module, "settings", test_settings)

    from app.storage import signal_repository as signal_repository_module

    monkeypatch.setattr(signal_repository_module, "settings", test_settings)
    init_db()

    rows = [
        (
            "rev-1",
            "confirmed_spike_reversal",
            "CONFIRMED SPIKE REVERSAL",
            "2026-04-10T11:00:00+00:00",
            "WIN",
        ),
        (
            "cont-1",
            "confirmed_spike_continuation",
            "CONFIRMED SPIKE CONTINUATION",
            "2026-04-10T12:00:00+00:00",
            "LOSS",
        ),
        (
            "early-1",
            "early_reversal",
            "EARLY SPIKE",
            "2026-04-10T13:00:00+00:00",
            "WIN",
        ),
    ]

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO signals (
                id, bot_id, bot_version, signal_type, signal_label, strategy_version,
                symbol, timeframe, baseline_method, signal_at, direction, entry_price,
                outcome
            ) VALUES (?, 'unified-sniper-bot', '1.0.0', ?, ?, '1.0.0', 'BTCUSDT', '5m',
                'median', ?, 'CALL', 100.0, ?)
            """,
            rows,
        )

    signal_types = (
        "confirmed_spike_reversal",
        "confirmed_spike_continuation",
    )
    stats = StatsRepository().get_stats(signal_types)
    recent = SignalRepository().get_recent(limit=10, signal_type=signal_types)

    assert stats["all"]["wins"] == 1
    assert stats["all"]["losses"] == 1
    assert stats["all"]["winrate"] == 50.0
    assert [row["signal_type"] for row in recent] == [
        "confirmed_spike_continuation",
        "confirmed_spike_reversal",
    ]

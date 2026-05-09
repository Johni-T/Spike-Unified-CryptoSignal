from datetime import datetime, timezone

from app.delivery.presenters import build_open_caption
from app.domain.enums import Direction, SignalType
from app.domain.models import Candle, OpenSignalEvent


def _stats() -> dict:
    return {
        "day": {"wins": 3, "losses": 1, "winrate": 75.0},
        "week": {"wins": 10, "losses": 5, "winrate": 66.7},
        "all": {"wins": 20, "losses": 10, "winrate": 66.7},
    }


def _event(signal_type: SignalType) -> OpenSignalEvent:
    candle = Candle(
        open_time=1,
        open=100.0,
        high=110.0,
        low=95.0,
        close=108.0,
        volume=300.0,
    )
    return OpenSignalEvent(
        signal_id="signal-1",
        signal_type=signal_type,
        strategy_version="1.0.0",
        symbol="BTCUSDT",
        timeframe="5m",
        direction=Direction.CALL,
        signal_at=datetime(2026, 3, 24, 12, 0, tzinfo=timezone.utc),
        entry_price=108.0,
        spike_multiplier=3.5,
        baseline_volume=100.0,
        spike_volume=300.0,
        chart_candles=[candle],
        trigger_candle=candle,
        drop_pct=25.0,
        confirmation_volume=225.0,
        notes="should stay hidden",
    )


def test_build_open_caption_uses_spike_labels_and_hides_notes() -> None:
    title, caption = build_open_caption(_event(SignalType.EARLY_REVERSAL), _stats())

    assert title == "EARLY SPIKE"
    assert "EARLY SPIKE" in caption
    assert "Notes" not in caption
    assert "All:" in caption


def test_build_open_caption_uses_confirmed_spike_label() -> None:
    title, caption = build_open_caption(
        _event(SignalType.CONFIRMED_SPIKE_REVERSAL), _stats()
    )

    assert title == "CONFIRMED SPIKE REVERSAL"
    assert "CONFIRMED SPIKE REVERSAL" in caption


def test_build_open_caption_uses_confirmed_spike_continuation_label() -> None:
    title, caption = build_open_caption(
        _event(SignalType.CONFIRMED_SPIKE_CONTINUATION), _stats()
    )

    assert title == "CONFIRMED SPIKE CONTINUATION"
    assert "CONFIRMED SPIKE CONTINUATION" in caption

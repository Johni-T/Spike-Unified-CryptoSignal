from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.domain.enums import Direction, Outcome, SignalType


@dataclass(frozen=True)
class Candle:
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float

    @property
    def is_bullish(self) -> bool:
        return self.close >= self.open

    @property
    def opened_at(self) -> datetime:
        return datetime.fromtimestamp(self.open_time / 1000, tz=timezone.utc)

    @classmethod
    def from_rest(cls, raw: list[Any]) -> "Candle":
        return cls(
            open_time=raw[0],
            open=float(raw[1]),
            high=float(raw[2]),
            low=float(raw[3]),
            close=float(raw[4]),
            volume=float(raw[5]),
        )

    @classmethod
    def from_ws(cls, payload: dict[str, Any]) -> "Candle":
        return cls(
            open_time=payload["t"],
            open=float(payload["o"]),
            high=float(payload["h"]),
            low=float(payload["l"]),
            close=float(payload["c"]),
            volume=float(payload["v"]),
        )


@dataclass(frozen=True)
class OpenSignalEvent:
    signal_id: str
    signal_type: SignalType
    strategy_version: str
    symbol: str
    timeframe: str
    direction: Direction
    signal_at: datetime
    entry_price: float
    spike_multiplier: float
    baseline_volume: float
    spike_volume: float
    chart_candles: list[Candle]
    trigger_candle: Candle
    confirmation_candle: Candle | None = None
    drop_pct: float | None = None
    confirmation_volume: float | None = None
    notes: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResolveSignalEvent:
    signal_id: str
    closed_at: datetime
    exit_price: float
    outcome: Outcome
    pnl_abs: float
    pnl_pct: float

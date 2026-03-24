from app.domain.enums import Direction, SignalType
from app.domain.models import Candle, OpenSignalEvent, ResolveSignalEvent
from app.strategies.base import BaseStrategy
from app.strategies.shared.outcome import evaluate_outcome
from app.strategies.shared.volume_baseline import mean_volume


class EarlyReversalStrategy(BaseStrategy):
    key = SignalType.EARLY_REVERSAL.value
    display_name = "Early Spike"
    version = "1.0.0"

    def on_closed_candle(
        self,
        symbol: str,
        timeframe: str,
        candles: list[Candle],
        state: dict,
    ) -> tuple[list[OpenSignalEvent], list[ResolveSignalEvent]]:
        opens: list[OpenSignalEvent] = []
        resolves: list[ResolveSignalEvent] = []
        latest = candles[-1]

        active = state.get("active_signal")
        if active:
            outcome, pnl_abs, pnl_pct = evaluate_outcome(
                active["direction"], active["entry_price"], latest.close
            )
            resolves.append(
                ResolveSignalEvent(
                    signal_id=active["signal_id"],
                    closed_at=latest.opened_at,
                    exit_price=latest.close,
                    outcome=outcome,
                    pnl_abs=pnl_abs,
                    pnl_pct=pnl_pct,
                )
            )
            state["active_signal"] = None

        previous = candles[:-1]
        baseline = mean_volume(previous, self.baseline_window)
        if baseline is None:
            return opens, resolves

        ratio = latest.volume / baseline
        if ratio < self.spike_multiplier:
            return opens, resolves

        direction = Direction.PUT if latest.is_bullish else Direction.CALL
        signal_id = f"{self.key}_{symbol}_{timeframe}_{latest.open_time}"
        event = OpenSignalEvent(
            signal_id=signal_id,
            signal_type=SignalType.EARLY_REVERSAL,
            strategy_version=self.version,
            symbol=symbol,
            timeframe=timeframe,
            direction=direction,
            signal_at=latest.opened_at,
            entry_price=latest.close,
            spike_multiplier=ratio,
            baseline_volume=baseline,
            spike_volume=latest.volume,
            chart_candles=candles[-self.candles_on_chart :],
            trigger_candle=latest,
            meta={"baseline_method": "mean"},
        )
        opens.append(event)
        state["active_signal"] = {
            "signal_id": signal_id,
            "direction": direction,
            "entry_price": latest.close,
        }
        return opens, resolves

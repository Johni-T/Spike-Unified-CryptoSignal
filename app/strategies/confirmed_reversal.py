from app.domain.enums import Direction, SignalType
from app.domain.models import Candle, OpenSignalEvent, ResolveSignalEvent
from app.strategies.base import BaseStrategy
from app.strategies.shared.outcome import evaluate_outcome
from app.strategies.shared.volume_baseline import median_volume


class ConfirmedReversalStrategy(BaseStrategy):
    key = "confirmed_reversal"
    display_name = "Confirmed Spike"
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

        pending = state.get("pending_spike")
        if pending:
            state["pending_spike"] = None
            if latest.volume >= pending["spike_candle"].volume:
                return opens, resolves

            spike_candle = pending["spike_candle"]
            drop_pct = (spike_candle.volume - latest.volume) / spike_candle.volume * 100
            if spike_candle.is_bullish != latest.is_bullish:
                direction = Direction.CALL if spike_candle.is_bullish else Direction.PUT
                signal_type = SignalType.CONFIRMED_SPIKE_CONTINUATION
            else:
                direction = Direction.PUT if spike_candle.is_bullish else Direction.CALL
                signal_type = SignalType.CONFIRMED_SPIKE_REVERSAL

            signal_id = f"{signal_type.value}_{symbol}_{timeframe}_{spike_candle.open_time}"
            event = OpenSignalEvent(
                signal_id=signal_id,
                signal_type=signal_type,
                strategy_version=self.version,
                symbol=symbol,
                timeframe=timeframe,
                direction=direction,
                signal_at=latest.opened_at,
                entry_price=latest.close,
                spike_multiplier=pending["ratio"],
                baseline_volume=pending["baseline_volume"],
                spike_volume=spike_candle.volume,
                chart_candles=candles[-self.candles_on_chart :],
                trigger_candle=spike_candle,
                confirmation_candle=latest,
                drop_pct=drop_pct,
                confirmation_volume=latest.volume,
                meta={"baseline_method": "median"},
            )
            opens.append(event)
            state["active_signal"] = {
                "signal_id": signal_id,
                "direction": direction,
                "entry_price": latest.close,
            }
            return opens, resolves

        previous = candles[:-1]
        baseline = median_volume(previous, self.baseline_window)
        if baseline is None:
            return opens, resolves

        ratio = latest.volume / baseline
        if ratio >= self.spike_multiplier:
            state["pending_spike"] = {
                "spike_candle": latest,
                "ratio": ratio,
                "baseline_volume": baseline,
            }
        return opens, resolves

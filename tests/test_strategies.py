from app.domain.enums import Direction
from app.domain.models import Candle
from app.strategies.confirmed_reversal import ConfirmedReversalStrategy
from app.strategies.early_reversal import EarlyReversalStrategy
from app.strategies.shared.volume_baseline import mean_volume, median_volume


def candle(
    open_time: int, open_price: float, close_price: float, volume: float
) -> Candle:
    high = max(open_price, close_price) + 1
    low = min(open_price, close_price) - 1
    return Candle(
        open_time=open_time,
        open=open_price,
        high=high,
        low=low,
        close=close_price,
        volume=volume,
    )


def test_median_volume_ignores_extreme_spike_effect() -> None:
    candles = [
        candle(idx, 100, 101, volume)
        for idx, volume in enumerate([10, 11, 9, 10, 500], start=1)
    ]
    assert median_volume(candles, 5) == 10


def test_mean_volume_absorbs_extreme_spike_effect() -> None:
    candles = [
        candle(idx, 100, 101, volume)
        for idx, volume in enumerate([10, 11, 9, 10, 500], start=1)
    ]
    assert mean_volume(candles, 5) == 108


def test_early_reversal_opposes_green_spike() -> None:
    strategy = EarlyReversalStrategy(
        baseline_window=5, spike_multiplier=2.5, candles_on_chart=10
    )
    series = [candle(idx, 100, 101, 10) for idx in range(1, 6)]
    series.append(candle(6, 100, 110, 30))
    opens, resolves = strategy.on_closed_candle("BTCUSDT", "5m", series, {})
    assert not resolves
    assert len(opens) == 1
    assert opens[0].direction == Direction.PUT


def test_confirmed_reversal_uses_pending_spike_then_opens_signal() -> None:
    strategy = ConfirmedReversalStrategy(
        baseline_window=5, spike_multiplier=2.5, candles_on_chart=10
    )
    state = {}
    base = [candle(idx, 100, 101, 10) for idx in range(1, 6)]
    spike = candle(6, 100, 110, 30)
    opens, resolves = strategy.on_closed_candle("BTCUSDT", "5m", base + [spike], state)
    assert not opens
    assert not resolves
    confirm = candle(7, 110, 105, 15)
    opens, resolves = strategy.on_closed_candle(
        "BTCUSDT", "5m", base + [spike, confirm], state
    )
    assert not resolves
    assert len(opens) == 1
    assert opens[0].direction == Direction.CALL


def test_early_reversal_mean_baseline_filters_follow_up_noise() -> None:
    strategy = EarlyReversalStrategy(
        baseline_window=5, spike_multiplier=2.5, candles_on_chart=10
    )
    state = {}
    base = [
        candle(idx, 100, 101, volume)
        for idx, volume in enumerate([10, 11, 9, 10, 12], start=1)
    ]
    first_spike = candle(6, 100, 110, 500)
    opens, resolves = strategy.on_closed_candle("BTCUSDT", "5m", base + [first_spike], state)
    assert len(opens) == 1
    assert not resolves

    follow_up = candle(7, 110, 112, 130)
    opens, resolves = strategy.on_closed_candle(
        "BTCUSDT", "5m", base + [first_spike, follow_up], state
    )
    assert not opens
    assert len(resolves) == 1

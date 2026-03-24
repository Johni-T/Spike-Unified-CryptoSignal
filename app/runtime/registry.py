from app.config import MarketConfig, settings
from app.strategies.confirmed_reversal import ConfirmedReversalStrategy
from app.strategies.early_reversal import EarlyReversalStrategy
from app.strategies.base import BaseStrategy


def build_registry() -> dict[str, list[BaseStrategy]]:
    strategies: list[BaseStrategy] = []
    if "early_reversal" in settings.enabled_strategies:
        strategies.append(
            EarlyReversalStrategy(
                settings.baseline_window,
                settings.spike_multiplier,
                settings.candles_on_chart,
            )
        )
    if "confirmed_reversal" in settings.enabled_strategies:
        strategies.append(
            ConfirmedReversalStrategy(
                settings.baseline_window,
                settings.spike_multiplier,
                settings.candles_on_chart,
            )
        )
    return {
        market.key: [strategy.clone() for strategy in strategies]
        for market in settings.markets
    }


def list_markets() -> list[MarketConfig]:
    return settings.markets

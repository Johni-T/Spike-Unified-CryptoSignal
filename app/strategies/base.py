from abc import ABC, abstractmethod

from app.domain.models import Candle, OpenSignalEvent, ResolveSignalEvent


class BaseStrategy(ABC):
    key: str
    display_name: str
    version: str

    def __init__(
        self, baseline_window: int, spike_multiplier: float, candles_on_chart: int
    ) -> None:
        self.baseline_window = baseline_window
        self.spike_multiplier = spike_multiplier
        self.candles_on_chart = candles_on_chart

    def clone(self) -> "BaseStrategy":
        return self.__class__(
            self.baseline_window, self.spike_multiplier, self.candles_on_chart
        )

    @abstractmethod
    def on_closed_candle(
        self,
        symbol: str,
        timeframe: str,
        candles: list[Candle],
        state: dict,
    ) -> tuple[list[OpenSignalEvent], list[ResolveSignalEvent]]:
        raise NotImplementedError

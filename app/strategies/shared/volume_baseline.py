import statistics

from app.domain.models import Candle


def mean_volume(candles: list[Candle], window: int) -> float | None:
    if len(candles) < window:
        return None
    sample = candles[-window:]
    baseline = statistics.fmean(candle.volume for candle in sample)
    if baseline <= 0:
        return None
    return baseline


def median_volume(candles: list[Candle], window: int) -> float | None:
    if len(candles) < window:
        return None
    sample = candles[-window:]
    baseline = statistics.median(candle.volume for candle in sample)
    if baseline <= 0:
        return None
    return baseline

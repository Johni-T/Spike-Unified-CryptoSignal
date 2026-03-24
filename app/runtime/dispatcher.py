import logging

from app.config import MarketConfig
from app.delivery.charting import render_chart
from app.delivery.presenters import build_close_caption, build_open_caption
from app.delivery.telegram_client import TelegramDelivery
from app.runtime.market_data import MarketDataStream
from app.runtime.state_store import StateStore
from app.storage.signal_repository import SignalRepository
from app.storage.stats_repository import StatsRepository


logger = logging.getLogger(__name__)


def _empty_stats() -> dict:
    return {
        "day": {"wins": 0, "losses": 0, "total": 0, "winrate": 0.0},
        "week": {"wins": 0, "losses": 0, "total": 0, "winrate": 0.0},
        "month": {"wins": 0, "losses": 0, "total": 0, "winrate": 0.0},
        "all": {"wins": 0, "losses": 0, "total": 0, "winrate": 0.0},
    }


class MarketDispatcher:
    def __init__(
        self, market: MarketConfig, strategies: list, state_store: StateStore
    ) -> None:
        self.market = market
        self.strategies = strategies
        self.state_store = state_store
        self.stream = MarketDataStream(market)
        self.delivery = TelegramDelivery()
        self.signals = SignalRepository()
        self.stats = StatsRepository()

    async def run(self) -> None:
        await self.stream.warmup()
        async for _ in self.stream.iter_closed_candles():
            candles = list(self.stream.candles)
            for strategy in self.strategies:
                try:
                    state = self.state_store.get(
                        strategy.key, self.market.symbol, self.market.timeframe
                    )
                    sent_signals = state.setdefault("sent_signals", {})
                    open_events, resolve_events = strategy.on_closed_candle(
                        self.market.symbol, self.market.timeframe, candles, state
                    )
                    for event in resolve_events:
                        row = None
                        sent_meta = sent_signals.pop(event.signal_id, {})
                        try:
                            self.signals.resolve_signal(event)
                            row = self.signals.get_signal(event.signal_id)
                        except Exception:
                            logger.exception(
                                "Failed to persist resolved signal %s", event.signal_id
                            )
                        signal_type = sent_meta.get("signal_type") or (
                            row["signal_type"] if row else None
                        )
                        try:
                            stats = (
                                self.stats.get_stats(signal_type)
                                if signal_type
                                else _empty_stats()
                            )
                        except Exception:
                            logger.exception(
                                "Failed to load stats for resolved signal %s",
                                event.signal_id,
                            )
                            stats = _empty_stats()
                        caption = build_close_caption(
                            sent_meta.get("caption")
                            or (row["title"] if row and row["title"] else None)
                            or (row["signal_type"] if row else event.signal_id),
                            event.outcome,
                            event.exit_price,
                            event.pnl_abs,
                            event.pnl_pct,
                            stats,
                        )
                        try:
                            await self.delivery.edit_caption(
                                sent_meta.get("message_id")
                                or (row["message_id"] if row else None),
                                caption,
                            )
                        except Exception:
                            logger.exception(
                                "Failed to edit caption for signal %s", event.signal_id
                            )
                            continue
                        logger.info(
                            "Resolved signal %s as %s",
                            event.signal_id,
                            event.outcome.value,
                        )
                    for event in open_events:
                        chart = render_chart(
                            event.chart_candles,
                            event.signal_type,
                            event.direction.value,
                            event.symbol,
                            event.timeframe,
                        )
                        try:
                            stats = self.stats.get_stats(event.signal_type.value)
                        except Exception:
                            logger.exception(
                                "Failed to load stats for %s", event.signal_type.value
                            )
                            stats = _empty_stats()
                        title, caption = build_open_caption(event, stats)
                        message_id = await self.delivery.send_photo(chart, caption)
                        sent_signals[event.signal_id] = {
                            "message_id": message_id,
                            "caption": caption,
                            "signal_type": event.signal_type.value,
                        }
                        try:
                            self.signals.add_signal(event, message_id, title)
                        except Exception:
                            logger.exception(
                                "Failed to persist opened signal %s", event.signal_id
                            )
                        logger.info(
                            "Opened %s signal %s",
                            event.signal_type.value,
                            event.signal_id,
                        )
                except Exception:
                    logger.exception(
                        "Strategy %s failed for %s %s",
                        strategy.key,
                        self.market.symbol,
                        self.market.timeframe,
                    )

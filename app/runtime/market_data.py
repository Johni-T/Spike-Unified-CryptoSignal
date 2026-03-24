import asyncio
import json
import logging
from collections import deque
from collections.abc import AsyncIterator

import aiohttp

from app.config import MarketConfig, settings
from app.domain.models import Candle


logger = logging.getLogger(__name__)


class MarketDataStream:
    def __init__(self, market: MarketConfig) -> None:
        self.market = market
        self.candles: deque[Candle] = deque(
            maxlen=max(settings.candles_on_chart * 4, settings.baseline_window + 10)
        )

    async def warmup(self) -> None:
        params = {
            "symbol": self.market.symbol,
            "interval": self.market.timeframe,
            "limit": max(settings.candles_on_chart * 4, settings.baseline_window + 10),
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(settings.rest_base, params=params) as response:
                payload = await response.json()
        for item in payload[:-1]:
            self.candles.append(Candle.from_rest(item))
        logger.info(
            "Warmup complete for %s %s with %s candles",
            self.market.symbol,
            self.market.timeframe,
            len(self.candles),
        )

    async def iter_closed_candles(self) -> AsyncIterator[Candle]:
        url = f"{settings.ws_base}/{self.market.symbol.lower()}@kline_{self.market.timeframe}"
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(
                        url, heartbeat=20, receive_timeout=60
                    ) as ws:
                        async for msg in ws:
                            if msg.type != aiohttp.WSMsgType.TEXT:
                                break
                            payload = json.loads(msg.data)
                            kline = payload.get("k")
                            if not kline or not kline.get("x"):
                                continue
                            candle = Candle.from_ws(kline)
                            self.candles.append(candle)
                            yield candle
            except Exception as exc:
                logger.warning(
                    "Market stream error for %s %s: %s",
                    self.market.symbol,
                    self.market.timeframe,
                    exc,
                )
                await asyncio.sleep(5)

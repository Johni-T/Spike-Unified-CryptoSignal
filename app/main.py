import asyncio
import logging
import sys

from app.bot_api.commands import build_application
from app.config import settings
from app.runtime.dispatcher import MarketDispatcher
from app.runtime.registry import build_registry, list_markets
from app.runtime.state_store import StateStore
from app.storage.db import init_db


logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.INFO)


async def main() -> None:
    init_db()
    app = build_application()
    state_store = StateStore()
    registry = build_registry()
    dispatchers = [
        MarketDispatcher(market, registry[market.key], state_store)
        for market in list_markets()
    ]
    async with app:
        await app.start()
        await app.updater.start_polling()
        tasks = [asyncio.create_task(dispatcher.run()) for dispatcher in dispatchers]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())

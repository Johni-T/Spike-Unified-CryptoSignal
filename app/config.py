import os
from dataclasses import dataclass


@dataclass(frozen=True)
class MarketConfig:
    symbol: str
    timeframe: str

    @property
    def key(self) -> str:
        return f"{self.symbol}:{self.timeframe}"


@dataclass(frozen=True)
class Settings:
    bot_id: str
    bot_version: str
    telegram_token: str
    telegram_chat_id: str
    db_path: str
    markets: list[MarketConfig]
    enabled_strategies: list[str]
    baseline_window: int
    spike_multiplier: float
    candles_on_chart: int
    log_level: str
    rest_base: str = "https://api.binance.com/api/v3/klines"
    ws_base: str = "wss://stream.binance.com:9443/ws"


def _parse_markets(raw: str) -> list[MarketConfig]:
    items = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        symbol, timeframe = chunk.split(":", 1)
        items.append(MarketConfig(symbol=symbol.upper(), timeframe=timeframe))
    if not items:
        items.append(MarketConfig(symbol="BTCUSDT", timeframe="5m"))
    return items


def load_settings() -> Settings:
    markets = _parse_markets(os.getenv("MARKETS", "BTCUSDT:5m"))
    strategies = [
        item.strip()
        for item in os.getenv(
            "ENABLED_STRATEGIES", "early_reversal,confirmed_reversal"
        ).split(",")
        if item.strip()
    ]
    return Settings(
        bot_id=os.getenv("BOT_ID", "unified-sniper-bot"),
        bot_version=os.getenv("BOT_VERSION", "1.0.0"),
        telegram_token=os.getenv("TELEGRAM_TOKEN", ""),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID", ""),
        db_path=os.getenv("SHARED_DB_PATH", "/shared-data/signals.db"),
        markets=markets,
        enabled_strategies=strategies,
        baseline_window=int(os.getenv("BASELINE_WINDOW", "20")),
        spike_multiplier=float(os.getenv("SPIKE_MULTIPLIER", "2.5")),
        candles_on_chart=int(os.getenv("CANDLES_ON_CHART", "30")),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )


settings = load_settings()

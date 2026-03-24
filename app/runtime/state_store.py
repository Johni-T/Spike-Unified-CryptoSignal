class StateStore:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str, str], dict] = {}

    def get(self, strategy_key: str, symbol: str, timeframe: str) -> dict:
        return self._items.setdefault((strategy_key, symbol, timeframe), {})

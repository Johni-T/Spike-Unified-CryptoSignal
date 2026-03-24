from app.config import settings
from app.delivery.presenters import TYPE_LABELS
from app.domain.models import OpenSignalEvent, ResolveSignalEvent
from app.storage.db import connect, dumps_meta, get_table_columns


class SignalRepository:
    def add_signal(
        self, event: OpenSignalEvent, message_id: int | None, title: str
    ) -> None:
        payload = {
            "id": event.signal_id,
            "bot_id": settings.bot_id,
            "bot_version": settings.bot_version,
            "signal_type": event.signal_type.value,
            "signal_label": TYPE_LABELS[event.signal_type],
            "strategy_version": event.strategy_version,
            "symbol": event.symbol,
            "timeframe": event.timeframe,
            "baseline_method": event.meta.get("baseline_method", "median"),
            "signal_at": event.signal_at.isoformat(),
            "direction": event.direction.value,
            "entry_price": event.entry_price,
            "spike_multiplier": event.spike_multiplier,
            "baseline_volume": event.baseline_volume,
            "spike_volume": event.spike_volume,
            "confirmation_volume": event.confirmation_volume,
            "drop_pct": event.drop_pct,
            "message_id": message_id,
            "signal_text": title,
            "title": title,
            "notes": event.notes,
            "meta_json": dumps_meta(event.meta),
            "volume": event.spike_volume,
            "avg_volume": event.baseline_volume,
            "ratio": event.spike_multiplier,
        }
        with connect() as conn:
            columns = get_table_columns(conn, "signals")
            insert_payload = {
                column: value for column, value in payload.items() if column in columns
            }
            placeholders = ", ".join("?" for _ in insert_payload)
            sql = f"""
                INSERT OR REPLACE INTO signals (
                    {", ".join(insert_payload)}
                ) VALUES ({placeholders})
            """
            conn.execute(sql, tuple(insert_payload.values()))

    def resolve_signal(self, event: ResolveSignalEvent) -> None:
        with connect() as conn:
            conn.execute(
                """
                UPDATE signals
                   SET closed_at = ?, exit_price = ?, outcome = ?, pnl_abs = ?, pnl_pct = ?
                 WHERE id = ?
                """,
                (
                    event.closed_at.isoformat(),
                    event.exit_price,
                    event.outcome.value,
                    event.pnl_abs,
                    event.pnl_pct,
                    event.signal_id,
                ),
            )

    def get_signal(self, signal_id: str):
        with connect() as conn:
            return conn.execute(
                "SELECT * FROM signals WHERE id = ?", (signal_id,)
            ).fetchone()

    def get_recent(self, limit: int = 10, signal_type: str | None = None):
        with connect() as conn:
            if signal_type:
                return conn.execute(
                    "SELECT * FROM signals WHERE signal_type = ? ORDER BY signal_at DESC LIMIT ?",
                    (signal_type, limit),
                ).fetchall()
            return conn.execute(
                "SELECT * FROM signals ORDER BY signal_label ASC, signal_at DESC LIMIT ?",
                (limit,),
            ).fetchall()

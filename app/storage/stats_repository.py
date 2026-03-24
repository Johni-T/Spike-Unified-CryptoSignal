from datetime import datetime, timedelta, timezone

from app.storage.db import connect


class StatsRepository:
    def get_stats(self, signal_type: str | None = None) -> dict:
        now = datetime.now(timezone.utc)
        periods = {
            "day": now.replace(hour=0, minute=0, second=0, microsecond=0),
            "week": now - timedelta(days=7),
            "month": now - timedelta(days=30),
            "all": None,
        }
        rows = self._load_rows(signal_type)
        result = {}
        for key, since in periods.items():
            if since is None:
                subset = rows
            else:
                subset = [row for row in rows if row["signal_at"] >= since]
            wins = sum(1 for row in subset if row["outcome"] == "WIN")
            losses = sum(1 for row in subset if row["outcome"] == "LOSS")
            total = wins + losses
            result[key] = {
                "wins": wins,
                "losses": losses,
                "total": total,
                "winrate": round((wins / total * 100) if total else 0.0, 1),
            }
        return result

    def _load_rows(self, signal_type: str | None) -> list[dict]:
        query = (
            "SELECT signal_at, outcome FROM signals WHERE outcome IN ('WIN', 'LOSS')"
        )
        params: tuple = ()
        if signal_type:
            query += " AND signal_type = ?"
            params = (signal_type,)
        with connect() as conn:
            raw_rows = conn.execute(query, params).fetchall()
        rows = []
        for row in raw_rows:
            rows.append(
                {
                    "signal_at": datetime.fromisoformat(row["signal_at"]).astimezone(
                        timezone.utc
                    ),
                    "outcome": row["outcome"],
                }
            )
        return rows

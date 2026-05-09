from datetime import datetime, timezone

from telegram.ext import ApplicationBuilder, CommandHandler

from app.config import settings
from app.runtime.registry import list_markets
from app.storage.signal_repository import SignalRepository
from app.storage.stats_repository import StatsRepository


CONFIRMED_SIGNAL_TYPES = (
    "confirmed_spike_reversal",
    "confirmed_spike_continuation",
)

SIGNAL_ALIASES = {
    "early": "early_reversal",
    "early_spike": "early_reversal",
    "confirmed": CONFIRMED_SIGNAL_TYPES,
    "confirmed_spike": CONFIRMED_SIGNAL_TYPES,
    "confirmed_reversal": "confirmed_spike_reversal",
    "confirmed_spike_reversal": "confirmed_spike_reversal",
    "confirmed_continuation": "confirmed_spike_continuation",
    "confirmed_spike_continuation": "confirmed_spike_continuation",
}


def _resolve_signal_type(args: list[str]) -> str | tuple[str, ...] | None:
    if not args:
        return None
    return SIGNAL_ALIASES.get(args[0].lower(), args[0].lower())


async def cmd_status(update, context) -> None:
    markets = ", ".join(
        f"{market.symbol} {market.timeframe}" for market in list_markets()
    )
    await update.message.reply_text(
        f"Unified sniper bot is running. Markets: {markets}"
    )


async def cmd_start(update, context) -> None:
    await cmd_status(update, context)


async def cmd_markets(update, context) -> None:
    text = "\n".join(
        f"- {market.symbol} {market.timeframe}" for market in list_markets()
    )
    await update.message.reply_text(f"Active markets:\n{text}")


async def cmd_stats(update, context) -> None:
    signal_type = _resolve_signal_type(context.args)
    stats = StatsRepository().get_stats(signal_type)
    if isinstance(signal_type, tuple):
        scope = ", ".join(signal_type)
    else:
        scope = signal_type or "all"
    text = (
        f"Stats scope: {scope}\n"
        f"Today: {stats['day']['wins']}W/{stats['day']['losses']}L ({stats['day']['winrate']}%)\n"
        f"Week: {stats['week']['wins']}W/{stats['week']['losses']}L ({stats['week']['winrate']}%)\n"
        f"Month: {stats['month']['wins']}W/{stats['month']['losses']}L ({stats['month']['winrate']}%)\n"
        f"All: {stats['all']['wins']}W/{stats['all']['losses']}L ({stats['all']['winrate']}%)"
    )
    await update.message.reply_text(text)


async def cmd_signals(update, context) -> None:
    signal_type = _resolve_signal_type(context.args)
    rows = SignalRepository().get_recent(limit=10, signal_type=signal_type)
    if not rows:
        await update.message.reply_text("No signals yet.")
        return
    lines = []
    for row in rows:
        ts = (
            datetime.fromisoformat(row["signal_at"])
            .astimezone(timezone.utc)
            .strftime("%d.%m %H:%M")
        )
        outcome = row["outcome"] or "OPEN"
        label = row["signal_label"] or row["title"] or row["signal_type"]
        lines.append(
            f"{ts} | {label} | {row['symbol']} {row['timeframe']} | {row['direction']} | {outcome}"
        )
    await update.message.reply_text("Recent signals:\n" + "\n".join(lines))


def build_application():
    app = ApplicationBuilder().token(settings.telegram_token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("markets", cmd_markets))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("signals", cmd_signals))
    return app

from datetime import timezone
from html import escape

from app.domain.enums import Outcome, SignalType
from app.domain.models import OpenSignalEvent


TYPE_LABELS = {
    SignalType.EARLY_REVERSAL: "EARLY SPIKE",
    SignalType.CONFIRMED_REVERSAL: "CONFIRMED SPIKE",
}
TYPE_BADGES = {
    SignalType.EARLY_REVERSAL: "Instant Spike Entry",
    SignalType.CONFIRMED_REVERSAL: "Spike Confirmed",
}
TYPE_EMOJIS = {
    SignalType.EARLY_REVERSAL: "⚡",
    SignalType.CONFIRMED_REVERSAL: "🧭",
}
TYPE_SUMMARY = {
    SignalType.EARLY_REVERSAL: "Entry right after the spike candle closes",
    SignalType.CONFIRMED_REVERSAL: "Entry after the spike gets lower-volume confirmation",
}
DIRECTION_EMOJIS = {
    "CALL": "🟢",
    "PUT": "🔴",
}
OUTCOME_LABELS = {
    Outcome.WIN: "WIN",
    Outcome.LOSS: "LOSS",
}
OUTCOME_EMOJIS = {
    Outcome.WIN: "✅",
    Outcome.LOSS: "❌",
}
OPEN_STATUS_LINE = "⏳ <b>Status:</b> <code>awaiting result</code>"


def _fmt_price(value: float) -> str:
    return f"{value:,.2f}"


def _fmt_volume(value: float) -> str:
    return f"{value:,.0f}"


def _fmt_stats_line(label: str, bucket: dict) -> str:
    return (
        f"<b>{label}:</b> "
        f"<code>{bucket['wins']}W / {bucket['losses']}L / {bucket['winrate']}%</code>"
    )


def build_open_caption(event: OpenSignalEvent, stats: dict) -> tuple[str, str]:
    title = TYPE_LABELS[event.signal_type]
    signal_emoji = TYPE_EMOJIS[event.signal_type]
    direction_emoji = DIRECTION_EMOJIS[event.direction.value]
    signal_time = event.signal_at.astimezone(timezone.utc).strftime(
        "%H:%M UTC | %d.%m.%Y"
    )
    details = []
    if event.drop_pct is not None:
        details.append(f"▫️ <b>Volume drop:</b> <code>-{event.drop_pct:.1f}%</code>")
    if event.confirmation_volume is not None:
        details.append(
            f"▫️ <b>Confirm volume:</b> <code>{_fmt_volume(event.confirmation_volume)}</code>"
        )
    caption = (
        f"{signal_emoji} <b>{escape(title)}</b>\n"
        f"<code>{escape(TYPE_BADGES[event.signal_type])}</code>\n"
        f"💬 {escape(TYPE_SUMMARY[event.signal_type])}\n\n"
        f"{direction_emoji} <b>{escape(event.direction.value)}</b>\n"
        f"🎯 <b>Entry:</b> <code>{_fmt_price(event.entry_price)}</code>\n"
        f"🪙 <b>Market:</b> <code>{escape(event.symbol)} / {escape(event.timeframe)}</code>\n"
        f"🕒 <b>Signal time:</b> <code>{signal_time}</code>\n\n"
        f"⚙️ <b>Volume setup</b>\n"
        f"▫️ <b>Spike ratio:</b> <code>x{event.spike_multiplier:.2f}</code>\n"
        f"▫️ <b>Baseline:</b> <code>{_fmt_volume(event.baseline_volume)}</code>\n"
        f"▫️ <b>Spike:</b> <code>{_fmt_volume(event.spike_volume)}</code>\n"
        f"{''.join(line + '\n' for line in details)}\n"
        f"📊 <b>Stats</b>\n"
        f"▫️ {_fmt_stats_line('Today', stats['day'])}\n"
        f"▫️ {_fmt_stats_line('7d', stats['week'])}\n"
        f"▫️ {_fmt_stats_line('All', stats['all'])}\n"
        f"{OPEN_STATUS_LINE}"
    )
    return title, caption


def build_close_caption(
    open_caption: str,
    outcome: Outcome,
    exit_price: float,
    pnl_abs: float,
    pnl_pct: float,
    stats: dict,
) -> str:
    base_caption = open_caption.replace(OPEN_STATUS_LINE, "", 1).rstrip()
    outcome_emoji = OUTCOME_EMOJIS[outcome]
    return (
        f"{base_caption}\n\n"
        f"🏁 <b>Result</b>\n"
        f"{outcome_emoji} <b>Outcome:</b> <code>{OUTCOME_LABELS[outcome]}</code>\n"
        f"📍 <b>Exit:</b> <code>{_fmt_price(exit_price)}</code>\n"
        f"💰 <b>PnL:</b> <code>{pnl_abs:+.2f} ({pnl_pct:+.3f}%)</code>\n"
        f"▫️ {_fmt_stats_line('Today', stats['day'])}\n"
        f"▫️ {_fmt_stats_line('All', stats['all'])}\n"
        f"✅ <b>Status:</b> <code>closed</code>"
    )

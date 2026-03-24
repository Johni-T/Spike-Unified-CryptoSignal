import io

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter

from app.domain.enums import SignalType
from app.domain.models import Candle


BG = "#050b14"
PANEL = "#0d1726"
PANEL_ALT = "#13233a"
GRID = "#28415f"
UP = "#12d98f"
DOWN = "#ff5b77"
TEXT = "#f4f7fb"
MUTED = "#92a8c3"
ACCENTS = {
    SignalType.EARLY_REVERSAL: "#ffb020",
    SignalType.CONFIRMED_REVERSAL: "#3db8ff",
}
SIGNAL_LABELS = {
    SignalType.EARLY_REVERSAL: "EARLY SPIKE",
    SignalType.CONFIRMED_REVERSAL: "CONFIRMED SPIKE",
}
DIR_COLORS = {
    "CALL": "#18d79a",
    "PUT": "#ff637e",
}


def _add_panel_gradient(ax, top: str, bottom: str) -> None:
    gradient = np.linspace(0, 1, 256).reshape(256, 1)
    cmap = LinearSegmentedColormap.from_list("panel_gradient", [top, bottom])
    ax.imshow(
        gradient,
        extent=(0, 1, 0, 1),
        transform=ax.transAxes,
        aspect="auto",
        cmap=cmap,
        interpolation="bicubic",
        zorder=0,
        alpha=1.0,
    )


def _format_volume(value: float, _position: float) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.0f}K"
    return f"{value:.0f}"


def _tick_positions(total: int) -> list[int]:
    if total <= 1:
        return [0]
    target = min(total, 6)
    if target == 1:
        return [0]
    step = max((total - 1) / (target - 1), 1)
    positions = []
    for idx in range(target):
        value = round(idx * step)
        if value not in positions:
            positions.append(value)
    if positions[-1] != total - 1:
        positions[-1] = total - 1
    return positions


def render_chart(
    candles: list[Candle],
    signal_type: SignalType,
    direction: str,
    symbol: str,
    timeframe: str,
) -> io.BytesIO:
    accent = ACCENTS[signal_type]
    direction_color = DIR_COLORS.get(direction, accent)
    fig, (ax_price, ax_vol) = plt.subplots(
        2,
        1,
        figsize=(11, 7),
        gridspec_kw={"height_ratios": [3.6, 1.1], "hspace": 0.02},
    )
    fig.patch.set_facecolor(BG)
    for ax in (ax_price, ax_vol):
        ax.set_facecolor(PANEL)
        ax.set_axisbelow(True)
        ax.grid(
            axis="y",
            color=GRID,
            linestyle=(0, (2, 6)),
            linewidth=0.8,
            alpha=0.65,
        )
        ax.tick_params(colors=MUTED, labelsize=8, length=0)
        ax.spines["top"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_edgecolor(GRID)
        ax.spines["right"].set_edgecolor(GRID)
    _add_panel_gradient(ax_price, "#15283f", PANEL_ALT)
    _add_panel_gradient(ax_vol, "#112033", PANEL_ALT)

    prices = []
    last_idx = len(candles) - 1
    for idx, candle in enumerate(candles):
        color = UP if candle.is_bullish else DOWN
        prices.extend([candle.high, candle.low])
        ax_price.plot(
            [idx, idx],
            [candle.low, candle.high],
            color=color,
            linewidth=1.45 if idx == last_idx else 1.3,
            solid_capstyle="round",
            zorder=4,
        )
        body_low = min(candle.open, candle.close)
        body_high = max(candle.open, candle.close)
        body_height = body_high - body_low
        candle_span = max(candle.high - candle.low, 1e-9)
        height = max(body_height, candle_span * 0.06)
        edge = accent if idx == last_idx else color
        width = 2.0 if idx == last_idx else 1.05
        ax_price.add_patch(
            Rectangle(
                (idx - 0.34, body_low - (height - body_height if body_height else 0) / 2),
                0.68,
                height,
                facecolor=color,
                edgecolor=edge,
                linewidth=width,
                joinstyle="round",
                alpha=0.98,
                zorder=5,
            )
        )
        ax_vol.bar(
            idx,
            candle.volume,
            color=(accent if idx == last_idx else color),
            alpha=0.96 if idx == last_idx else 0.82,
            width=0.68,
            zorder=3,
        )

    price_range = max(prices) - min(prices) if prices else 0
    price_pad = price_range * 0.14 if price_range else max(candles[-1].close * 0.01, 1)
    floor = min(prices) - price_pad

    tick_positions = _tick_positions(len(candles))
    tick_labels = [candles[idx].opened_at.strftime("%H:%M") for idx in tick_positions]
    ax_vol.set_xticks(tick_positions, tick_labels)
    ax_price.tick_params(labelbottom=False)
    ax_price.set_xlim(-0.8, len(candles) - 0.2)
    ax_vol.set_xlim(-0.8, len(candles) - 0.2)
    ax_price.set_ylim(floor, max(prices) + price_pad)
    ax_price.yaxis.tick_right()
    ax_vol.yaxis.tick_right()
    ax_vol.yaxis.set_major_formatter(FuncFormatter(_format_volume))
    ax_price.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.2f}"))
    ax_vol.set_xlabel("Candle close time (UTC)", color=MUTED, fontsize=8, labelpad=10)
    ax_vol.set_ylabel("Volume", color=MUTED, fontsize=8, labelpad=10)
    ax_price.text(
        0.013,
        0.965,
        "PRICE",
        transform=ax_price.transAxes,
        color=MUTED,
        fontsize=8,
        fontweight="bold",
        ha="left",
        va="top",
    )
    ax_vol.text(
        0.013,
        0.94,
        "VOLUME",
        transform=ax_vol.transAxes,
        color=MUTED,
        fontsize=8,
        fontweight="bold",
        ha="left",
        va="top",
    )

    fig.text(
        0.065,
        0.955,
        symbol,
        color=TEXT,
        fontsize=18,
        fontweight="bold",
        ha="left",
    )
    fig.text(
        0.065,
        0.925,
        f" {SIGNAL_LABELS[signal_type]} ",
        color=TEXT,
        fontsize=10,
        ha="left",
        bbox={
            "boxstyle": "round,pad=0.28",
            "fc": accent,
            "ec": accent,
            "lw": 0.0,
        },
    )
    fig.text(
        0.245,
        0.925,
        f" {timeframe} ",
        color=MUTED,
        fontsize=10,
        ha="left",
        bbox={
            "boxstyle": "round,pad=0.28",
            "fc": PANEL_ALT,
            "ec": GRID,
            "lw": 0.8,
        },
    )
    fig.text(
        0.325,
        0.925,
        f" {direction} ",
        color=TEXT,
        fontsize=10,
        ha="left",
        bbox={
            "boxstyle": "round,pad=0.28",
            "fc": direction_color,
            "ec": direction_color,
            "lw": 0.0,
        },
    )
    fig.text(
        0.935,
        0.955,
        "SNIPER",
        color=accent,
        fontsize=12,
        fontweight="bold",
        ha="right",
    )
    fig.text(
        0.935,
        0.925,
        "spike setup",
        color=MUTED,
        fontsize=9,
        ha="right",
    )

    fig.add_artist(
        Line2D([0.065, 0.935], [0.905, 0.905], transform=fig.transFigure, color=GRID)
    )
    fig.subplots_adjust(top=0.88, bottom=0.12, left=0.06, right=0.94)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=125, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf

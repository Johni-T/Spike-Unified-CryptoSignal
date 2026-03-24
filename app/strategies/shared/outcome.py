from app.domain.enums import Direction, Outcome


def evaluate_outcome(
    direction: Direction, entry_price: float, exit_price: float
) -> tuple[Outcome, float, float]:
    if direction == Direction.CALL:
        pnl_abs = exit_price - entry_price
        outcome = Outcome.WIN if exit_price > entry_price else Outcome.LOSS
    else:
        pnl_abs = entry_price - exit_price
        outcome = Outcome.WIN if exit_price < entry_price else Outcome.LOSS
    pnl_pct = (pnl_abs / entry_price * 100) if entry_price else 0.0
    return outcome, pnl_abs, pnl_pct

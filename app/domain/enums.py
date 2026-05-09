from enum import StrEnum


class Direction(StrEnum):
    CALL = "CALL"
    PUT = "PUT"


class Outcome(StrEnum):
    WIN = "WIN"
    LOSS = "LOSS"


class SignalType(StrEnum):
    EARLY_REVERSAL = "early_reversal"
    CONFIRMED_SPIKE_REVERSAL = "confirmed_spike_reversal"
    CONFIRMED_SPIKE_CONTINUATION = "confirmed_spike_continuation"

# Unified Sniper Bot

Single-container Telegram signal bot with two strategy types:

- `early_reversal` - sends an early reversal signal immediately after a spike candle closes.
- `confirmed_reversal` - waits for a lower-volume confirmation candle before entering.
  Internally it now splits into:
  - `confirmed_spike_reversal` - same-color follow-through with weaker volume, entry against the spike.
  - `confirmed_spike_continuation` - opposite-color confirmation candle, entry in the spike direction.

`early_reversal` uses a mean volume baseline so fresh spikes temporarily raise the threshold and reduce follow-up noise.
`confirmed_reversal` uses a median volume baseline so one extreme candle does not break confirmation logic.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
python -m app.main
```

## Run in Docker

```bash
cp .env.example .env
docker compose up --build -d
```

## Telegram commands

- `/status`
- `/markets`
- `/stats`
- `/stats early`
- `/stats confirmed`
- `/stats confirmed_reversal`
- `/stats confirmed_continuation`
- `/signals`
- `/signals early`
- `/signals confirmed`
- `/signals confirmed_reversal`
- `/signals confirmed_continuation`

# Forex A+ Telegram Alert Bot

A Python Telegram bot that monitors:
EUR/USD, USD/JPY, NZD/CAD, GBP/JPY, GBP/USD, XAU/USD

Timeframes:
30M, 1H, 2H, 4H, 1D

Alert classes:
- MARKET UPDATE: trend, BOS/CHOCH, key levels, zones, breakouts
- WATCHLIST: developing setup
- A+ BUY/SELL: multi-condition setup with entry, SL, TP and R:R

## Important
This is an educational/automation framework, not financial advice. Price-action detection is algorithmic and will need backtesting and tuning against your broker/data feed before being used with real money.

## 1. Create a Telegram bot
In Telegram, open @BotFather, create a bot with /newbot, and copy the token.

## 2. Create an API key
This starter uses Twelve Data's REST API for OHLCV data. Create an API key and put it in `.env`.

## 3. Install
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Configure
Copy `.env.example` to `.env` and set:
TELEGRAM_BOT_TOKEN
TWELVE_DATA_API_KEY
TELEGRAM_CHAT_ID

Optional:
SCAN_SECONDS=300
MIN_SCORE=80
RISK_REWARD=3
RISK_PERCENT=1
ZONE_LOOKBACK=80

## 5. Run
```bash
python bot.py
```

The bot polls the configured symbols and sends alerts when new qualifying conditions are detected.

## Telegram commands
/start
/status
/pairs
/settings
/scan

## Strategy logic
The A+ engine uses a scoring model:
- HTF directional alignment
- market structure break / CHOCH
- fresh supply/demand zone
- displacement/impulse
- retest proximity
- key-level context
- minimum risk/reward
- spread/data sanity checks where available

It deliberately does NOT claim to predict markets. It identifies rule-based conditions from the supplied OHLC data.

## Production upgrades
For a production deployment, replace the REST polling layer with a broker/market-data websocket if available, persist state in PostgreSQL/Redis, add logging/monitoring, and backtest the exact rules before live use.

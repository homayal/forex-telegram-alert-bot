import asyncio
import logging
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import *
from market_data import TwelveData
from strategy import build_setup, market_snapshot, trend

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("forex-bot")

data = TwelveData(TWELVE_DATA_API_KEY)
last_alerts = set()

def fmt(p):
    # Compact adaptive decimal formatting.
    if p >= 1000: return f"{p:.2f}"
    if p >= 100: return f"{p:.3f}"
    return f"{p:.5f}"

def setup_message(s):
    return (
        f"🚨 <b>A+ {s.direction} SETUP</b>\n\n"
        f"📌 <b>{s.symbol}</b> | {s.timeframe}\n"
        f"⭐ Score: <b>{s.score}/100</b>\n\n"
        f"Entry: <b>{fmt(s.entry_low)} – {fmt(s.entry_high)}</b>\n"
        f"SL: <b>{fmt(s.sl)}</b>\n"
        f"TP1: <b>{fmt(s.tp1)}</b>\n"
        f"TP2: <b>{fmt(s.tp2)}</b>\n"
        f"R:R target: <b>1:{RISK_REWARD:g}</b>\n\n"
        f"🧠 <b>Reason</b>\n• " + "\n• ".join(s.reason) +
        "\n\n⚠️ Educational/algorithmic alert. Confirm conditions before trading."
    )

def snapshot_message(s):
    z = s["zones"][-1] if s["zones"] else None
    zone_text = "None detected"
    if z:
        zone_text = f"{z.kind}: {fmt(z.low)} – {fmt(z.high)}"
    return (
        f"📊 <b>MARKET UPDATE</b>\n\n"
        f"📌 <b>{s['symbol']}</b> | {s['timeframe']}\n"
        f"Price: <b>{fmt(s['price'])}</b>\n"
        f"Trend: <b>{s['trend']}</b>\n"
        f"Structure: <b>{s['structure']}</b>\n"
        f"Zone: <b>{zone_text}</b>\n"
        f"Key high: {fmt(s['levels']['recent_high'])}\n"
        f"Key low: {fmt(s['levels']['recent_low'])}"
    )

async def send(chat_id, text, app):
    await app.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")

async def scan_job(context: ContextTypes.DEFAULT_TYPE):
    if not TELEGRAM_CHAT_ID:
        log.warning("TELEGRAM_CHAT_ID is not configured")
        return

    app = context.application
    for symbol in SYMBOLS:
        try:
            # Use 4H as the default higher-timeframe directional filter.
            htf = data.candles(symbol, "4h", 220)
            htf_bias = trend(htf)

            for tf in TIMEFRAMES:
                try:
                    df = data.candles(symbol, tf, 220)
                    snap = market_snapshot(symbol, tf, df)

                    # Option B: market information only when a meaningful event exists.
                    event = snap["structure"]
                    if event != "NONE":
                        key = f"UPDATE|{symbol}|{tf}|{event}|{df['datetime'].iloc[-1]}"
                        if key not in last_alerts:
                            await send(TELEGRAM_CHAT_ID, snapshot_message(snap), app)
                            last_alerts.add(key)

                    # Option A: actionable A+ setup.
                    setup = build_setup(symbol, tf, df, htf_bias, MIN_SCORE, RISK_REWARD)
                    if setup:
                        key = f"SETUP|{symbol}|{tf}|{setup.direction}|{df['datetime'].iloc[-1]}"
                        if key not in last_alerts:
                            await send(TELEGRAM_CHAT_ID, setup_message(setup), app)
                            last_alerts.add(key)

                except Exception as e:
                    log.exception("TF scan failed for %s %s: %s", symbol, tf, e)

        except Exception as e:
            log.exception("Symbol scan failed for %s: %s", symbol, e)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 <b>Forex A+ Alert Bot</b>\n\n"
        "Monitoring 6 instruments across 30M–Daily.\n"
        "Use /status, /pairs, /settings or /scan.",
        parse_mode="HTML"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🟢 Bot online\n"
        f"Pairs: {len(SYMBOLS)}\n"
        f"Timeframes: {', '.join(TIMEFRAMES)}\n"
        f"Minimum A+ score: {MIN_SCORE}\n"
        f"Target R:R: 1:{RISK_REWARD:g}"
    )

async def pairs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📌 " + "\n".join(SYMBOLS))

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"⚙️ Settings\nMinimum score: {MIN_SCORE}\nRisk target: {RISK_PERCENT}%\n"
        f"R:R: 1:{RISK_REWARD:g}\nScan: every {SCAN_SECONDS}s"
    )

async def scan_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔎 Manual scan started...")
    await scan_job(context)
    await update.message.reply_text("✅ Scan complete.")

def main():
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN in .env")
    if not TWELVE_DATA_API_KEY:
        raise SystemExit("Missing TWELVE_DATA_API_KEY in .env")
    if not TELEGRAM_CHAT_ID:
        log.warning("TELEGRAM_CHAT_ID is empty; commands work, automatic alerts will not.")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("pairs", pairs))
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(CommandHandler("scan", scan_now))

    app.job_queue.run_repeating(scan_job, interval=SCAN_SECONDS, first=10)
    log.info("Starting bot")
    app.run_polling()

if __name__ == "__main__":
    main()

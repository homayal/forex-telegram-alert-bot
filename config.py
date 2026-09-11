import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

SCAN_SECONDS = int(os.getenv("SCAN_SECONDS", "300"))
MIN_SCORE = int(os.getenv("MIN_SCORE", "80"))
RISK_REWARD = float(os.getenv("RISK_REWARD", "3"))
RISK_PERCENT = float(os.getenv("RISK_PERCENT", "1"))
ZONE_LOOKBACK = int(os.getenv("ZONE_LOOKBACK", "80"))

SYMBOLS = ["EUR/USD", "USD/JPY", "NZD/CAD", "GBP/JPY", "GBP/USD", "XAU/USD"]
TIMEFRAMES = ["30min", "1h", "2h", "4h", "1day"]

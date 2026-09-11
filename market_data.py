import requests
import pandas as pd

class TwelveData:
    BASE = "https://api.twelvedata.com/time_series"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def candles(self, symbol: str, interval: str, outputsize: int = 250) -> pd.DataFrame:
        r = requests.get(self.BASE, params={
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize,
            "apikey": self.api_key,
            "format": "JSON",
            "timezone": "UTC",
        }, timeout=20)
        r.raise_for_status()
        data = r.json()
        if "values" not in data:
            raise RuntimeError(data.get("message", f"No data returned for {symbol} {interval}"))
        df = pd.DataFrame(data["values"])
        df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
        for c in ["open","high","low","close","volume"]:
            if c in df:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.sort_values("datetime").dropna(subset=["open","high","low","close"]).reset_index(drop=True)
        return df

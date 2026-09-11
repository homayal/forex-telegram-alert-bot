from dataclasses import dataclass
import numpy as np
import pandas as pd

@dataclass
class Zone:
    kind: str
    low: float
    high: float
    index: int
    strength: float

@dataclass
class Setup:
    symbol: str
    timeframe: str
    direction: str
    score: int
    entry_low: float
    entry_high: float
    sl: float
    tp1: float
    tp2: float
    reason: list[str]

def atr(df, n=14):
    prev = df["close"].shift(1)
    tr = pd.concat([
        df["high"]-df["low"],
        (df["high"]-prev).abs(),
        (df["low"]-prev).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def swings(df, left=2, right=2):
    highs, lows = [], []
    h = df["high"].values
    l = df["low"].values
    for i in range(left, len(df)-right):
        if h[i] == max(h[i-left:i+right+1]):
            highs.append(i)
        if l[i] == min(l[i-left:i+right+1]):
            lows.append(i)
    return highs, lows

def trend(df):
    hi, lo = swings(df)
    if len(hi) < 2 or len(lo) < 2:
        return "NEUTRAL"
    hh = df.loc[hi[-1],"high"] > df.loc[hi[-2],"high"]
    hl = df.loc[lo[-1],"low"] > df.loc[lo[-2],"low"]
    lh = df.loc[hi[-1],"high"] < df.loc[hi[-2],"high"]
    ll = df.loc[lo[-1],"low"] < df.loc[lo[-2],"low"]
    if hh and hl: return "BULLISH"
    if lh and ll: return "BEARISH"
    return "RANGE"

def structure_event(df):
    hi, lo = swings(df)
    if len(hi) < 2 and len(lo) < 2:
        return "NONE"
    close = df["close"].iloc[-1]
    last_h = df["high"].iloc[hi[-1]] if hi else np.nan
    last_l = df["low"].iloc[lo[-1]] if lo else np.nan
    # A close beyond a recent swing is treated as BOS.
    if not np.isnan(last_h) and close > last_h:
        return "BULLISH BOS"
    if not np.isnan(last_l) and close < last_l:
        return "BEARISH BOS"
    return "NONE"

def detect_zones(df, lookback=80):
    x = df.iloc[-lookback:].copy()
    a = atr(x).bfill()
    zones = []
    for i in range(2, len(x)-2):
        body = abs(x["close"].iloc[i] - x["open"].iloc[i])
        impulse = abs(x["close"].iloc[i+1] - x["open"].iloc[i+1])
        if body < a.iloc[i]*0.8 and impulse > a.iloc[i]*1.2:
            # Last small candle before displacement = candidate origin.
            if x["close"].iloc[i+1] > x["high"].iloc[i]:
                zones.append(Zone("DEMAND", x["low"].iloc[i], x["high"].iloc[i], i, float(impulse/a.iloc[i])))
            elif x["close"].iloc[i+1] < x["low"].iloc[i]:
                zones.append(Zone("SUPPLY", x["low"].iloc[i], x["high"].iloc[i], i, float(impulse/a.iloc[i])))
    return zones[-10:]

def key_levels(df):
    d = df.iloc[:-1]
    return {
        "previous_high": float(d["high"].iloc[-1]),
        "previous_low": float(d["low"].iloc[-1]),
        "recent_high": float(d["high"].tail(20).max()),
        "recent_low": float(d["low"].tail(20).min()),
    }

def build_setup(symbol, timeframe, df, htf_trend=None, min_score=80, rr=3):
    price = float(df["close"].iloc[-1])
    a = float(atr(df).iloc[-1])
    if not np.isfinite(a) or a <= 0:
        return None

    t = trend(df)
    event = structure_event(df)
    zones = detect_zones(df)
    nearest = None
    distance = 1e99
    for z in zones:
        d = 0 if z.low <= price <= z.high else min(abs(price-z.low), abs(price-z.high))
        if d < distance:
            nearest, distance = z, d

    if nearest is None:
        return None

    score = 0
    reasons = []
    direction = None

    if htf_trend == "BULLISH":
        score += 20; reasons.append("HTF bullish alignment")
    elif htf_trend == "BEARISH":
        score += 20; reasons.append("HTF bearish alignment")

    if t == "BULLISH":
        score += 15; reasons.append("local bullish trend")
    elif t == "BEARISH":
        score += 15; reasons.append("local bearish trend")

    if event == "BULLISH BOS":
        score += 20; reasons.append("bullish BOS")
    elif event == "BEARISH BOS":
        score += 20; reasons.append("bearish BOS")

    zone_distance_ok = distance <= a * 0.75
    if zone_distance_ok:
        score += 20; reasons.append(f"price near {nearest.kind.lower()} zone")

    if nearest.kind == "DEMAND" and (t == "BULLISH" or event == "BULLISH BOS") and htf_trend != "BEARISH":
        direction = "BUY"
    if nearest.kind == "SUPPLY" and (t == "BEARISH" or event == "BEARISH BOS") and htf_trend != "BULLISH":
        direction = "SELL"

    if direction is None:
        return None

    entry_low, entry_high = nearest.low, nearest.high
    buffer = a * 0.15
    if direction == "BUY":
        sl = nearest.low - buffer
        risk = max(price-sl, a*0.25)
        tp1 = price + risk*2
        tp2 = price + risk*rr
    else:
        sl = nearest.high + buffer
        risk = max(sl-price, a*0.25)
        tp1 = price - risk*2
        tp2 = price - risk*rr

    if risk <= 0:
        return None

    # Final quality gate.
    if score < min_score:
        return None

    return Setup(symbol, timeframe, direction, score, entry_low, entry_high, sl, tp1, tp2, reasons)

def market_snapshot(symbol, timeframe, df):
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "trend": trend(df),
        "structure": structure_event(df),
        "price": float(df["close"].iloc[-1]),
        "levels": key_levels(df),
        "zones": detect_zones(df),
    }

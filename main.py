import os
import yfinance as yf
import pandas as pd
import numpy as np
import yaml

# ============================================================
# OPTIONAL CONFIG LOADING (CLOUD SAFE)
# ============================================================
CONFIG_PATH = "config.yaml"

config = {}
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f) or {}
    except Exception:
        config = {}


# ============================================================
# INTERNAL HELPER — FORCE SCALAR
# ============================================================
def scalar(x):
    """
    Force pandas object to native Python scalar.
    Raises if not exactly one value.
    """
    if hasattr(x, "item"):
        return x.item()
    return float(x)


# ============================================================
# LIVE AI ANALYSIS
# ============================================================
def analyze_stock(symbol, period="6mo"):
    try:
        df = yf.download(symbol, period=period, interval="1d", progress=False)

        if df.empty:
            return None

        # ---- Flatten columns if needed (yfinance safety)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close = df["Close"].astype(float)

        df["MA20"] = close.rolling(20).mean()

        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()

        rs = avg_gain / avg_loss
        df["RSI"] = 100 - (100 / (1 + rs))

        # ---- Force scalars
        close_v = scalar(close.iloc[-1])
        ma20_v = scalar(df["MA20"].iloc[-1])
        rsi_v = scalar(df["RSI"].iloc[-1])

        if close_v > ma20_v and rsi_v > 55:
            regime = "Bullish"
        elif close_v < ma20_v and rsi_v < 45:
            regime = "Bearish"
        else:
            regime = "Sideways"

        confidence = min(abs(rsi_v - 50) * 2, 100)

        return {
            "Symbol": symbol,
            "AI_Market_Regime": regime,
            "AI_Confidence": round(confidence, 1),
            "RSI": round(rsi_v, 2),
            "Last_Traded_Price": round(close_v, 2),
            "Date": df.index[-1]
        }

    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None


# ============================================================
# BACKTEST ENGINE — SIGNAL VALIDATION
# ============================================================
def backtest_regime(symbol, lookahead_days=5):
    df = yf.download(symbol, period="2y", interval="1d", progress=False)

    if df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    close = df["Close"].astype(float)
    df["MA20"] = close.rolling(20).mean()

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    results = []

    for i in range(50, len(df) - lookahead_days):
        close_v = scalar(close.iloc[i])
        ma20_v = scalar(df["MA20"].iloc[i])
        rsi_v = scalar(df["RSI"].iloc[i])

        if close_v > ma20_v and rsi_v > 55:
            signal = "Bullish"
        elif close_v < ma20_v and rsi_v < 45:
            signal = "Bearish"
        else:
            signal = "Sideways"

        future_close = scalar(close.iloc[i + lookahead_days])
        future_return = (future_close - close_v) / close_v

        if future_return > 0.01:
            actual = "Bullish"
        elif future_return < -0.01:
            actual = "Bearish"
        else:
            actual = "Sideways"

        results.append({
            "Signal": signal,
            "Actual": actual,
            "Return_%": round(future_return * 100, 2)
        })

    return pd.DataFrame(results)


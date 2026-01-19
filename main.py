# main.py — Explainable AI Engine (Transparent Decisions)

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import os


NSE_CACHE_FILE = "nse_universe.csv"


# ============================================================
# AUTO LOAD NSE UNIVERSE (CACHED)
# ============================================================
def load_nse_universe():
    if os.path.exists(NSE_CACHE_FILE):
        return pd.read_csv(NSE_CACHE_FILE)

    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    df = pd.read_csv(url)
    df = df[["SYMBOL", "NAME OF COMPANY"]]
    df.columns = ["symbol", "name"]
    df["symbol"] = df["symbol"] + ".NS"

    df.to_csv(NSE_CACHE_FILE, index=False)
    return df


# ============================================================
# DATA FETCH
# ============================================================
def fetch_data(symbol, period="2y"):
    df = yf.download(symbol, period=period, progress=False)
    if df.empty:
        return None
    return df.dropna()


# ============================================================
# INDICATORS
# ============================================================
def compute_rsi(series, window=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


# ============================================================
# EXPLAINABLE ANALYSIS
# ============================================================
def analyze_stock(symbol):
    try:
        df = fetch_data(symbol)
        if df is None or len(df) < 60:
            return {"Error": "Insufficient data"}

        df["MA20"] = df["Close"].rolling(20).mean()
        df["RSI"] = compute_rsi(df["Close"])

        last = df.iloc[-1]
        close = float(last["Close"])
        ma20 = float(last["MA20"])
        rsi = float(last["RSI"])

        reasons = []

        # --- Regime logic ---
        if close > ma20 and rsi > 55:
            state = "Bullish"
            reasons.append("Price is above 20-day moving average")
            reasons.append("RSI is above 55, indicating momentum strength")
        elif close < ma20 and rsi < 45:
            state = "Bearish"
            reasons.append("Price is below 20-day moving average")
            reasons.append("RSI is below 45, indicating weakness")
        else:
            state = "Sideways"
            reasons.append("Price and RSI show mixed signals")

        # --- Confidence logic ---
        confidence = round(abs(rsi - 50) * 2, 1)
        if confidence >= 70:
            reasons.append("Strong deviation from neutral RSI (high confidence)")
        elif confidence >= 40:
            reasons.append("Moderate RSI conviction")
        else:
            reasons.append("RSI close to neutral (low confidence)")

        # --- Risk logic ---
        high_risk = confidence < 40
        if high_risk:
            reasons.append("Low confidence increases risk")

        explanation = " • ".join(reasons)

        return {
            "Stock": symbol,
            "Last_Price": round(close, 2),
            "RSI": round(rsi, 2),
            "State": state,
            "Confidence": confidence,
            "High_Risk": high_risk,
            "Explanation": explanation,
            "Last_Updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

    except Exception as e:
        return {"Error": str(e)}


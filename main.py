import yfinance as yf
import pandas as pd
import numpy as np

# ============================================================
# HELPERS
# ============================================================
def scalar(x):
    return float(x.iloc[0]) if hasattr(x, "iloc") else float(x)

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ============================================================
# CORE AI SIGNAL
# ============================================================
def ai_signal(price, ma20, rsi):
    if price > ma20 and rsi > 55:
        return "Bullish"
    elif price < ma20 and rsi < 45:
        return "Bearish"
    return "Sideways"

# ============================================================
# STOCK ANALYSIS
# ============================================================
def analyze_stock(symbol):
    df = yf.download(symbol, period="6mo", interval="1d", progress=False)
    if df.empty:
        return None

    df["MA20"] = df["Close"].rolling(20).mean()
    df["RSI"] = compute_rsi(df["Close"])

    last = df.iloc[-1]
    price = scalar(last["Close"])
    ma20 = scalar(last["MA20"])
    rsi = scalar(last["RSI"])

    signal = ai_signal(price, ma20, rsi)
    confidence = round(abs(rsi - 50) * 1.5, 1)

    return {
        "Symbol": symbol,
        "Price": round(price, 2),
        "RSI": round(rsi, 2),
        "State": signal,
        "Confidence": confidence
    }

# ============================================================
# OPTIONS SENTIMENT (READ-ONLY)
# ============================================================
def analyze_options_sentiment(symbol):
    try:
        t = yf.Ticker(symbol)
        if not t.options:
            return None

        chain = t.option_chain(t.options[0])
        call_oi = chain.calls["openInterest"].sum()
        put_oi = chain.puts["openInterest"].sum()

        if call_oi == 0:
            return None

        pcr = round(put_oi / call_oi, 2)

        sentiment = (
            "Bullish" if pcr < 0.7 else
            "Bearish" if pcr > 1.2 else
            "Neutral"
        )

        return {
            "PCR": pcr,
            "Options_Sentiment": sentiment
        }

    except Exception:
        return None

# ============================================================
# BACKTEST ENGINE
# ============================================================
def backtest_ai(symbol, lookahead=5):
    df = yf.download(symbol, period="1y", interval="1d", progress=False)
    if df.empty:
        return None

    df["MA20"] = df["Close"].rolling(20).mean()
    df["RSI"] = compute_rsi(df["Close"])

    wins = 0
    losses = 0
    returns = []

    for i in range(25, len(df) - lookahead):
        row = df.iloc[i]
        future = df.iloc[i + lookahead]

        price = scalar(row["Close"])
        ma20 = scalar(row["MA20"])
        rsi = scalar(row["RSI"])
        future_price = scalar(future["Close"])

        signal = ai_signal(price, ma20, rsi)
        pct_change = (future_price - price) / price * 100

        correct = False
        if signal == "Bullish" and pct_change > 0:
            correct = True
        elif signal == "Bearish" and pct_change < 0:
            correct = True
        elif signal == "Sideways" and abs(pct_change) < 1.5:
            correct = True

        if correct:
            wins += 1
            returns.append(pct_change)
        else:
            losses += 1

    total = wins + losses
    accuracy = round((wins / total) * 100, 1) if total else 0
    avg_return = round(np.mean(returns), 2) if returns else 0

    return {
        "Accuracy_%": accuracy,
        "Wins": wins,
        "Losses": losses,
        "Avg_Return_%": avg_return
    }


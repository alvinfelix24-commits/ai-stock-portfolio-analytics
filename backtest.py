import pandas as pd
import yaml

from src.main import fetch_data, detect_market_regime


# ============================================================
# LOAD CONFIG
# ============================================================
with open("config.yaml", "r") as f:
    CONFIG = yaml.safe_load(f)

PORTFOLIO = CONFIG["portfolio"]
RSI_WINDOW = CONFIG["indicators"]["rsi_window"]


# ============================================================
# RSI (HISTORICAL)
# ============================================================
def calculate_rsi(close, window):
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


# ============================================================
# BACKTEST ONE STOCK
# ============================================================
def backtest_stock(symbol):
    df = fetch_data(symbol)
    if df is None:
        return None

    close = df["Close"].squeeze()
    rsi = calculate_rsi(close, RSI_WINDOW)

    records = []

    # start after indicators are stable
    for i in range(60, len(close) - 21):
        price_now = close.iloc[i]

        future_5d = (close.iloc[i + 5] - price_now) / price_now * 100
        future_10d = (close.iloc[i + 10] - price_now) / price_now * 100
        future_20d = (close.iloc[i + 20] - price_now) / price_now * 100

        # IMPORTANT: only past data is used here
        regime, _ = detect_market_regime(
            close.iloc[:i],
            rsi.iloc[:i]
        )

        records.append({
            "Stock": symbol,
            "Regime": regime,
            "Return_5D": future_5d,
            "Return_10D": future_10d,
            "Return_20D": future_20d,
        })

    return pd.DataFrame(records)


# ============================================================
# RUN BACKTEST
# ============================================================
all_results = []

for stock in PORTFOLIO:
    print(f"🔍 Backtesting {stock} ...")
    res = backtest_stock(stock)
    if res is not None:
        all_results.append(res)

df = pd.concat(all_results, ignore_index=True)

summary = df.groupby("Regime")[["Return_5D", "Return_10D", "Return_20D"]].mean()

print("\n📊 BACKTEST SUMMARY (Average % Returns)")
print(summary.round(2))

# Save results
summary.to_csv("reports/ai_regime_backtest_summary.csv")
print("\n💾 Saved to reports/ai_regime_backtest_summary.csv")


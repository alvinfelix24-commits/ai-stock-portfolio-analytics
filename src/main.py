import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from datetime import datetime
import os

print("✅ Portfolio AI script started")

# ----------------------------
# PORTFOLIO
# ----------------------------
portfolio = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS"
]

period = "2y"
results = []

# ----------------------------
# FUNCTION: ANALYZE STOCK
# ----------------------------
def analyze_stock(symbol):
    data = yf.Ticker(symbol).history(period=period)

    if data.empty or len(data) < 60:
        return None

    # Indicators
    data["MA20"] = data["Close"].rolling(20).mean()

    delta = data["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss

    data["RSI"] = 100 - (100 / (1 + rs))
    data.dropna(inplace=True)

    # Label market state
    def label(row):
        if row["Close"] > row["MA20"] and row["RSI"] > 55:
            return "Bullish"
        elif row["Close"] < row["MA20"] and row["RSI"] < 45:
            return "Bearish"
        else:
            return "Sideways"

    data["State"] = data.apply(label, axis=1)

    # ML prep
    X = data[["Close", "MA20", "RSI"]]
    y = data["State"]

    X_train, _, y_train, _ = train_test_split(
        X, y, test_size=0.25, shuffle=False
    )

    model = RandomForestClassifier(n_estimators=150, random_state=42)
    model.fit(X_train, y_train)

    latest = X.iloc[-1:]
    prediction = model.predict(latest)[0]
    confidence = np.max(model.predict_proba(latest)) * 100

    close = latest["Close"].values[0]
    ma = latest["MA20"].values[0]
    rsi = latest["RSI"].values[0]

    high_risk = prediction == "Bearish" and (close < ma or rsi < 35)

    return {
        "Stock": symbol,
        "State": prediction,
        "Confidence": round(confidence, 1),
        "High_Risk": high_risk
    }

# ----------------------------
# RUN ANALYSIS
# ----------------------------
for stock in portfolio:
    print(f"🔍 Analyzing {stock}")
    res = analyze_stock(stock)
    if res:
        results.append(res)

df = pd.DataFrame(results)

print("\n📊 PORTFOLIO SUMMARY")
print(df)

# ----------------------------
# SAVE REPORTS
# ----------------------------
os.makedirs("reports", exist_ok=True)
date = datetime.now().strftime("%Y-%m-%d")

csv_path = f"reports/portfolio_report_{date}.csv"
json_path = f"reports/portfolio_report_{date}.json"

df.to_csv(csv_path, index=False)
df.to_json(json_path, orient="records", indent=2)

print("\n💾 Reports saved")
print(csv_path)
print(json_path)

# ----------------------------
# PORTFOLIO HEALTH SCORE
# ----------------------------
score = 0
max_score = len(df) * 30

for _, row in df.iterrows():
    if row["State"] == "Bullish":
        score += 20
    elif row["State"] == "Sideways":
        score += 10

    if row["Confidence"] >= 80:
        score += 10
    elif row["Confidence"] >= 60:
        score += 5

    if row["High_Risk"]:
        score -= 10

health = max(0, min(100, int((score / max_score) * 100)))

print("\n📊 PORTFOLIO HEALTH SCORE")
print("========================")
print(f"Score: {health} / 100")

if health >= 75:
    print("Strong portfolio health")
elif health >= 50:
    print("Moderate portfolio health")
else:
    print("Weak portfolio health")



import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
from datetime import datetime
import pytz

# --------------------------------------------------
# Streamlit Config
# --------------------------------------------------
st.set_page_config(page_title="AI Stock Portfolio (India)", layout="wide")

st.title("🇮🇳 AI Stock Portfolio — Portfolio Optimization")
st.caption("Educational Market Analytics | NSE | Risk-Adjusted Analysis")

# --------------------------------------------------
# Legal Disclaimer (MANDATORY)
# --------------------------------------------------
st.warning(
    """
    ⚠️ **DISCLAIMER (SEBI-COMPLIANT)**  
    This application is strictly for **educational and analytical purposes only**.  
    It does **not provide investment advice, recommendations, or portfolio management services**  
    as defined under SEBI (Investment Advisers) Regulations, 2013.  
    All results shown are **historical simulations**, not predictions.
    """
)

# --------------------------------------------------
# Time & Market Context (India)
# --------------------------------------------------
IST = pytz.timezone("Asia/Kolkata")

# --------------------------------------------------
# Helper Functions
# --------------------------------------------------
def normalize_ticker(ticker):
    ticker = ticker.strip().upper()
    return ticker if "." in ticker else ticker + ".NS"

def get_price_column(df):
    return df["Adj Close"] if "Adj Close" in df.columns else df["Close"]

@st.cache_data(ttl=3600)
def fetch_data(ticker):
    time.sleep(1)
    return yf.download(ticker, period="5y", progress=False)

def compute_returns(df):
    price = get_price_column(df).astype(float)
    returns = price.pct_change().dropna()
    return price, returns

def cagr(price_series):
    years = (price_series.index[-1] - price_series.index[0]).days / 365
    return (price_series.iloc[-1] / price_series.iloc[0]) ** (1 / years) - 1

def volatility(returns):
    return returns.std() * np.sqrt(252)

def sharpe_ratio(returns, risk_free_rate=0.05):
    excess = returns.mean() * 252 - risk_free_rate
    return excess / (returns.std() * np.sqrt(252))

def max_drawdown(price_series):
    rolling_max = price_series.cummax()
    drawdown = (price_series - rolling_max) / rolling_max
    return drawdown.min()

# --------------------------------------------------
# Sidebar
# --------------------------------------------------
st.sidebar.header("📥 NSE Portfolio Setup")

tickers_input = st.sidebar.text_input(
    "NSE Symbols (comma-separated)",
    value="RELIANCE,TCS,INFY"
)

total_capital = st.sidebar.number_input(
    "Total Paper Capital (₹)",
    min_value=50000,
    value=200000,
    step=50000
)

# --------------------------------------------------
# Main Execution
# --------------------------------------------------
if st.sidebar.button("📊 Run Portfolio Optimization"):

    tickers = [normalize_ticker(t) for t in tickers_input.split(",")]
    metrics = []
    price_data = {}

    st.subheader("📈 Risk Metrics (Per Stock)")

    for ticker in tickers:
        df = fetch_data(ticker)
        if df.empty:
            st.warning(f"No data for {ticker}")
            continue

        price, returns = compute_returns(df)
        price_data[ticker] = price

        metrics.append({
            "Stock": ticker.replace(".NS",""),
            "CAGR (%)": round(cagr(price) * 100, 2),
            "Volatility (%)": round(volatility(returns) * 100, 2),
            "Sharpe Ratio": round(sharpe_ratio(returns), 2),
            "Max Drawdown (%)": round(max_drawdown(price) * 100, 2)
        })

    metrics_df = pd.DataFrame(metrics)
    st.dataframe(metrics_df, use_container_width=True)

    # --------------------------------------------------
    # Allocation Simulation (Risk-Adjusted)
    # --------------------------------------------------
    st.subheader("📐 Allocation Simulation (Paper Only)")

    metrics_df["Score"] = (
        metrics_df["Sharpe Ratio"] /
        metrics_df["Volatility (%)"].abs()
    )

    metrics_df["Weight (%)"] = (
        metrics_df["Score"] / metrics_df["Score"].sum() * 100
    )

    metrics_df["Allocated Capital (₹)"] = (
        metrics_df["Weight (%)"] / 100 * total_capital
    ).round(0)

    allocation_df = metrics_df[
        ["Stock","Weight (%)","Allocated Capital (₹)"]
    ].round(2)

    st.dataframe(allocation_df, use_container_width=True)

    # --------------------------------------------------
    # Portfolio Equity Curve (Simulated)
    # --------------------------------------------------
    st.subheader("📉 Simulated Portfolio Equity Curve")

    aligned_prices = pd.concat(price_data.values(), axis=1)
    aligned_prices.columns = price_data.keys()
    aligned_prices = aligned_prices.dropna()

    weights = metrics_df.set_index("Stock")["Weight (%)"] / 100
    weights.index = [s + ".NS" for s in weights.index]

    portfolio_value = (aligned_prices * weights).sum(axis=1)
    portfolio_value = portfolio_value / portfolio_value.iloc[0] * total_capital

    fig, ax = plt.subplots()
    ax.plot(portfolio_value)
    ax.set_ylabel("Portfolio Value (₹)")
    ax.set_xlabel("Time")
    st.pyplot(fig)

    # --------------------------------------------------
    # Portfolio Risk Summary
    # --------------------------------------------------
    portfolio_returns = portfolio_value.pct_change().dropna()

    st.subheader("🧠 Portfolio Risk Summary")

    col1, col2, col3 = st.columns(3)
    col1.metric("Portfolio CAGR (%)", round(cagr(portfolio_value) * 100, 2))
    col2.metric("Portfolio Sharpe", round(sharpe_ratio(portfolio_returns), 2))
    col3.metric("Max Drawdown (%)", round(max_drawdown(portfolio_value) * 100, 2))

    st.success("✅ Portfolio optimization completed (educational simulation only)")

else:
    st.info("👈 Enter NSE stocks and run optimization")


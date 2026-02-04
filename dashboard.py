# ============================================================
# AI Stock Portfolio Analytics - Enhanced & Debugged
# ============================================================

import streamlit as st
import json
import os
from datetime import datetime
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import time
import pytz

# Your existing imports
try:
    from main import analyze_stock, analyze_options_sentiment, backtest_ai
    HAS_MAIN_FUNCTIONS = True
except ImportError:
    HAS_MAIN_FUNCTIONS = False

# ============================================================
# CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="AI Stock Portfolio Analytics - Enhanced",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

WATCHLIST_FILE = "watchlist.json"
DEFAULT_WATCHLIST = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
RISK_FREE_RATE = 0.065
TRADING_DAYS_PER_YEAR = 252
MIN_DATA_POINTS = 30
IST = pytz.timezone("Asia/Kolkata")

# ============================================================
# LEGAL DISCLAIMER
# ============================================================
with st.expander("⚠️ LEGAL DISCLAIMER (SEBI-COMPLIANT)", expanded=False):
    st.warning(
        """
        **EDUCATIONAL USE ONLY - NOT INVESTMENT ADVICE**
        
        This tool is NOT registered with SEBI and does NOT provide:
        - Investment advice or recommendations
        - Portfolio management services
        - Personalized financial guidance
        
        All analysis is educational and based on historical data only.
        Consult a SEBI-registered Investment Adviser before investing.
        Stock markets are subject to risk. You may lose capital.
        """
    )

# ============================================================
# WATCHLIST FUNCTIONS
# ============================================================
def load_watchlist():
    if not os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, "w") as f:
            json.dump(DEFAULT_WATCHLIST, f)
        return DEFAULT_WATCHLIST.copy()
    
    try:
        with open(WATCHLIST_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    
    return DEFAULT_WATCHLIST.copy()

def save_watchlist(watchlist):
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(sorted(set(watchlist)), f)

# ============================================================
# PORTFOLIO ANALYTICS FUNCTIONS
# ============================================================

@st.cache_data(ttl=3600)
def fetch_stock_data(ticker, period="5y"):
    try:
        time.sleep(0.3)
        data = yf.download(ticker, period=period, progress=False)
        if data.empty:
            return pd.DataFrame()
        return data
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            'sector': info.get('sector', 'Unknown'),
            'name': info.get('longName', ticker),
            'market_cap': info.get('marketCap', 0)
        }
    except:
        return {'sector': 'Unknown', 'name': ticker, 'market_cap': 0}

def get_price_column(df):
    return df["Adj Close"] if "Adj Close" in df.columns else df["Close"]

def compute_returns(df):
    price = get_price_column(df).astype(float)
    returns = price.pct_change().dropna()
    return price, returns

def cagr(price_series):
    if len(price_series) < 2:
        return 0
    years = (price_series.index[-1] - price_series.index[0]).days / 365.25
    if years <= 0:
        return 0
    return float((price_series.iloc[-1] / price_series.iloc[0]) ** (1 / years) - 1)

def volatility(returns):
    vol = returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    # Convert to scalar if it's a Series
    if isinstance(vol, pd.Series):
        vol = vol.iloc[0] if len(vol) > 0 else 0.0
    # Handle NaN
    if pd.isna(vol):
        return 0.0
    return float(vol)

def sharpe_ratio(returns, risk_free_rate=RISK_FREE_RATE):
    mean_return = returns.mean()
    std_return = returns.std()
    
    # Convert to scalars if Series
    if isinstance(mean_return, pd.Series):
        mean_return = mean_return.iloc[0] if len(mean_return) > 0 else 0.0
    if isinstance(std_return, pd.Series):
        std_return = std_return.iloc[0] if len(std_return) > 0 else 0.0
    
    # Check for NaN or zero
    if pd.isna(mean_return) or pd.isna(std_return) or std_return == 0:
        return 0.0
    
    excess = float(mean_return) * TRADING_DAYS_PER_YEAR - risk_free_rate
    vol = float(std_return) * np.sqrt(TRADING_DAYS_PER_YEAR)
    
    return float(excess / vol) if vol != 0 else 0.0

def sortino_ratio(returns, risk_free_rate=RISK_FREE_RATE):
    mean_return = returns.mean()
    downside_returns = returns[returns < 0]
    
    if len(downside_returns) == 0:
        return 0.0
    
    downside_std = downside_returns.std()
    
    # Convert to scalars if Series
    if isinstance(mean_return, pd.Series):
        mean_return = mean_return.iloc[0] if len(mean_return) > 0 else 0.0
    if isinstance(downside_std, pd.Series):
        downside_std = downside_std.iloc[0] if len(downside_std) > 0 else 0.0
    
    # Check for NaN or zero
    if pd.isna(mean_return) or pd.isna(downside_std) or downside_std == 0:
        return 0.0
    
    excess = float(mean_return) * TRADING_DAYS_PER_YEAR - risk_free_rate
    vol = float(downside_std) * np.sqrt(TRADING_DAYS_PER_YEAR)
    
    return float(excess / vol) if vol != 0 else 0.0

def max_drawdown(price_series):
    rolling_max = price_series.cummax()
    drawdown = (price_series - rolling_max) / rolling_max
    min_dd = drawdown.min()
    
    # Convert to scalar if Series
    if isinstance(min_dd, pd.Series):
        min_dd = min_dd.iloc[0] if len(min_dd) > 0 else 0.0
    
    # Check for NaN
    if pd.isna(min_dd):
        return 0.0
    
    return float(min_dd)

def calmar_ratio(price_series, returns):
    cagr_val = cagr(price_series)
    mdd = abs(max_drawdown(price_series))
    return float(cagr_val / mdd) if mdd != 0 else 0.0

# ============================================================
# MAIN HEADER
# ============================================================
st.title("🧠 AI Stock Portfolio Analytics — Enhanced")
st.caption("🇮🇳 Search, Screen, Analyze & Optimize | Educational Tool")

# ============================================================
# TABS
# ============================================================
tabs = st.tabs([
    "🔍 Search",
    "📌 Watchlist",
    "➕ Add Stock",
    "🔎 AI Screener",
    "🧠 Explanation",
    "📊 Portfolio"
])

# ============================================================
# TAB 1: SEARCH
# ============================================================
with tabs[0]:
    st.subheader("🔍 Stock Search & Analysis")
    
    watchlist = load_watchlist()
    symbol = st.selectbox("Search stock", watchlist, key="search_stock")
    
    if HAS_MAIN_FUNCTIONS:
        with st.spinner("Analyzing stock…"):
            try:
                result = analyze_stock(symbol)
            except Exception:
                st.error("⚠️ Market data temporarily unavailable.")
                st.stop()
        
        price = result.get("Price", "N/A")
        rsi = result.get("RSI", "N/A")
        state = result.get("State", "Unknown")
        explanation = result.get("Explanation", "")
        updated = result.get("Updated", datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M UTC"))
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Price", f"₹ {price}" if price != "N/A" else "N/A")
        col2.metric("RSI", rsi)
        col3.metric("State", state)
        
        st.subheader("🧠 AI Explanation")
        st.info(explanation)
        st.caption(f"Updated: {updated}")
    else:
        st.info("Using basic analysis mode")
        df = fetch_stock_data(symbol, period="1y")
        if not df.empty:
            price, returns = compute_returns(df)
            current_price = price.iloc[-1]
            
            col1, col2 = st.columns(2)
            col1.metric("Current Price", f"₹ {current_price:.2f}")
            col2.metric("1Y Return", f"{((price.iloc[-1]/price.iloc[0]-1)*100):.2f}%")

# ============================================================
# TAB 2: WATCHLIST
# ============================================================
with tabs[1]:
    st.subheader("📌 Your Watchlist")
    watchlist = load_watchlist()
    
    if not watchlist:
        st.info("Watchlist is empty.")
    else:
        for s in watchlist:
            st.markdown(f"🔹 **{s}**")
        st.metric("Total Stocks", len(watchlist))

# ============================================================
# TAB 3: ADD STOCK
# ============================================================
with tabs[2]:
    st.subheader("➕ Add New Stock")
    
    new_symbol = st.text_input("Enter Yahoo symbol (e.g. HDFCBANK.NS)")
    
    if st.button("Add to Watchlist"):
        if not new_symbol:
            st.warning("Please enter a symbol.")
        else:
            wl = load_watchlist()
            sym = new_symbol.upper().strip()
            
            if sym in wl:
                st.warning("Stock already in watchlist.")
            else:
                wl.append(sym)
                save_watchlist(wl)
                st.success(f"{sym} added successfully.")
                st.rerun()

# ============================================================
# TAB 4: AI SCREENER
# ============================================================
with tabs[3]:
    st.subheader("🔎 AI Stock Screener")
    
    if HAS_MAIN_FUNCTIONS:
        col1, col2 = st.columns(2)
        
        with col1:
            state_filter = st.multiselect(
                "Market State",
                ["Bullish", "Sideways", "Bearish"],
                default=["Bullish"]
            )
        
        with col2:
            rsi_min, rsi_max = st.slider("RSI Range", 0, 100, (40, 70))
        
        include_high_risk = st.checkbox("Include High Risk Stocks", value=False)
        
        if st.button("Run Screener"):
            watchlist = load_watchlist()
            results = []
            
            with st.spinner("Screening stocks…"):
                for sym in watchlist:
                    try:
                        res = analyze_stock(sym)
                    except Exception:
                        continue
                    
                    state = res.get("State")
                    rsi = res.get("RSI")
                    high_risk = res.get("High_Risk", False)
                    
                    if state not in state_filter:
                        continue
                    if not isinstance(rsi, (int, float)):
                        continue
                    if not (rsi_min <= rsi <= rsi_max):
                        continue
                    if high_risk and not include_high_risk:
                        continue
                    
                    results.append({
                        "Stock": sym,
                        "State": state,
                        "RSI": rsi,
                        "Price": res.get("Price", "N/A"),
                        "High Risk": "⚠️" if high_risk else "✅"
                    })
            
            if results:
                st.dataframe(pd.DataFrame(results), use_container_width=True)
            else:
                st.info("No stocks matched your criteria.")
    else:
        st.info("AI Screener requires main.py functions.")

# ============================================================
# TAB 5: EXPLANATION
# ============================================================
with tabs[4]:
    st.subheader("🧠 Why Did the AI Decide This?")
    
    watchlist = load_watchlist()
    symbol = st.selectbox("Choose stock", watchlist, key="explain")
    
    if HAS_MAIN_FUNCTIONS:
        with st.spinner("Generating explanation…"):
            try:
                result = analyze_stock(symbol)
            except Exception:
                st.error("⚠️ Unable to fetch explanation.")
                st.stop()
        
        st.success(f"Market Regime: **{result.get('State','Unknown')}**")
        st.write(result.get("Explanation",""))
        
        if result.get("High_Risk", False):
            st.error("⚠️ High risk detected")
        else:
            st.success("✅ Risk level acceptable")
    else:
        st.info("Explanation feature requires main.py functions.")

# ============================================================
# TAB 6: PORTFOLIO ANALYTICS
# ============================================================
with tabs[5]:
    st.subheader("📊 Portfolio Analytics & Optimization")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        period = st.selectbox("Period", ["1y", "2y", "3y", "5y"], index=2)
    
    with col2:
        capital = st.number_input("Capital (₹)", min_value=50000, value=500000, step=50000)
    
    with col3:
        method = st.selectbox("Strategy", ["Equal Weight", "Risk-Adjusted (Sharpe)", "Minimum Volatility"])
    
    if st.button("📊 Analyze Portfolio", type="primary"):
        watchlist = load_watchlist()
        
        if len(watchlist) < 2:
            st.warning("Add at least 2 stocks for portfolio analysis")
            st.stop()
        
        st.info("Fetching data...")
        progress = st.progress(0)
        
        metrics = []
        price_data = {}
        
        for i, ticker in enumerate(watchlist):
            df = fetch_stock_data(ticker, period=period)
            
            if df.empty or len(df) < 30:
                progress.progress((i + 1) / len(watchlist))
                continue
            
            info = fetch_stock_info(ticker)
            price, returns = compute_returns(df)
            price_data[ticker] = price
            
            metrics.append({
                "Stock": ticker.replace(".NS", ""),
                "Sector": info['sector'],
                "CAGR (%)": round(cagr(price) * 100, 2),
                "Volatility (%)": round(volatility(returns) * 100, 2),
                "Sharpe": round(sharpe_ratio(returns), 2),
                "Sortino": round(sortino_ratio(returns), 2),
                "Max DD (%)": round(max_drawdown(price) * 100, 2),
                "Price (₹)": round(price.iloc[-1], 2)
            })
            
            progress.progress((i + 1) / len(watchlist))
        
        progress.empty()
        
        if not metrics:
            st.error("No valid data found")
            st.stop()
        
        df_metrics = pd.DataFrame(metrics)
        
        st.markdown("---")
        st.subheader("📈 Stock Metrics")
        st.dataframe(df_metrics, use_container_width=True)
        
        # Download button
        csv = df_metrics.to_csv(index=False)
        st.download_button("📥 Download CSV", csv, "metrics.csv", "text/csv")
        
        # Sector Analysis
        st.markdown("---")
        st.subheader("🏢 Sector Distribution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            sector_counts = df_metrics['Sector'].value_counts()
            st.dataframe(sector_counts.to_frame('Count'))
        
        with col2:
            fig, ax = plt.subplots(figsize=(6, 6))
            ax.pie(sector_counts.values, labels=sector_counts.index, autopct='%1.1f%%')
            ax.set_title("Sector Breakdown")
            st.pyplot(fig)
            plt.close()
        
        # Allocation
        st.markdown("---")
        st.subheader("💼 Allocation Strategy")
        
        if method == "Equal Weight":
            df_metrics["Weight (%)"] = 100.0 / len(df_metrics)
        
        elif method == "Risk-Adjusted (Sharpe)":
            # Use clip for vectorized maximum operation
            sharpe_positive = df_metrics["Sharpe"].clip(lower=0)
            volatility_safe = df_metrics["Volatility (%)"].replace(0, 1)  # Avoid division by zero
            df_metrics["Score"] = sharpe_positive / volatility_safe
            
            total_score = df_metrics["Score"].sum()
            if total_score > 0:
                df_metrics["Weight (%)"] = (df_metrics["Score"] / total_score) * 100
            else:
                df_metrics["Weight (%)"] = 100.0 / len(df_metrics)
        
        elif method == "Minimum Volatility":
            volatility_safe = df_metrics["Volatility (%)"].replace(0, 1)
            df_metrics["Score"] = 1 / volatility_safe
            df_metrics["Weight (%)"] = (df_metrics["Score"] / df_metrics["Score"].sum()) * 100
        
        # Cap and normalize
        df_metrics["Weight (%)"] = df_metrics["Weight (%)"].clip(upper=40)
        df_metrics["Weight (%)"] = (df_metrics["Weight (%)"] / df_metrics["Weight (%)"].sum()) * 100
        
        # Ensure numeric types before calculations
        df_metrics["Weight (%)"] = pd.to_numeric(df_metrics["Weight (%)"], errors='coerce')
        df_metrics["Price (₹)"] = pd.to_numeric(df_metrics["Price (₹)"], errors='coerce')
        
        df_metrics["Capital (₹)"] = (df_metrics["Weight (%)"] / 100 * capital).round(0)
        df_metrics["Shares"] = (df_metrics["Capital (₹)"] / df_metrics["Price (₹)"]).round(0)
        
        st.dataframe(df_metrics[["Stock", "Sector", "Weight (%)", "Capital (₹)", "Shares"]], use_container_width=True)
        
        # Pie chart
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.pie(df_metrics["Weight (%)"], labels=df_metrics["Stock"], autopct='%1.1f%%')
        ax.set_title(f"Allocation - {method}")
        st.pyplot(fig)
        plt.close()
        
        # Portfolio Performance
        st.markdown("---")
        st.subheader("📈 Portfolio Value Over Time")
        
        aligned = pd.concat(price_data.values(), axis=1)
        aligned.columns = price_data.keys()
        aligned = aligned.dropna()
        
        weights_dict = dict(zip(df_metrics["Stock"] + ".NS", df_metrics["Weight (%)"] / 100))
        weights_series = pd.Series(weights_dict)
        
        portfolio = (aligned * weights_series).sum(axis=1)
        portfolio = portfolio / portfolio.iloc[0] * capital
        
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(portfolio, linewidth=2)
        ax.set_ylabel("Value (₹)")
        ax.set_title("Portfolio Performance")
        ax.grid(alpha=0.3)
        st.pyplot(fig)
        plt.close()
        
        # Metrics
        returns = portfolio.pct_change().dropna()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("CAGR", f"{(cagr(portfolio)*100):.2f}%")
        col2.metric("Sharpe", f"{sharpe_ratio(returns):.2f}")
        col3.metric("Max DD", f"{(max_drawdown(portfolio)*100):.2f}%")
        
        st.success("✅ Analysis complete!")
        st.caption(f"Updated: {datetime.now(IST).strftime('%Y-%m-%d %H:%M IST')}")

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption("🎓 Educational Tool | Not Financial Advice | Consult SEBI-registered advisers")


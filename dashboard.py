import sys
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd
import yaml
import matplotlib.pyplot as plt
import os
import requests

from main import analyze_stock, analyze_portfolio, fetch_data


# ============================================================
# PATHS
# ============================================================
STOCK_FILE = "data_all_stocks.csv"


# ============================================================
# LOAD CONFIG
# ============================================================
with open("config.yaml", "r") as f:
    CONFIG = yaml.safe_load(f)


# ============================================================
# LOAD / INIT STOCK UNIVERSE
# ============================================================
if not os.path.exists(STOCK_FILE):
    pd.DataFrame(columns=["Symbol", "Name", "Exchange"]).to_csv(STOCK_FILE, index=False)

ALL_STOCKS = pd.read_csv(STOCK_FILE)


# ============================================================
# YAHOO AUTOCOMPLETE
# ============================================================
@st.cache_data(ttl=3600)
def yahoo_autocomplete(query):
    url = "https://query1.finance.yahoo.com/v1/finance/search"
    r = requests.get(url, params={"q": query, "quotesCount": 10}, timeout=5)
    if r.status_code != 200:
        return []

    out = []
    for q in r.json().get("quotes", []):
        s = q.get("symbol", "")
        if s.endswith(".NS") or s.endswith(".BO"):
            out.append({
                "Symbol": s,
                "Name": q.get("shortname", ""),
                "Exchange": q.get("exchange", "")
            })
    return out


# ============================================================
# STREAMLIT SETUP
# ============================================================
st.set_page_config(page_title="AI Stock Analytics", layout="wide")
st.title("📈 AI Stock Analytics")
st.caption("Groww-style UX • AI Screener • Yahoo Finance (Delayed)")


# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Single Stock",
    "⚖️ Compare Stocks",
    "➕ Add Stock",
    "🧠 AI Screener"
])


# ============================================================
# TAB 3 — ADD STOCK (AUTOCOMPLETE)
# ============================================================
with tab3:
    st.subheader("➕ Add Stock (Yahoo Search)")
    q = st.text_input("Search company or symbol")

    if q:
        matches = yahoo_autocomplete(q)
        if not matches:
            st.info("No Yahoo-supported NSE/BSE symbols found.")
        for m in matches:
            col1, col2 = st.columns([4, 1])
            col1.write(f"**{m['Symbol']}** — {m['Name']}")
            if col2.button("Add", key=m["Symbol"]):
                if m["Symbol"] in ALL_STOCKS["Symbol"].values:
                    st.warning("Already exists.")
                else:
                    ALL_STOCKS = pd.concat(
                        [ALL_STOCKS, pd.DataFrame([m])],
                        ignore_index=True
                    )
                    ALL_STOCKS.to_csv(STOCK_FILE, index=False)
                    st.success(f"{m['Symbol']} added")
                    st.rerun()


# ============================================================
# TAB 1 — SINGLE STOCK
# ============================================================
with tab1:
    symbol = st.selectbox("Select Stock", ALL_STOCKS["Symbol"].tolist())
    res = analyze_stock(symbol)

    if res is None:
        st.warning("Yahoo data not available for this stock.")
        st.stop()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Price (₹)", res["Last_Traded_Price"])
    c2.metric("RSI", res["RSI"])
    c3.metric("Regime", res["AI_Market_Regime"])
    c4.metric("Confidence", res["AI_Confidence"])

    st.caption(f"Last update: {res['Last_Traded_Time']} (Delayed)")


# ============================================================
# TAB 2 — COMPARISON
# ============================================================
with tab2:
    st.subheader("⚖️ Compare")
    a = st.selectbox("Stock A", ALL_STOCKS["Symbol"].tolist(), key="a")
    b = st.selectbox("Stock B", ALL_STOCKS["Symbol"].tolist(), key="b")

    ra, rb = analyze_stock(a), analyze_stock(b)
    if ra is None or rb is None:
        st.warning("Insufficient Yahoo data.")
        st.stop()

    def show(col, r):
        col.metric("Price", r["Last_Traded_Price"])
        col.metric("RSI", r["RSI"])
        col.metric("Regime", r["AI_Market_Regime"])
        col.metric("Confidence", r["AI_Confidence"])

    c1, c2 = st.columns(2)
    show(c1, ra)
    show(c2, rb)


# ============================================================
# TAB 4 — AI SCREENER (NEW)
# ============================================================
with tab4:
    st.subheader("🧠 AI Screener")

    regime = st.multiselect(
        "Market Regime",
        ["Bullish", "Sideways", "Bearish"],
        default=["Bullish"]
    )

    rsi_min, rsi_max = st.slider(
        "RSI Range",
        0, 100, (30, 70)
    )

    min_conf = st.slider(
        "Minimum AI Confidence",
        0, 100, 50
    )

    exclude_high_risk = st.checkbox("Exclude High-Risk Stocks", value=True)

    if st.button("Run AI Screener"):
        results = []

        with st.spinner("Running AI across stocks..."):
            for s in ALL_STOCKS["Symbol"]:
                r = analyze_stock(s)
                if r is None:
                    continue

                if r["AI_Market_Regime"] not in regime:
                    continue
                if not (rsi_min <= r["RSI"] <= rsi_max):
                    continue
                if r["AI_Confidence"] < min_conf:
                    continue
                if exclude_high_risk and r["High_Risk"]:
                    continue

                results.append(r)

        if not results:
            st.warning("No stocks matched the AI criteria.")
        else:
            df = pd.DataFrame(results)
            st.success(f"{len(df)} stocks matched")
            st.dataframe(df, use_container_width=True)


# ============================================================
# PORTFOLIO AI
# ============================================================
st.divider()
st.subheader("🧩 AI Portfolio Brain")

p = analyze_portfolio()
risk = p["AI_Portfolio_Risk_Level"]

if risk == "HIGH":
    st.error(f"⚠️ Portfolio Risk: {risk}")
elif risk == "MEDIUM":
    st.warning(f"⚠️ Portfolio Risk: {risk}")
else:
    st.success(f"✅ Portfolio Risk: {risk}")

for i in p["AI_Portfolio_Insights"]:
    st.write("•", i)


import streamlit as st
import json
import os
from datetime import datetime

from main import analyze_stock

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="AI Stock Portfolio Analytics",
    page_icon="🧠",
    layout="wide"
)

# ============================================================
# WATCHLIST STORAGE (PERSISTENT)
# ============================================================
WATCHLIST_FILE = "watchlist.json"
DEFAULT_WATCHLIST = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]

def load_watchlist():
    if not os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, "w") as f:
            json.dump(DEFAULT_WATCHLIST, f)
        return DEFAULT_WATCHLIST.copy()
    with open(WATCHLIST_FILE, "r") as f:
        return json.load(f)

def save_watchlist(watchlist):
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(sorted(set(watchlist)), f)

# ============================================================
# HEADER
# ============================================================
st.title("🧠 Explainable AI — Market Decisions")
st.caption("Every AI decision explained in plain English")

tab_search, tab_watchlist, tab_add, tab_explain = st.tabs(
    ["🔍 Search", "📌 Watchlist", "➕ Add Stock", "🧠 Explanation"]
)

# ============================================================
# 🔍 SEARCH TAB
# ============================================================
with tab_search:
    watchlist = load_watchlist()
    symbol = st.selectbox("Search stock", watchlist)

    with st.spinner("Analyzing stock…"):
        try:
            result = analyze_stock(symbol)
        except Exception:
            st.error("⚠️ Market data temporarily unavailable (rate limited).")
            st.stop()

    # SAFE EXTRACTION (NO KeyErrors)
    price = result.get("Price", "N/A")
    rsi = result.get("RSI", "N/A")
    state = result.get("State", "Unknown")
    explanation = result.get("Explanation", "No explanation available.")
    updated = result.get("Updated", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))

    col1, col2, col3 = st.columns(3)
    col1.metric("Price", f"₹ {price}" if price != "N/A" else "N/A")
    col2.metric("RSI", rsi)
    col3.metric("State", state)

    st.subheader("🧠 AI Explanation")
    st.info(explanation)
    st.caption(f"Updated: {updated}")

# ============================================================
# 📌 WATCHLIST TAB
# ============================================================
with tab_watchlist:
    watchlist = load_watchlist()
    st.subheader("📌 Your Watchlist")

    if not watchlist:
        st.info("Watchlist is empty.")
    else:
        for s in watchlist:
            st.markdown(f"🔹 **{s}**")

# ============================================================
# ➕ ADD STOCK TAB
# ============================================================
with tab_add:
    st.subheader("➕ Add New Stock")

    new_symbol = st.text_input("Enter Yahoo Finance symbol (e.g. HDFCBANK.NS)")

    if st.button("Add to Watchlist"):
        if new_symbol:
            watchlist = load_watchlist()
            watchlist.append(new_symbol.upper())
            save_watchlist(watchlist)
            st.success(f"Added {new_symbol.upper()} to watchlist")
            st.experimental_rerun()
        else:
            st.warning("Please enter a valid symbol")

# ============================================================
# 🧠 EXPLANATION TAB
# ============================================================
with tab_explain:
    watchlist = load_watchlist()
    symbol = st.selectbox("Choose stock", watchlist)

    with st.spinner("Generating explanation…"):
        try:
            result = analyze_stock(symbol)
        except Exception:
            st.error("⚠️ Unable to fetch explanation right now.")
            st.stop()

    state = result.get("State", "Unknown")
    explanation = result.get("Explanation", "No explanation available.")
    risk = result.get("High_Risk", False)

    st.success(f"Market Regime: **{state}**")
    st.write("### Explanation")
    st.write(explanation)

    if risk:
        st.error("⚠️ High risk detected")
    else:
        st.success("✅ Risk level acceptable")


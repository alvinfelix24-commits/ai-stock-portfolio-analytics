import streamlit as st
import json
import os
from datetime import datetime

from main import analyze_stock  # uses your existing main.py logic

# ============================================================
# APP CONFIG
# ============================================================
st.set_page_config(
    page_title="AI Stock Portfolio Analytics",
    page_icon="🧠",
    layout="wide"
)

# ============================================================
# WATCHLIST STORAGE (Persistent)
# ============================================================
WATCHLIST_FILE = "watchlist.json"

DEFAULT_WATCHLIST = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS"
]


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

# ============================================================
# TABS
# ============================================================
tab_search, tab_watchlist, tab_add, tab_explain = st.tabs(
    ["🔍 Search", "📌 Watchlist", "➕ Add Stock", "🧠 Explanation"]
)

# ============================================================
# 🔍 SEARCH TAB
# ============================================================
with tab_search:
    watchlist = load_watchlist()

    symbol = st.selectbox(
        "Search stock",
        watchlist,
        index=0
    )

    with st.spinner("Analyzing stock..."):
        result = analyze_stock(symbol)

    col1, col2, col3 = st.columns(3)

    col1.metric("Price", f"₹ {result['Price']}")
    col2.metric("RSI", result["RSI"])
    col3.metric("State", result["State"])

    st.subheader("🧠 AI Explanation")
    st.info(result["Explanation"])

    st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ============================================================
# 📌 WATCHLIST TAB
# ============================================================
with tab_watchlist:
    st.subheader("📌 Your Watchlist")

    watchlist = load_watchlist()

    if not watchlist:
        st.info("No stocks in watchlist yet.")
    else:
        for sym in watchlist:
            st.write(f"🔹 {sym}")

# ============================================================
# ➕ ADD STOCK TAB  (PHASE J)
# ============================================================
with tab_add:
    st.subheader("➕ Add stock to watchlist")

    new_stock = st.text_input(
        "Enter Yahoo Finance symbol",
        placeholder="Example: HDFCBANK.NS"
    )

    if st.button("Add to Watchlist"):
        if not new_stock:
            st.warning("Please enter a symbol.")
        else:
            watchlist = load_watchlist()
            sym = new_stock.upper().strip()

            if sym in watchlist:
                st.warning("Stock already exists in watchlist.")
            else:
                watchlist.append(sym)
                save_watchlist(watchlist)
                st.success(f"{sym} added successfully!")
                st.rerun()

# ============================================================
# 🧠 EXPLANATION TAB
# ============================================================
with tab_explain:
    st.subheader("🧠 Why did the AI make this decision?")

    watchlist = load_watchlist()
    symbol = st.selectbox("Choose stock", watchlist)

    result = analyze_stock(symbol)

    st.success(f"Market Regime: {result['State']}")

    st.markdown("**Explanation:**")
    st.write(result["Explanation"])

    risk_msg = "⚠️ High Risk" if result["High_Risk"] else "✅ Risk level acceptable"
    st.info(risk_msg)


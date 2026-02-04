import streamlit as st
import json
import os
from datetime import datetime


from main import analyze_stock
from main import analyze_stock, analyze_options_sentiment, backtest_ai


# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="AI Stock Portfolio Analytics",
    page_icon="🧠",
    layout="wide"
)

# ============================================================
# WATCHLIST (SAFE + PERSISTENT)
# ============================================================
WATCHLIST_FILE = "watchlist.json"
DEFAULT_WATCHLIST = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]

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
# HEADER
# ============================================================
st.title("🧠 Explainable AI — Market Decisions")
st.caption("Search, screen, and understand stocks with AI")

tabs = st.tabs([
    "🔍 Search",
    "📌 Watchlist",
    "➕ Add Stock",
    "🔎 AI Screener",
    "🧠 Explanation"
])

# ============================================================
# 🔍 SEARCH TAB
# ============================================================
with tabs[0]:
    watchlist = load_watchlist()
    symbol = st.selectbox("Search stock", watchlist)

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
    updated = result.get(
        "Updated",
        datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    )

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
with tabs[1]:
    st.subheader("📌 Your Watchlist")
    watchlist = load_watchlist()

    if not watchlist:
        st.info("Watchlist is empty.")
    else:
        for s in watchlist:
            st.markdown(f"🔹 **{s}**")

# ============================================================
# ➕ ADD STOCK TAB
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
# 🔎 AI SCREENER TAB  (PHASE L)
# ============================================================
with tabs[3]:
    st.subheader("🔎 AI Stock Screener")
    st.markdown("Filter stocks based on AI signals")

    # --- Filters ---
    state_filter = st.multiselect(
        "Market State",
        ["Bullish", "Sideways", "Bearish"],
        default=["Bullish"]
    )

    rsi_min, rsi_max = st.slider(
        "RSI Range",
        0, 100, (40, 70)
    )

    include_high_risk = st.checkbox(
        "Include High Risk Stocks",
        value=False
    )

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
                    "High Risk": high_risk
                })

        if results:
            st.dataframe(results, width="stretch")
        else:
            st.info("No stocks matched your criteria.")

# ============================================================
# 🧠 EXPLANATION TAB
# ============================================================
with tabs[4]:
    st.subheader("🧠 Why did the AI decide this?")

    watchlist = load_watchlist()
    symbol = st.selectbox("Choose stock", watchlist)

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

try:
    result = analyze_stock(symbol)
except Exception as e:
    st.error("Data temporarily unavailable. Please retry later.")
    st.stop()


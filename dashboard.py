import os
import sys
import yaml
import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

# ------------------------------------------------------------
# ENSURE ROOT PATH (STREAMLIT CLOUD SAFE)
# ------------------------------------------------------------
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from main import analyze_stock

# ------------------------------------------------------------
# STREAMLIT PAGE SETUP
# ------------------------------------------------------------
st.set_page_config(
    page_title="AI Stock Portfolio Analytics",
    layout="wide"
)

st.title("📊 AI Stock Portfolio Analytics")
st.caption("Live price • RSI • Cloud-safe • NSE Ready")

# ------------------------------------------------------------
# SIDEBAR — STOCK INPUT
# ------------------------------------------------------------
st.sidebar.header("🔍 Stock Selection")

default_stocks = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS"
]

symbols_text = st.sidebar.text_area(
    "Enter stock symbols (comma-separated)",
    value=",".join(default_stocks),
    help="Example: RELIANCE.NS, TCS.NS"
)

symbols = [s.strip().upper() for s in symbols_text.split(",") if s.strip()]

run_btn = st.sidebar.button("▶ Run Analysis")

# ------------------------------------------------------------
# CACHED ANALYSIS (PER STOCK)
# ------------------------------------------------------------
@st.cache_data(ttl=300)  # cache for 5 minutes
def cached_analyze(symbol):
    return analyze_stock(symbol)

# ------------------------------------------------------------
# MAIN LOGIC
# ------------------------------------------------------------
if run_btn and symbols:
    st.subheader("📈 Stock Analysis")

    results = []

    for sym in symbols:
        with st.spinner(f"Analyzing {sym}..."):
            try:
                res = cached_analyze(sym)
                if res:
                    results.append(res)
                else:
                    st.warning(f"No data for {sym}")
            except Exception as e:
                st.error(f"{sym}: {e}")

    if results:
        df = pd.DataFrame(results)

        # ----------------------------------------------------
        # LIVE PRICE + TIME (DISPLAY)
        # ----------------------------------------------------
        ist = pytz.timezone("Asia/Kolkata")
        now_ist = datetime.now(ist).strftime("%d %b %Y • %I:%M %p IST")

        st.markdown(f"🕒 **Last Updated:** {now_ist}")

        st.dataframe(df, use_container_width=True)

        # ----------------------------------------------------
        # PORTFOLIO HEALTH SCORE
        # ----------------------------------------------------
        score = 0
        max_score = len(df) * 20

        for _, row in df.iterrows():
            if row.get("State") == "Bullish":
                score += 20
            elif row.get("State") == "Sideways":
                score += 10

        pct = int((score / max_score) * 100) if max_score else 0

        st.subheader("📊 Portfolio Health")
        st.progress(pct)

        if pct >= 70:
            st.success(f"Strong portfolio ({pct}%)")
        elif pct >= 40:
            st.warning(f"Moderate portfolio ({pct}%)")
        else:
            st.error(f"Weak portfolio ({pct}%)")

    else:
        st.warning("No valid stocks analyzed.")

else:
    st.info("👈 Enter stock symbols and click **Run Analysis**")


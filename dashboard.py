# dashboard.py — Explainable AI View

import streamlit as st
import json
import os
from main import analyze_stock, load_nse_universe

st.set_page_config(page_title="Explainable AI Stocks", layout="wide")

WATCHLIST_FILE = "watchlist.json"


def load_watchlist():
    if not os.path.exists(WATCHLIST_FILE):
        return []
    with open(WATCHLIST_FILE, "r") as f:
        return json.load(f).get("stocks", [])


@st.cache_data(show_spinner=False)
def load_universe():
    df = load_nse_universe()
    df["label"] = df["symbol"] + " — " + df["name"]
    return df


watchlist = load_watchlist()
universe = load_universe()

st.title("🧠 Explainable AI — Market Decisions")
st.caption("Every AI decision explained in plain English")

tabs = st.tabs(["🔍 Search", "📌 Watchlist", "🧠 Explanation"])


# ============================================================
# TAB 1 — SEARCH
# ============================================================
with tabs[0]:
    choice = st.selectbox("Search stock", universe["label"].tolist())
    symbol = choice.split(" — ")[0]

    res = analyze_stock(symbol)

    if res.get("Error"):
        st.error(res["Error"])
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Price", res["Last_Price"])
        col2.metric("RSI", res["RSI"])
        col3.metric("State", res["State"])

        st.markdown("### 🧠 AI Explanation")
        st.info(res["Explanation"])


# ============================================================
# TAB 2 — WATCHLIST
# ============================================================
with tabs[1]:
    st.subheader("📌 Watchlist")

    if not watchlist:
        st.info("No stocks added yet.")
    else:
        for s in watchlist:
            st.write(f"🔹 {s}")


# ============================================================
# TAB 3 — DEEP EXPLANATION
# ============================================================
with tabs[2]:
    st.subheader("🔍 Why did AI make this decision?")

    stock = st.selectbox("Choose stock", watchlist)

    if stock:
        res = analyze_stock(stock)
        if res.get("Error"):
            st.error(res["Error"])
        else:
            st.success(f"**Market Regime:** {res['State']}")
            st.write("**Explanation:**")
            st.write(res["Explanation"])

            if res["High_Risk"]:
                st.warning("⚠️ Risk is elevated due to weak conviction")
            else:
                st.success("✅ Risk level acceptable")

            st.caption(f"Updated: {res['Last_Updated']}")


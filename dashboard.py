import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from src.main import analyze_stock, backtest_regime


st.set_page_config(page_title="AI Stock Intelligence", layout="wide")
st.title("🧠 AI Stock Intelligence Platform")

tab1, tab2, tab3 = st.tabs(
    ["📊 Live AI", "🔍 Explainability", "📈 Backtest"]
)


# ============================================================
# TAB 1 — LIVE AI
# ============================================================
with tab1:
    symbol = st.text_input("Stock Symbol", "RELIANCE.NS")

    res = analyze_stock(symbol)

    if res:
        st.metric("Last Price", res["Last_Traded_Price"])
        st.metric("Market Regime", res["AI_Market_Regime"])
        st.metric("AI Confidence", res["AI_Confidence"])
        st.metric("RSI", res["RSI"])


# ============================================================
# TAB 3 — BACKTEST
# ============================================================
with tab3:
    st.subheader("📈 AI Regime Backtest (Signal Validation)")

    st.info(
        "This backtest evaluates **signal accuracy**, not trading returns.\n\n"
        "Forward window: 5 days"
    )

    bt = backtest_regime(symbol)

    if bt is None:
        st.warning("Backtest unavailable.")
        st.stop()

    accuracy = (bt["Signal"] == bt["Actual"]).mean() * 100

    st.metric("Signal Accuracy (%)", round(accuracy, 2))

    st.subheader("Confusion Matrix")
    cm = pd.crosstab(bt["Signal"], bt["Actual"])

    fig, ax = plt.subplots()
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(cm.columns)))
    ax.set_yticks(range(len(cm.index)))
    ax.set_xticklabels(cm.columns)
    ax.set_yticklabels(cm.index)

    for i in range(len(cm.index)):
        for j in range(len(cm.columns)):
            ax.text(j, i, cm.iloc[i, j], ha="center", va="center")

    ax.set_xlabel("Actual Outcome")
    ax.set_ylabel("AI Signal")
    st.pyplot(fig)

    st.caption("Diagonal dominance = better signal quality")


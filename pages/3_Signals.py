import streamlit as st
from streamlit_autorefresh import st_autorefresh
from utils.data_fetchers import get_nifty_spot, get_india_vix, get_option_chain, parse_option_chain
from utils.calculations import calculate_gex, generate_signals, bias_score

st.set_page_config(page_title="Signals", page_icon="🎯", layout="wide")
st_autorefresh(interval=45000, key="sig")

st.title("🎯 Signals & Confluence")
with st.expander("ℹ️ Help – Signals"):
    st.markdown("""
    These are **transparent rule-based notes**, not trade recommendations.
    Rules combine PCR, VIX, GEX regime, Max Pain proximity and walls.
    Always combine with your own price action, risk management and Zerodha execution.
    Expected win probability is not calculated – markets are probabilistic and past patterns do not guarantee future results.
    """)

spot = get_nifty_spot()
vix = get_india_vix()
raw = get_option_chain("NIFTY")
df, summary = parse_option_chain(raw) if raw else (pd.DataFrame(), {})

if not spot or not summary:
    st.warning("Insufficient data.")
    st.stop()

gex = calculate_gex(df, summary["underlying"]) if not df.empty else {"regime":"Unknown","gamma_flip":spot["last"],"call_wall":None,"put_wall":None}
bias = bias_score(summary.get("pcr_oi",1), vix["last"] if vix else 14, gex["regime"], spot["last"], summary.get("max_pain"))
st.metric("Bias Score", f"{bias['score']} – {bias['label']}")
st.write("Reasons:", ", ".join(bias["reasons"]) if bias["reasons"] else "—")

signals = generate_signals(spot["last"], vix["last"] if vix else 14, summary.get("pcr_oi",1),
                           summary.get("max_pain"), gex["regime"], gex["gamma_flip"],
                           gex.get("call_wall"), gex.get("put_wall"))
st.subheader("Current Confluence Notes")
for s in signals:
    st.markdown(f"- {s}")

st.markdown("---")
st.markdown("""
**Example interpretation (educational)**
- Positive GEX + near Put Wall + elevated PCR → mean-reversion long bias, consider defined-risk bullish structures
- Negative GEX + expanding range + low PCR → momentum bias, prefer directional with stops
Always size small and respect invalidation levels.
""")

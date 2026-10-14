import streamlit as st
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
from utils.data_fetchers import get_global_indices

st.set_page_config(page_title="Global & News", page_icon="🌍", layout="wide")
st_autorefresh(interval=60000, key="glob")

st.title("🌍 Global Indices & News Keywords")
with st.expander("ℹ️ Help"):
    st.markdown("Global cues help gauge overnight sentiment. Watch USDINR, crude and US markets for India impact. News section lists keywords to monitor on X / Moneycontrol / ET.")

globals_ = get_global_indices()
if globals_:
    cols = st.columns(4)
    items = list(globals_.items())
    for i, (k,v) in enumerate(items):
        cols[i%4].metric(k, f"{v['last']:,.2f}", f"{v['chg_pct']:+.2f}%")

st.subheader("Keywords to Watch")
st.markdown("""
- RBI / MPC / inflation / rate decision
- FII / DII flows
- USDINR, crude oil spikes
- Major results (Reliance, HDFC, TCS, Infosys)
- Geopolitics, Fed, US CPI, China data
- GIFT Nifty large gaps
""")
st.caption("Morning brief continues via separate Grok Automation at 7:30 AM IST.")

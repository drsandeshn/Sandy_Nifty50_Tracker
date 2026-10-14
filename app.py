"""
Sandy_Nifty50_Tracker - Clean Public Version
No personal data, no Telegram tokens stored.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

from utils.data_fetchers import (
    get_nifty_spot, get_india_vix, get_option_chain, parse_option_chain,
    get_expected_move, get_atm_straddle, get_global_indices, get_live_quotes
)
from utils.calculations import calculate_gex, calc_cpr, generate_signals, bias_score

st.set_page_config(page_title="Sandy_Nifty50_Tracker", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

# Auto refresh every 45s
count = st_autorefresh(interval=45 * 1000, key="main_refresh")

st.title("📈 Sandy_Nifty50_Tracker")
st.caption(f"Clean public market tracker • Auto-refresh 45s • {datetime.now().strftime('%H:%M:%S')} IST • Educational only")

with st.sidebar:
    st.header("Navigation")
    st.page_link("app.py", label="🏠 Overview", icon="🏠")
    st.page_link("pages/1_Option_Chain.py", label="📊 Option Chain", icon="📊")
    st.page_link("pages/2_GEX_Board.py", label="⚡ GEX Board", icon="⚡")
    st.page_link("pages/3_Signals.py", label="🎯 Signals", icon="🎯")
    st.page_link("pages/4_Positions.py", label="📋 My Positions", icon="📋")
    st.page_link("pages/5_Global_News.py", label="🌍 Global & News", icon="🌍")
    st.markdown("---")
    st.info("No personal data stored. You execute all trades on Zerodha.")
    st.caption("Not financial advice.")

# ========== DATA ==========
with st.spinner("Fetching data..."):
    spot = get_nifty_spot()
    vix = get_india_vix()
    raw = get_option_chain("NIFTY")
    df, summary = parse_option_chain(raw) if raw else (pd.DataFrame(), {})
    globals_ = get_global_indices()
    live = get_live_quotes()

# ========== OVERVIEW ==========
st.header("Overview")
with st.expander("ℹ️ Help – Overview", expanded=False):
    st.markdown("""
    **What you see here**
    - Nifty spot & change
    - India VIX regime (Calm <13, Normal 13-17, Elevated >17)
    - Expected move (1σ / 2σ) based on VIX – statistical range for the day/week
    - Bias score – simple confluence of PCR + GEX + Max Pain
    Use expected move to choose strikes and decide position size. Bias score is only a quick filter, not a signal to trade.
    """)

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    if spot:
        st.metric("Nifty 50", f"{spot['last']:,.1f}", f"{spot['change']:+.1f} ({spot['pct_change']:+.2f}%)")
    else:
        st.metric("Nifty 50", "—")
with c2:
    if vix:
        regime = "Calm" if vix["last"] < 13 else ("Normal" if vix["last"] < 17 else "Elevated")
        st.metric("India VIX", f"{vix['last']:.2f}", f"{vix['pct_change']:+.2f}%")
        st.caption(f"Regime: **{regime}**")
    else:
        st.metric("India VIX", "—")
with c3:
    st.metric("PCR (OI)", f"{summary.get('pcr_oi', 0):.3f}" if summary else "—")
with c4:
    st.metric("Max Pain", f"{summary.get('max_pain', 0):,.0f}" if summary else "—")
with c5:
    st.metric("Call / Put Wall", f"{summary.get('call_wall', 0):.0f} / {summary.get('put_wall', 0):.0f}" if summary else "—")

if spot and vix:
    em1 = get_expected_move(spot["last"], vix["last"], 1)
    em7 = get_expected_move(spot["last"], vix["last"], 7)
    st.subheader("Expected Move (VIX-based)")
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("1σ Daily", f"±{em1['1sigma']:.0f}")
    e2.metric("1σ Range", f"{em1['lower_1s']:.0f} – {em1['upper_1s']:.0f}")
    e3.metric("1σ Weekly", f"±{em7['1sigma']:.0f}")
    e4.metric("2σ Daily", f"±{em1['2sigma']:.0f}")

# GEX + Bias
if not df.empty and summary and spot:
    gex = calculate_gex(df, summary["underlying"])
    bias = bias_score(summary.get("pcr_oi", 1), vix["last"] if vix else 14, gex["regime"],
                      spot["last"], summary.get("max_pain"))
    st.subheader("GEX Snapshot & Bias")
    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Net GEX (Cr)", gex["net_gex"])
    g2.metric("Regime", gex["regime"].split("(")[0].strip())
    g3.metric("Gamma Flip", f"{gex['gamma_flip']:,.0f}")
    g4.metric("Bias Score", f"{bias['score']} ({bias['label']})")
    st.caption("Reasons: " + ", ".join(bias["reasons"]) if bias["reasons"] else "")

    signals = generate_signals(spot["last"], vix["last"] if vix else 14, summary.get("pcr_oi",1),
                               summary.get("max_pain"), gex["regime"], gex["gamma_flip"],
                               gex.get("call_wall"), gex.get("put_wall"))
    st.markdown("**Quick Confluence**")
    for s in signals[:5]:
        st.write(s)

# Live quotes + globals compact
if live:
    st.subheader("Live Quotes")
    cols = st.columns(4)
    for i, k in enumerate(["NIFTY", "BANKNIFTY", "VIX", "SENSEX"]):
        if k in live:
            cols[i].metric(k, f"{live[k]['last']:,.1f}", f"{live[k]['chg_pct']:+.2f}%")

if globals_:
    st.subheader("Global Cues")
    cols = st.columns(6)
    for i, k in enumerate(["S&P 500", "Nasdaq", "US VIX", "Hang Seng", "USDINR", "Crude"]):
        if k in globals_ and i < 6:
            cols[i].metric(k, f"{globals_[k]['last']:,.1f}", f"{globals_[k]['chg_pct']:+.2f}%")

# CPR
if spot:
    cpr = calc_cpr(spot.get("high", spot["last"]), spot.get("low", spot["last"]), spot["last"])
    st.subheader("CPR Pivots (approx)")
    p1, p2, p3 = st.columns(3)
    p1.metric("Pivot", f"{cpr['pivot']}")
    p2.metric("BC / TC", f"{cpr['bc']} / {cpr['tc']}")
    p3.metric("S1 / R1", f"{cpr['s1']} / {cpr['r1']}")

st.markdown("---")
st.caption(f"Refresh #{count} • Public educational tool • Data from Yahoo + NSE public endpoints • Not financial advice")

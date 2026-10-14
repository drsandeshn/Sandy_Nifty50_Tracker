import streamlit as st
from datetime import datetime

st.set_page_config(page_title="My Positions", page_icon="📋", layout="wide")
st.title("📋 My Positions (Session Only)")
with st.expander("ℹ️ Help – Positions"):
    st.markdown("""
    This page is **session-only**. Positions are lost when you close the browser tab.
    No data is saved on any server. Enter trades you already took on Zerodha for quick P&L tracking.
    """)

if "positions" not in st.session_state:
    st.session_state.positions = []

with st.form("add"):
    c1,c2,c3,c4 = st.columns(4)
    sym = c1.text_input("Symbol (e.g. NIFTY25OCT24500CE)")
    side = c2.selectbox("Side", ["BUY","SELL"])
    qty = c3.number_input("Qty (lots)", 1, 100, 1)
    avg = c4.number_input("Avg Price", 0.0, 100000.0, 0.0, 0.5)
    ltp = st.number_input("Current LTP", 0.0, 100000.0, 0.0, 0.5)
    if st.form_submit_button("Add"):
        if sym and avg > 0:
            pnl = (ltp - avg) * qty * 25 if side=="BUY" else (avg - ltp) * qty * 25
            st.session_state.positions.append({"symbol":sym,"side":side,"qty":qty,"avg":avg,"ltp":ltp,"pnl":pnl,"time":datetime.now().strftime("%H:%M")})
            st.success("Added (session only)")

if st.session_state.positions:
    total = sum(p["pnl"] for p in st.session_state.positions)
    st.metric("Total Approx P&L (₹)", f"{total:,.0f}")
    for i,p in enumerate(st.session_state.positions):
        st.write(f"{p['side']} {p['symbol']} ×{p['qty']} @ {p['avg']} → LTP {p['ltp']} | P&L ₹{p['pnl']:,.0f}")
else:
    st.info("No positions in this session.")

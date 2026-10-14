import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from utils.data_fetchers import get_option_chain, parse_option_chain, get_atm_straddle
from utils.calculations import calculate_gex

st.set_page_config(page_title="Option Chain", page_icon="📊", layout="wide")
st_autorefresh(interval=45000, key="oc")

st.title("📊 Option Chain & Positioning")
with st.expander("ℹ️ Help – Option Chain"):
    st.markdown("""
    - **OI** = Open Interest (outstanding contracts)
    - **ΔOI** = Change in OI today (positive = new positions)
    - **PCR** > 1.2 often seen as bullish (more puts written), < 0.8 bearish
    - **Max Pain** = strike where option writers lose least – price often gravitates here near expiry
    - **Call/Put walls** = highest OI strikes – act as resistance/support
    Use with GEX and price structure. Not a standalone signal.
    """)

raw = get_option_chain("NIFTY")
df, summary = parse_option_chain(raw) if raw else (pd.DataFrame(), {})

if df.empty:
    st.warning("Option chain unavailable right now (NSE may block some networks or market closed). Try again later.")
    st.stop()

st.success(f"Underlying **{summary.get('underlying',0):,.1f}** | Expiry: {summary.get('nearest_expiry')} | PCR OI: **{summary.get('pcr_oi')}** | Max Pain: **{summary.get('max_pain'):,.0f}**")

mid = summary.get("atm", 0)
plot_df = df[(df["strike"] >= mid-500) & (df["strike"] <= mid+500)]
fig = go.Figure()
fig.add_trace(go.Bar(x=plot_df["strike"], y=plot_df["ce_oi"], name="Call OI", marker_color="#ef5350"))
fig.add_trace(go.Bar(x=plot_df["strike"], y=plot_df["pe_oi"], name="Put OI", marker_color="#26a69a"))
fig.update_layout(barmode="group", title="Open Interest by Strike", height=360, margin=dict(l=10,r=10,t=40,b=10))
st.plotly_chart(fig, use_container_width=True)

st.subheader("Chain Table (ATM ± 300)")
view = df[(df["strike"] >= mid-300) & (df["strike"] <= mid+300)].sort_values("strike")
st.dataframe(view[["strike","ce_oi","ce_chgoi","ce_volume","ce_ltp","ce_iv","pe_ltp","pe_iv","pe_volume","pe_chgoi","pe_oi"]],
             use_container_width=True, height=400)

straddle = get_atm_straddle(df, mid)
if straddle:
    st.info(f"ATM Straddle ({straddle['atm_strike']:.0f}): {straddle['ce_ltp']:.1f} + {straddle['pe_ltp']:.1f} = **{straddle['straddle']:.1f}** pts")

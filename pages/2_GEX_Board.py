import streamlit as st
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from utils.data_fetchers import get_option_chain, parse_option_chain
from utils.calculations import calculate_gex

st.set_page_config(page_title="GEX Board", page_icon="⚡", layout="wide")
st_autorefresh(interval=45000, key="gex")

st.title("⚡ GEX Board")
with st.expander("ℹ️ Help – GEX"):
    st.markdown("""
    **Gamma Exposure (GEX)** estimates how much dealer hedging may amplify or dampen moves.
    - **Positive GEX** → dealers long gamma → they sell into strength / buy dips → pinning / mean-reversion
    - **Negative GEX** → dealers short gamma → they buy strength / sell weakness → trend amplification
    - **Gamma Flip** → level where regime can change
    - **Call/Put walls** → large OI concentrations
    This is an approximation using public OI + IV. Research only.
    """)

raw = get_option_chain("NIFTY")
df, summary = parse_option_chain(raw) if raw else (pd.DataFrame(), {})
if df.empty or not summary:
    st.warning("Chain data unavailable.")
    st.stop()

gex = calculate_gex(df, summary["underlying"])
c1,c2,c3,c4 = st.columns(4)
c1.metric("Net GEX (Cr)", gex["net_gex"])
c2.metric("Regime", gex["regime"])
c3.metric("Gamma Flip", f"{gex['gamma_flip']:,.0f}")
c4.metric("Call / Put Wall", f"{gex.get('call_wall',0):.0f} / {gex.get('put_wall',0):.0f}")

if "df" in gex and not gex["df"].empty:
    gdf = gex["df"]
    mid = summary["underlying"]
    plot = gdf[(gdf["strike"] >= mid-600) & (gdf["strike"] <= mid+600)]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=plot["strike"], y=plot["call_gex"]/1e7, name="Call GEX", marker_color="#ef5350"))
    fig.add_trace(go.Bar(x=plot["strike"], y=plot["put_gex"]/1e7, name="Put GEX", marker_color="#26a69a"))
    fig.update_layout(barmode="relative", title="Strike-wise GEX (Cr)", height=380)
    st.plotly_chart(fig, use_container_width=True)

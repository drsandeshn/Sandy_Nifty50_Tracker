"""
Calculations for Sandy_Nifty50_Tracker
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List

def approx_gamma(S, K, T, sigma):
    """Simple approximation when full BS not critical."""
    if T <= 0 or sigma <= 0 or S <= 0:
        return 0.0
    try:
        from scipy.stats import norm
        d1 = (np.log(S/K) + (0.5*sigma**2)*T) / (sigma * np.sqrt(T))
        return float(norm.pdf(d1) / (S * sigma * np.sqrt(T)))
    except Exception:
        # fallback rough
        return max(0, 0.4 / (S * sigma * np.sqrt(max(T, 1/365))))

def calculate_gex(df: pd.DataFrame, spot: float, days_to_exp: float = 5.0) -> Dict[str, Any]:
    if df.empty or spot <= 0:
        return {"net_gex": 0, "regime": "Unknown", "gamma_flip": spot, "call_wall": None, "put_wall": None}
    T = max(days_to_exp / 365, 1/365)
    df = df.copy()
    df["ce_sig"] = df["ce_iv"].apply(lambda x: max(float(x)/100, 0.08) if pd.notna(x) and x > 0 else 0.14)
    df["pe_sig"] = df["pe_iv"].apply(lambda x: max(float(x)/100, 0.08) if pd.notna(x) and x > 0 else 0.14)
    lot = 25
    mult = lot * (spot ** 2) * 0.01
    df["call_gex"] = df.apply(lambda r: approx_gamma(spot, r["strike"], T, r["ce_sig"]) * r["ce_oi"] * mult, axis=1)
    df["put_gex"] = df.apply(lambda r: -approx_gamma(spot, r["strike"], T, r["pe_sig"]) * r["pe_oi"] * mult, axis=1)
    df["net"] = df["call_gex"] + df["put_gex"]
    net = df["net"].sum()
    call_wall = float(df.loc[df["call_gex"].idxmax(), "strike"]) if not df.empty else None
    put_wall = float(df.loc[df["put_gex"].idxmin(), "strike"]) if not df.empty else None
    df_s = df.sort_values("strike")
    df_s["cum"] = df_s["net"].cumsum()
    flip = float(df_s.loc[df_s["cum"].abs().idxmin(), "strike"])
    if net > 5e8:
        regime = "Strong Positive Gamma (Pinning)"
    elif net > 0:
        regime = "Positive Gamma"
    elif net > -5e8:
        regime = "Neutral / Flip Zone"
    else:
        regime = "Negative Gamma (Trending)"
    return {
        "net_gex": round(net / 1e7, 2),
        "regime": regime,
        "gamma_flip": flip,
        "call_wall": call_wall,
        "put_wall": put_wall,
        "df": df_s
    }

def calc_cpr(high, low, close):
    p = (high + low + close) / 3
    bc = (high + low) / 2
    tc = (p - bc) + p
    return {"pivot": round(p,1), "bc": round(bc,1), "tc": round(tc,1),
            "r1": round(2*p - low,1), "s1": round(2*p - high,1)}

def generate_signals(spot, vix, pcr, max_pain, gex_regime, gamma_flip, call_wall, put_wall) -> List[str]:
    sigs = []
    if pcr > 1.25:
        sigs.append("🟢 Elevated PCR → Contrarian bullish lean (heavy put writing)")
    elif pcr < 0.75:
        sigs.append("🔴 Low PCR → Contrarian bearish lean (heavy call writing)")
    if vix > 18:
        sigs.append("⚠️ High VIX → Prefer defined-risk structures")
    elif vix < 12:
        sigs.append("💤 Low VIX → Premium selling environment; watch for expansion")
    if max_pain and abs(spot - max_pain) < 40:
        sigs.append(f"📌 Near Max Pain ({max_pain:.0f}) → Pinning risk")
    if "Positive Gamma" in gex_regime:
        sigs.append("🧲 Positive GEX → Mean-reversion / pinning bias")
    elif "Negative Gamma" in gex_regime:
        sigs.append("🚀 Negative GEX → Trend / expansion bias")
    if put_wall and abs(spot - put_wall) < 40:
        sigs.append(f"🛡️ Near Put Wall ({put_wall:.0f}) → Support zone")
    if call_wall and abs(spot - call_wall) < 40:
        sigs.append(f"🧱 Near Call Wall ({call_wall:.0f}) → Resistance zone")
    if not sigs:
        sigs.append("➡️ Neutral confluence — wait for clearer setup")
    return sigs

def bias_score(pcr, vix, gex_regime, spot, max_pain) -> Dict:
    score = 0
    reasons = []
    if pcr > 1.2:
        score += 1
        reasons.append("PCR supportive")
    elif pcr < 0.8:
        score -= 1
        reasons.append("PCR resistive")
    if "Positive" in gex_regime:
        score += 1
        reasons.append("Positive GEX")
    elif "Negative" in gex_regime:
        score -= 1
        reasons.append("Negative GEX")
    if max_pain and spot < max_pain - 30:
        score += 0.5
    elif max_pain and spot > max_pain + 30:
        score -= 0.5
    if vix > 20:
        reasons.append("High vol – caution")
    label = "Bullish lean" if score >= 1.5 else ("Bearish lean" if score <= -1.5 else "Neutral")
    return {"score": round(score,1), "label": label, "reasons": reasons}

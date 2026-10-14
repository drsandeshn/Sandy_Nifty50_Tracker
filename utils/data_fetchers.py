"""
Data fetchers for Sandy_Nifty50_Tracker (clean public version)
"""
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import time
import warnings
warnings.filterwarnings("ignore")

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/option-chain",
})

def _warm():
    try:
        SESSION.get("https://www.nseindia.com", timeout=6)
        time.sleep(0.3)
    except Exception:
        pass

def get_nifty_spot() -> Optional[Dict[str, Any]]:
    try:
        t = yf.Ticker("^NSEI")
        hist = t.history(period="5d", interval="1m")
        if hist.empty:
            hist = t.history(period="5d")
        if hist.empty:
            return None
        last = float(hist["Close"].iloc[-1])
        prev_close = float(hist["Close"].iloc[0]) if len(hist) > 1 else last
        return {
            "last": last,
            "change": last - prev_close,
            "pct_change": (last / prev_close - 1) * 100 if prev_close else 0,
            "open": float(hist["Open"].iloc[0]),
            "high": float(hist["High"].max()),
            "low": float(hist["Low"].min()),
            "source": "Yahoo",
            "timestamp": datetime.now().isoformat()
        }
    except Exception:
        return None

def get_india_vix() -> Optional[Dict[str, Any]]:
    try:
        t = yf.Ticker("^INDIAVIX")
        hist = t.history(period="5d")
        if hist.empty:
            return None
        last = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else last
        return {
            "last": last,
            "change": last - prev,
            "pct_change": (last / prev - 1) * 100 if prev else 0,
            "source": "Yahoo"
        }
    except Exception:
        return None

def get_option_chain(symbol: str = "NIFTY") -> Optional[Dict]:
    _warm()
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    try:
        r = SESSION.get(url, timeout=12)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def parse_option_chain(raw: Optional[Dict]) -> Tuple[pd.DataFrame, Dict]:
    if not raw or "records" not in raw:
        return pd.DataFrame(), {}
    data = raw["records"]
    underlying = float(data.get("underlyingValue", 0))
    expiry_dates = data.get("expiryDates", [])
    rows = []
    for item in data.get("data", []):
        strike = item.get("strikePrice")
        ce = item.get("CE", {})
        pe = item.get("PE", {})
        rows.append({
            "strike": strike,
            "ce_oi": ce.get("openInterest", 0) or 0,
            "ce_chgoi": ce.get("changeinOpenInterest", 0) or 0,
            "ce_volume": ce.get("totalTradedVolume", 0) or 0,
            "ce_ltp": ce.get("lastPrice", 0) or 0,
            "ce_iv": ce.get("impliedVolatility", 0) or 0,
            "pe_oi": pe.get("openInterest", 0) or 0,
            "pe_chgoi": pe.get("changeinOpenInterest", 0) or 0,
            "pe_volume": pe.get("totalTradedVolume", 0) or 0,
            "pe_ltp": pe.get("lastPrice", 0) or 0,
            "pe_iv": pe.get("impliedVolatility", 0) or 0,
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df, {}
    total_ce_oi = df["ce_oi"].sum()
    total_pe_oi = df["pe_oi"].sum()
    pcr_oi = total_pe_oi / total_ce_oi if total_ce_oi else 0
    pcr_vol = df["pe_volume"].sum() / df["ce_volume"].sum() if df["ce_volume"].sum() else 0
    # Max Pain
    pain = []
    for k in df["strike"]:
        call_pain = ((df["strike"] - k).clip(lower=0) * df["ce_oi"]).sum()
        put_pain = ((k - df["strike"]).clip(lower=0) * df["pe_oi"]).sum()
        pain.append(call_pain + put_pain)
    max_pain = float(df["strike"].iloc[np.argmin(pain)]) if pain else underlying
    atm = df.iloc[(df["strike"] - underlying).abs().argsort()[:1]]["strike"].values[0]
    call_wall = df.loc[df["ce_oi"].idxmax(), "strike"] if not df.empty else None
    put_wall = df.loc[df["pe_oi"].idxmax(), "strike"] if not df.empty else None
    summary = {
        "underlying": underlying,
        "pcr_oi": round(pcr_oi, 3),
        "pcr_vol": round(pcr_vol, 3),
        "max_pain": max_pain,
        "atm": atm,
        "call_wall": call_wall,
        "put_wall": put_wall,
        "nearest_expiry": expiry_dates[0] if expiry_dates else None,
        "total_ce_oi": int(total_ce_oi),
        "total_pe_oi": int(total_pe_oi),
    }
    return df, summary

def get_expected_move(spot: float, vix: float, days: float = 1.0) -> Dict[str, float]:
    move = spot * (vix / 100) * np.sqrt(days / 365)
    return {
        "1sigma": round(move, 1),
        "2sigma": round(2 * move, 1),
        "lower_1s": round(spot - move, 1),
        "upper_1s": round(spot + move, 1),
        "lower_2s": round(spot - 2*move, 1),
        "upper_2s": round(spot + 2*move, 1),
    }

def get_atm_straddle(df: pd.DataFrame, atm: float) -> Optional[Dict]:
    if df.empty:
        return None
    row = df.iloc[(df["strike"] - atm).abs().argsort()[:1]]
    if row.empty:
        return None
    ce = float(row["ce_ltp"].values[0])
    pe = float(row["pe_ltp"].values[0])
    return {"atm_strike": float(row["strike"].values[0]), "ce_ltp": ce, "pe_ltp": pe, "straddle": ce + pe}

def get_global_indices() -> Dict[str, Dict]:
    symbols = {
        "S&P 500": "^GSPC", "Nasdaq": "^IXIC", "Dow": "^DJI",
        "US VIX": "^VIX", "Nikkei": "^N225", "Hang Seng": "^HSI",
        "FTSE": "^FTSE", "DAX": "^GDAXI", "USDINR": "INR=X",
        "Crude": "CL=F", "Gold": "GC=F"
    }
    out = {}
    for name, sym in symbols.items():
        try:
            t = yf.Ticker(sym)
            h = t.history(period="5d")
            if not h.empty:
                last = float(h["Close"].iloc[-1])
                prev = float(h["Close"].iloc[-2]) if len(h) > 1 else last
                out[name] = {"last": round(last, 2), "chg_pct": round((last/prev - 1)*100, 2)}
        except Exception:
            continue
    return out

def get_live_quotes() -> Dict[str, Any]:
    tickers = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "VIX": "^INDIAVIX", "SENSEX": "^BSESN"}
    out = {}
    for name, sym in tickers.items():
        try:
            t = yf.Ticker(sym)
            h = t.history(period="2d")
            if not h.empty:
                last = float(h["Close"].iloc[-1])
                prev = float(h["Close"].iloc[-2]) if len(h) > 1 else last
                out[name] = {"last": round(last, 2), "chg_pct": round((last/prev-1)*100, 2)}
        except Exception:
            continue
    return out

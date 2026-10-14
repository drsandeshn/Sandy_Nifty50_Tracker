# Sandy_Nifty50_Tracker

Clean public Nifty 50 market tracker for personal educational use.

## Features
- Overview: Nifty spot, VIX regime, expected move, bias score, global cues, CPR
- Option Chain: OI, ΔOI, PCR, Max Pain, walls, ATM straddle
- GEX Board: Net GEX, regime, Gamma Flip, strike-wise GEX
- Signals: Transparent rule-based confluence notes
- My Positions: Session-only manual tracking (no data saved)
- Global & News keywords

No personal data or Telegram tokens are stored.

## Local run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Push this folder to a public GitHub repository
2. Go to https://share.streamlit.io
3. New app → select the repo → main file: app.py
4. Deploy

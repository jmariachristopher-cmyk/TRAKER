# Weekly Options Tracker (Streamlit + Upstox)

A live-updating replacement for the Google Sheets tracker. Pulls SELL prices
straight from the Upstox option chain for up to 4 positions a week.

## What it does

- Edit each position (underlying, lot size, expiry, and 3 legs) right in the app.
- Paste your Upstox access token once per session — it is never saved or committed.
- Click "Refresh Now" or turn on Auto-Refresh (every 30s–5min) to pull live LTPs.
- Auto-refresh only actually re-fetches during NSE market hours (9:15 AM–3:30 PM
  IST, Mon–Fri) — outside that window it just idles.
- Shows Diff, P&L per leg, and 3 RISK metrics (premium, diff, P&L) per position,
  same formulas as the original sheet.

## Deploy it (free, ~5 minutes)

1. Create a new **public or private** GitHub repo (e.g. `options-tracker`).
2. Upload `app.py`, `requirements.txt`, and this `README.md` to it.
3. Go to https://share.streamlit.io and sign in with GitHub.
4. Click **"New app"**, pick your repo/branch, and set the main file to `app.py`.
5. Click **Deploy**. Streamlit Cloud installs `requirements.txt` automatically
   and gives you a URL like `https://yourname-options-tracker.streamlit.app`.

That URL is your live dashboard — open it on desktop or phone, paste today's
Upstox token, and go.

## Daily use

1. Generate a fresh Upstox access token (tokens expire every day — this is an
   Upstox platform limit, not something the app can bypass).
2. Open your Streamlit app URL.
3. Paste the token into the sidebar.
4. Toggle "Auto-refresh" on, or click "Refresh Now" whenever you want a manual pull.

## Notes

- Nothing is stored server-side between sessions — if you refresh the browser tab,
  you'll need to re-enter the token and any position edits you made that session.
  If you want positions to persist across restarts, say so and this can be
  extended to read/write a small JSON or Google Sheet as backing storage.
- Verify `NSE_EQ|GODREJPROP` is the exact instrument key for GODREJPROP options
  via Upstox's instrument search — index vs. stock option keys are formatted
  differently.

import streamlit as st
import requests
from datetime import datetime, date
from zoneinfo import ZoneInfo
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Weekly Options Tracker", layout="wide")

IST = ZoneInfo("Asia/Kolkata")

# ---------------------------------------------------------------------------
# Default position config -- mirrors the original weekly_options_tracker layout
# ---------------------------------------------------------------------------
DEFAULT_POSITIONS = [
    {
        "name": "Position 1",
        "underlying_key": "NSE_INDEX|Nifty 50",
        "lot_size": 65,
        "expiry": date(2026, 8, 27),
        "legs": [
            {"label": "SELL ATM CE", "qty": 1, "buy": 118.65, "strike_label": "24100 CE"},
            {"label": "BUY OTM CE", "qty": 1, "buy": 96.25, "strike_label": "24050 CE"},
            {"label": "BUY OTM CE", "qty": 1, "buy": 77.0, "strike_label": "24000 CE"},
        ],
    },
    {
        "name": "Position 2",
        "underlying_key": "NSE_EQ|GODREJPROP",
        "lot_size": 325,
        "expiry": date(2026, 8, 27),
        "legs": [
            {"label": "SELL ATM PE", "qty": 1, "buy": 44.95, "strike_label": "2000 PE"},
            {"label": "BUY OTM PE", "qty": 1, "buy": 34.0, "strike_label": "1980 PE"},
            {"label": "BUY OTM PE", "qty": 1, "buy": 24.7, "strike_label": "1960 PE"},
        ],
    },
    {
        "name": "Position 3",
        "underlying_key": "",
        "lot_size": 1,
        "expiry": date.today(),
        "legs": [
            {"label": "SELL ATM CE", "qty": 1, "buy": 0.0, "strike_label": ""},
            {"label": "BUY OTM CE", "qty": 1, "buy": 0.0, "strike_label": ""},
            {"label": "BUY OTM CE", "qty": 1, "buy": 0.0, "strike_label": ""},
        ],
    },
    {
        "name": "Position 4",
        "underlying_key": "",
        "lot_size": 1,
        "expiry": date.today(),
        "legs": [
            {"label": "SELL ATM CE", "qty": 1, "buy": 0.0, "strike_label": ""},
            {"label": "BUY OTM CE", "qty": 1, "buy": 0.0, "strike_label": ""},
            {"label": "BUY OTM CE", "qty": 1, "buy": 0.0, "strike_label": ""},
        ],
    },
]

if "positions" not in st.session_state:
    st.session_state.positions = DEFAULT_POSITIONS


# ---------------------------------------------------------------------------
# Upstox helpers
# ---------------------------------------------------------------------------
def is_market_hours():
    now = datetime.now(IST)
    if now.weekday() > 4:  # Sat/Sun
        return False
    minutes = now.hour * 100 + now.minute
    return 915 <= minutes <= 1530


@st.cache_data(ttl=60, show_spinner=False)
def fetch_option_chain(underlying_key, expiry_str, token):
    url = "https://api.upstox.com/v2/option/chain"
    params = {"instrument_key": underlying_key, "expiry_date": expiry_str}
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json().get("data", [])


def parse_strike_label(label):
    label = (label or "").strip()
    parts = label.split()
    if len(parts) != 2:
        return None
    strike_str, opt_type = parts
    opt_type = opt_type.upper()
    if opt_type not in ("CE", "PE"):
        return None
    try:
        return float(strike_str), opt_type
    except ValueError:
        return None


def lookup_ltp(chain_data, strike, opt_type):
    for item in chain_data:
        if round(item.get("strike_price", -1)) == round(strike):
            leg = item.get("call_options") if opt_type == "CE" else item.get("put_options")
            if leg and leg.get("market_data"):
                return leg["market_data"].get("ltp")
    return None


# ---------------------------------------------------------------------------
# Sidebar: token + auto-refresh controls
# ---------------------------------------------------------------------------
st.sidebar.header("Upstox connection")
token = st.sidebar.text_input(
    "Access token (regenerate daily)", type="password",
    help="Paste today's Upstox access token here. It is NOT saved anywhere -- "
         "you re-enter it each session/day.",
)

auto_refresh_on = st.sidebar.toggle("Auto-refresh", value=False)
refresh_seconds = st.sidebar.slider("Refresh every (seconds)", 30, 300, 180, step=30)

st.sidebar.markdown("---")
if is_market_hours():
    st.sidebar.success("Market is OPEN (9:15 AM - 3:30 PM IST)")
else:
    st.sidebar.warning("Market is CLOSED right now")

if auto_refresh_on and is_market_hours():
    st_autorefresh(interval=refresh_seconds * 1000, key="auto_refresh_timer")

st.title("📈 Weekly Options Tracker")
st.caption("Live SELL prices pulled from the Upstox option chain. Edit each position below.")

manual_refresh = st.button("🔁 Refresh Now", type="primary")


# ---------------------------------------------------------------------------
# Editable position blocks + live table
# ---------------------------------------------------------------------------
for p_idx, pos in enumerate(st.session_state.positions):
    with st.expander(f"⚙️ Edit {pos['name']}", expanded=False):
        c1, c2, c3 = st.columns(3)
        pos["name"] = c1.text_input("Position name", pos["name"], key=f"name_{p_idx}")
        pos["underlying_key"] = c2.text_input(
            "Upstox underlying key", pos["underlying_key"], key=f"key_{p_idx}",
            help='e.g. "NSE_INDEX|Nifty 50" or "NSE_EQ|GODREJPROP"',
        )
        pos["lot_size"] = c3.number_input("Lot size", value=int(pos["lot_size"]), key=f"lot_{p_idx}")
        pos["expiry"] = st.date_input("Expiry", pos["expiry"], key=f"expiry_{p_idx}")

        leg_options = ["SELL ATM CE", "BUY OTM CE", "SELL ATM PE", "BUY OTM PE",
                       "SELL OTM CE", "BUY ATM CE", "SELL OTM PE", "BUY ATM PE"]
        for l_idx, leg in enumerate(pos["legs"]):
            lc1, lc2, lc3, lc4 = st.columns(4)
            default_index = leg_options.index(leg["label"]) if leg["label"] in leg_options else 0
            leg["label"] = lc1.selectbox("Leg", leg_options, index=default_index, key=f"label_{p_idx}_{l_idx}")
            leg["qty"] = lc2.number_input("Qty (lots)", value=int(leg["qty"]), key=f"qty_{p_idx}_{l_idx}")
            leg["buy"] = lc3.number_input("Entry (BUY) price", value=float(leg["buy"]), format="%.2f", key=f"buy_{p_idx}_{l_idx}")
            leg["strike_label"] = lc4.text_input("Strike (SBB), e.g. 24100 CE", leg["strike_label"], key=f"strike_{p_idx}_{l_idx}")

    # ---- Live table for this position ----
    st.subheader(pos["name"] or f"Position {p_idx+1}")

    chain_data = None
    fetch_error = None
    if token and pos["underlying_key"]:
        try:
            expiry_str = pos["expiry"].strftime("%Y-%m-%d")
            if manual_refresh:
                fetch_option_chain.clear()
            chain_data = fetch_option_chain(pos["underlying_key"], expiry_str, token)
        except requests.exceptions.HTTPError as e:
            fetch_error = f"Upstox API error: {e}"
        except Exception as e:
            fetch_error = f"Error: {e}"

    if fetch_error:
        st.error(fetch_error)

    rows = []
    total_risk_premium = 0.0
    total_diff = 0.0
    total_pnl = 0.0

    for leg in pos["legs"]:
        parsed = parse_strike_label(leg["strike_label"])
        sell_price = None
        if chain_data and parsed:
            strike, opt_type = parsed
            sell_price = lookup_ltp(chain_data, strike, opt_type)

        is_sell_leg = leg["label"].startswith("SELL")
        buy_price = leg["buy"]

        diff = None
        pnl = None
        if sell_price is not None:
            diff = (buy_price - sell_price) if is_sell_leg else (sell_price - buy_price)
            pnl = diff * pos["lot_size"]
            total_diff += diff
            total_pnl += pnl

        total_risk_premium += buy_price if is_sell_leg else -buy_price

        rows.append({
            "Leg": leg["label"],
            "Qty": leg["qty"],
            "BUY": buy_price,
            "SELL (live)": sell_price if sell_price is not None else "—",
            "Diff": round(diff, 2) if diff is not None else "—",
            "P&L": round(pnl, 2) if pnl is not None else "—",
            "SBB": leg["strike_label"],
        })

    st.dataframe(rows, use_container_width=True, hide_index=True)

    rc1, rc2, rc3 = st.columns(3)
    rc1.metric("RISK (premium)", f"{total_risk_premium:,.2f}")
    rc2.metric("RISK (diff)", f"{total_diff:,.2f}")
    rc3.metric("RISK (P&L)", f"{total_pnl:,.2f}")

    st.markdown("---")

st.caption(
    f"Last checked: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')} IST · "
    "Access token expires daily -- paste a fresh one each trading morning."
)

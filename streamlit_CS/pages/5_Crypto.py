import streamlit as st
import pandas as pd
import requests
import time
import plotly.express as px

st.set_page_config(page_title="Live API Demo", page_icon="📡", layout="wide")
st.title("📡 Live Data from a Free API (CoinGecko)")
st.caption("Public endpoint, no API key required. Updates live.")

# ---------- Section A: Read once ----------
COINS = ["bitcoin", "ethereum"]
VS = "usd"
url = f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(COINS)}&vs_currencies={VS}"


#Helper function
HEADERS = {"User-Agent": "msudenver-dataviz/1.0", "Accept": "application/json"}

def get_json(u):
    resp = requests.get(u, timeout=10, headers=HEADERS)
    # Friendly handling for 429
    if resp.status_code == 429:
        retry = int(resp.headers.get("Retry-After", "20"))
        raise requests.HTTPError(f"429 Too Many Requests. Retry after ~{retry}s.", response=resp)
    resp.raise_for_status()
    return resp.json()


try:
    data = get_json(url)
    df_once = pd.DataFrame(data).T.reset_index().rename(columns={"index": "coin"})
except requests.HTTPError as e:
    st.error(f"HTTP error: {e}")
    st.stop()
except requests.RequestException as e:
    st.error(f"Network error: {e}")
    st.stop()


st.subheader("A) Read once (no cache)")
st.dataframe(df_once)

st.subheader("A1) Quick bar plot")
fig_bar = px.bar(df_once, x="coin", y=VS, title="Current price (USD)")
st.plotly_chart(fig_bar, use_container_width=True)

# ---------- Section B: Error handling ----------
st.subheader("B) Error handling")
try:
    data = get_json(url)
    df_now = pd.DataFrame(data).T.reset_index().rename(columns={"index": "coin"})
    st.success("✅ API call ok")
except requests.HTTPError as e:
    st.warning("⚠️ API limit hit or temporarily blocked. Showing the message below and stopping.")
    st.error(str(e))
    st.stop()
except requests.RequestException as e:
    st.error(f"API error: {e}")
    st.stop()


# ---------- Section C: Cache with TTL ----------
st.subheader("C) Cache with TTL")

CACHE_TTL = 60  # was 20; bump to reduce hits

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_prices():
    d = get_json(url)
    return pd.DataFrame(d).T.reset_index().rename(columns={"index": "coin"})

def build_url(ids):
    return f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(ids)}&vs_currencies={VS}"

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_prices_for(ids_tuple):
    d = get_json(build_url(list(ids_tuple)))
    return pd.DataFrame(d).T.reset_index().rename(columns={"index": "coin"})


# ---------- Section D: Live history ----------
st.subheader("D) Live series with session history")

if "price_history" not in st.session_state:
    st.session_state.price_history = pd.DataFrame(columns=["time", "coin", "price"])

#refresh_sec = st.slider("Refresh every (sec)", 5, 60, 10)
refresh_sec = st.slider("Refresh every (sec)", 30, 180, 60)  # >= CACHE_TTL recommended

live = st.toggle("Enable live updates", value=True)

df_tick = fetch_prices()
timestamp = pd.Timestamp.now()

new_rows = [{"time": timestamp, "coin": row["coin"], "price": row[VS]} for _, row in df_tick.iterrows()]
hist = pd.concat([st.session_state.price_history, pd.DataFrame(new_rows)], ignore_index=True)

window_min = st.slider("Show last N minutes", 1, 60, 10)
cutoff = timestamp - pd.Timedelta(minutes=window_min)
hist = hist[hist["time"] >= cutoff].copy()
st.session_state.price_history = hist

if len(hist):
    fig_line = px.line(hist, x="time", y="price", color="coin", title="Live price (USD)", markers=True)
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("Waiting for first tick…")

cols = st.columns(len(COINS))
for i, c in enumerate(COINS):
    latest = hist[hist["coin"] == c]["price"].iloc[-1] if (hist["coin"] == c).any() else None
    with cols[i]:
        st.metric(c.capitalize(), f"${latest:,.2f}" if latest is not None else "—")

# ---------- Section E: Options & polish ----------
st.subheader("E) Options & polish")
available = ["bitcoin","ethereum","solana","dogecoin","cardano","litecoin"]
chosen = st.multiselect("Pick coins", default=COINS, options=available)

def build_url(ids):
    return f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(ids)}&vs_currencies={VS}"

@st.cache_data(ttl=20)
def fetch_prices_for(ids_tuple):
    r = requests.get(build_url(list(ids_tuple)), timeout=10)
    r.raise_for_status()
    d = r.json()
    return pd.DataFrame(d).T.reset_index().rename(columns={"index": "coin"})

df_custom = fetch_prices_for(tuple(chosen) or tuple(COINS))
st.dataframe(df_custom)

# ---------- Section F: Auto-refresh (LAST) ----------

if live:
    st.caption(f"Last refreshed at: {time.strftime('%H:%M:%S')}")
    time.sleep(refresh_sec)
    (getattr(st, "rerun", None) or getattr(st, "experimental_rerun"))()



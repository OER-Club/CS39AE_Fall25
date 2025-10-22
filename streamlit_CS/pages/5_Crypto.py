# live_crypto.py
import streamlit as st
import pandas as pd
import requests
import time
import plotly.express as px

st.set_page_config(page_title="Live API Demo", page_icon="📡", layout="wide")
st.title("📡 Live Data from a Free API (CoinGecko)")
st.caption("Public endpoint, no API key required. Updates live.")

#Step1

st.subheader("1) Read API once (no cache)")
COINS = ["bitcoin", "ethereum"]
VS = "usd"
url = f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(COINS)}&vs_currencies={VS}"

resp = requests.get(url, timeout=10)
resp.raise_for_status()
data = resp.json()           # {'bitcoin': {'usd': 12345}, 'ethereum': {'usd': 2345}}
df_once = pd.DataFrame(data).T.reset_index().rename(columns={"index": "coin"})
st.dataframe(df_once)

#Step 2
st.subheader("2) Quick bar plot")
fig_bar = px.bar(df_once, x="coin", y=VS, title="Current price (USD)")
st.plotly_chart(fig_bar, use_container_width=True)

#Step3
st.subheader("3) Error handling")
try:
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
except requests.RequestException as e:
    st.error(f"API error: {e}")
    st.stop()

df_now = pd.DataFrame(data).T.reset_index().rename(columns={"index": "coin"})
st.success("✅ API call ok")

#Step 4
st.subheader("4) Cache with TTL")

@st.cache_data(ttl=20)  # re-use result for 20s
def fetch_prices():
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    d = r.json()
    return pd.DataFrame(d).T.reset_index().rename(columns={"index": "coin"})

df_cached = fetch_prices()
st.dataframe(df_cached)

#Step5
st.subheader("5) Live series with session history")

# init history
if "price_history" not in st.session_state:
    # columns: time, coin, price
    st.session_state.price_history = pd.DataFrame(columns=["time", "coin", "price"])

refresh_sec = st.slider("Refresh every (sec)", 5, 60, 10)
live = st.toggle("Enable live updates", value=True)

# fetch (respect cache TTL to avoid hammering)
df_tick = fetch_prices()
timestamp = pd.Timestamp.now()

# append to history (one row per coin)
new_rows = []
for _, row in df_tick.iterrows():
    new_rows.append({"time": timestamp, "coin": row["coin"], "price": row[VS]})
hist = pd.concat([st.session_state.price_history, pd.DataFrame(new_rows)], ignore_index=True)

# keep last N minutes to avoid unbounded growth
window_min = st.slider("Show last N minutes", 1, 60, 10)
cutoff = timestamp - pd.Timedelta(minutes=window_min)
hist = hist[hist["time"] >= cutoff].copy()
st.session_state.price_history = hist  # persist

# plot
if len(hist):
    fig_line = px.line(
        hist, x="time", y="price", color="coin",
        title="Live price (USD)", markers=True
    )
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("Waiting for first tick…")

# lightweight metrics
cols = st.columns(len(COINS))
for i, c in enumerate(COINS):
    latest = hist[hist["coin"] == c]["price"].iloc[-1] if (hist["coin"] == c).any() else None
    with cols[i]:
        st.metric(c.capitalize(), f"${latest:,.2f}" if latest else "—")

# auto-rerun loop
live = st.toggle("Enable live updates", value=True)
refresh_sec = st.slider("Refresh every (sec)", 5, 60, 10)

if live:
    st.caption(f"Last refreshed at: {time.strftime('%H:%M:%S')}")
    # ✅ Put sleep + rerun as the LAST statements in your script
    time.sleep(refresh_sec)
    st.experimental_rerun()

#Step 6
st.subheader("6) Options & polish")
# let students pick coins
available = ["bitcoin","ethereum","solana","dogecoin","cardano","litecoin"]
chosen = st.multiselect("Pick coins", default=COINS, options=available)

# rebuild url and cache key when coins change
def build_url(ids):
    return f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(ids)}&vs_currencies={VS}"

@st.cache_data(ttl=20)
def fetch_prices_for(ids):
    r = requests.get(build_url(ids), timeout=10)
    r.raise_for_status()
    d = r.json()
    return pd.DataFrame(d).T.reset_index().rename(columns={"index": "coin"})

df_custom = fetch_prices_for(tuple(chosen) or tuple(COINS))
st.dataframe(df_custom)

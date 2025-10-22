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


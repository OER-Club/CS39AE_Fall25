# live_crypto.py
import streamlit as st
import pandas as pd
import requests
import time
import plotly.express as px

st.set_page_config(page_title="Live API Demo", page_icon="📡", layout="wide")
st.title("📡 Live Data from a Free API (CoinGecko)")
st.caption("Public endpoint, no API key required. Updates live.")

# ---------------- Small helper: resilient HTTP GET (retries + headers) ----------------
def http_get(url, params=None, max_retries=3, backoff=2.0, timeout=10):
    headers = {
        "Accept": "application/json",
        "User-Agent": "msudenver-streamlit-class/1.0 (+contact: instructor@example.edu)"
    }
    attempt = 0
    while True:
        try:
            r = requests.get(url, params=params, headers=headers, timeout=timeout)
            # Retry on 429/5xx
            if r.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                attempt += 1
                time.sleep(backoff ** attempt)
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            if attempt < max_retries:
                attempt += 1
                time.sleep(backoff ** attempt)
                continue
            raise

# ---------------- Step 1 ----------------
st.subheader("1) Read API once (no cache)")
COINS = ["bitcoin", "ethereum"]
VS = "usd"
BASE_URL = "https://api.coingecko.com/api/v3/simple/price"
params = {"ids": ",".join(COINS), "vs_currencies": VS}

# FIX: guard the first call; show fallback if API unhappy
try:
    data = http_get(BASE_URL, params=params)
    df_once = pd.DataFrame(data).T.reset_index().rename(columns={"index": "coin"})
    st.success("✅ API call OK")
except requests.HTTPError as e:
    code = e.response.status_code if e.response is not None else "?"
    st.error(f"API error (HTTP {code}). Showing fallback sample.")
    df_once = pd.DataFrame({"coin": ["bitcoin", "ethereum"], VS: [30000.0, 2000.0]})

st.dataframe(df_once)

# ---------------- Step 2 ----------------
st.subheader("2) Quick bar plot")
fig_bar = px.bar(df_once, x="coin", y=VS, title="Current price (USD)")
st.plotly_chart(fig_bar, use_container_width=True)

# ---------------- Step 3 ----------------
st.subheader("3) Error handling")
# (Kept for teaching—now it uses the same helper)
try:
    data = http_get(BASE_URL, params=params)
    df_now = pd.DataFrame(data).T.reset_index().rename(columns={"index": "coin"})
    st.success("✅ API call ok (guarded)")
except requests.RequestException as e:
    st.error(f"API error: {e}")
    st.stop()

# ---------------- Step 4 ----------------
st.subheader("4) Cache with TTL")

@st.cache_data(ttl=20)  # re-use result for 20s
def fetch

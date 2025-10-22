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

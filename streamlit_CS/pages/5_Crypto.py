# live_crypto.py
import streamlit as st
import pandas as pd
import requests
import time
import plotly.express as px

st.set_page_config(page_title="Live API Demo", page_icon="📡", layout="wide")
st.title("📡 Live Data from a Free API (CoinGecko)")
st.caption("Public endpoint, no API key required. Updates live.")

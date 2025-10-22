import streamlit as st
import pandas as pd
import plotly.express as px
st.set_page_config(page_title="Scaffolded Viz Demo", page_icon="📈", layout="wide")
st.title("📈 Scaffolded Interactive Visualization")

st.subheader("1) Read CSV (no cache)")
uploaded = st.file_uploader("Upload a CSV with columns: date, value[, category]", type=["csv"])

if uploaded:
    df = pd.read_csv(uploaded)
    st.dataframe(df.head())

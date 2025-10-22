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

st.subheader("3) Quick visual (no cache)")
if uploaded:
    # Try to coerce a time axis if present
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    fig = px.line(df, x=df.columns[0], y=df.columns[1], title="Quick Plot")
    st.plotly_chart(fig, use_container_width=True)

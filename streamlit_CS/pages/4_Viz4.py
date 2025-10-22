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

st.subheader("4) Add filters")
if uploaded:
    # Optional category filter
    cat_col = "category" if "category" in df.columns else None
    if cat_col:
        cats = ["(All)"] + sorted(df[cat_col].dropna().unique().tolist())
        choice = st.selectbox("Category filter", cats)
        df_view = df if choice == "(All)" else df[df[cat_col] == choice]
    else:
        df_view = df

    # Time window (if there is a date)
    if "date" in df_view.columns and pd.api.types.is_datetime64_any_dtype(df_view["date"]):
        last_n = st.slider("Last N rows to chart", 10, min(500, len(df_view)), 50)
        df_view = df_view.tail(last_n)

    st.dataframe(df_view.head())
    fig_filt = px.line(
        df_view,
        x=df_view.columns[0],
        y=df_view.columns[1],
        color=cat_col if cat_col else None,
        title="Interactive Plot"
    )
    st.plotly_chart(fig_filt, use_container_width=True)

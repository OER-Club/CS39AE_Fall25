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

st.subheader("4) Add check-box filters + Bar Chart")

if uploaded:
    # ---- Category filter using checkboxes ----
    cat_col = "category" if "category" in df.columns else None
    if cat_col:
        st.write("Select categories to display:")
        cats = sorted(df[cat_col].dropna().unique().tolist())
        selected = []
        for c in cats:
            if st.checkbox(c, value=True, key=f"chk_{c}"):
                selected.append(c)

        # Filter data based on checked boxes
        df_view = df[df[cat_col].isin(selected)] if selected else df.iloc[0:0]
    else:
        df_view = df

    # ---- Row limit slider ----
    row_limit = st.slider("Number of rows to display", 5, len(df_view), min(50, len(df_view)))
    df_view = df_view.tail(row_limit)

    st.dataframe(df_view.head())

    # ---- Create bar chart ----
    x_col = df_view.columns[0]
    y_col = df_view.columns[1]

    fig_bar = px.bar(
        df_view,
        x=x_col,
        y=y_col,
        color=cat_col if cat_col else None,
        title=f"Bar Chart of {y_col} by {x_col}",
        barmode="group"
    )
    fig_bar.update_layout(xaxis_title=x_col, yaxis_title=y_col)
    st.plotly_chart(fig_bar, use_container_width=True)


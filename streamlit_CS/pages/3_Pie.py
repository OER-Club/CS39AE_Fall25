import streamlit as st
import pandas as pd
import plotly.express as px

# -------------------- PAGE SETUP --------------------
st.set_page_config(page_title="Simple Pie Chart", page_icon="🥧", layout="wide")
st.title("Interactive Pie Chart from CSV")

st.write("""
Upload a small CSV file (around 10 rows) with **two columns**:
- `category`: labels for each slice  
- `value`: numeric values representing slice size  
""")

# -------------------- UPLOAD DATA --------------------
use_sample = st.toggle("Use bundled sample file (data/pie_demo.csv)", value=True)

uploaded = use_sample
if not use_sample:
  uploaded_file = st.file_uploader("📂 Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    # Step 1: Read CSV
    df = pd.read_csv(uploaded_file)

    # Step 2: Show data table
    st.subheader("Data Preview")
    st.dataframe(df, use_container_width=True)

    # Step 3: Make an interactive pie chart
    st.subheader("Interactive Pie Chart")
    fig = px.pie(
        df,
        names="category",
        values="value",
        title="Category Share (Interactive Pie Chart)",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👆 Upload a CSV file to begin (with 'category' and 'value' columns).")

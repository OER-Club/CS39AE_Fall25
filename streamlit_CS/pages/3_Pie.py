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

# -------------------- TOGGLE DATA SOURCE --------------------
use_sample = st.toggle("Use sample CSV from GitHub", value=True)

if use_sample:
    # Step 1: Read CSV from GitHub raw link
    github_csv_url = "data/pie_demo.csv"
    # 👆 Replace <username> and <repo> with your actual GitHub info
    df = pd.read_csv(github_csv_url)
    st.success("Loaded sample CSV from GitHub ✅")
else:
    # Step 2: Let user upload CSV
    uploaded_file = st.file_uploader("📂 Upload your CSV file", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success("Loaded your uploaded CSV ✅")
    else:
        st.info(" Upload a CSV file to continue.")
        st.stop()

# -------------------- PREVIEW --------------------
st.subheader("Data Preview")
st.dataframe(df, use_container_width=True)

# -------------------- PIE CHART --------------------
st.subheader("Interactive Pie Chart")
fig = px.pie(
    df,
    names="category",
    values="value",
    title="Category Share (Interactive Pie Chart)",
    color_discrete_sequence=px.colors.qualitative.Pastel
)
st.plotly_chart(fig, use_container_width=True)

st.caption("Built in Streamlit • CSV read directly from GitHub or upload option")

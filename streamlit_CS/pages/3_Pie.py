import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# -------------------- PAGE SETUP --------------------
st.set_page_config(page_title="Simple Pie Chart", page_icon="🥧", layout="wide")
st.title("🥧 Interactive Pie Chart from CSV")

st.write("""
Use the toggle to load a **sample CSV file** from your repo’s `data/` folder,  
or upload your own 2-column CSV with:
- `category` — labels for each slice  
- `value` — numeric values representing slice size
""")

# -------------------- TOGGLE --------------------
use_sample = st.toggle("Use bundled sample file (data/pie_demo.csv)", value=True)

if use_sample:
    # Get absolute path safely
    csv_path = Path(__file__).parent.parent / "data" / "pie_demo.csv"
    # Example: if this file is in pages/, it goes up one level (../data/pie_demo.csv)
    
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        st.success(f"✅ Loaded sample CSV from {csv_path.name}")
    else:
        st.error("❌ Could not find data/pie_demo.csv. Make sure it exists in the 'data' folder.")
        st.stop()
else:
    uploaded_file = st.file_uploader("📂 Upload your CSV file", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success("✅ Loaded your uploaded CSV")
    else:
        st.info("Upload a CSV file to continue.")
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

st.caption("Built in Streamlit • Reads from local 'data/pie_demo.csv' or user upload")

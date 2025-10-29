import streamlit as st

st.title("Simple Row and Column Layout")

# ---- Row 1: Two Columns ----
st.write("### Row 1: Two Columns")

col1, col2 = st.columns(2)

col1.write("This is Column 1")
col2.write("This is Column 2")

# ---- Row 2: Three Columns ----
st.write("### Row 2: Three Columns")

colA, colB, colC = st.columns(3)

colA.write("Column A")
colB.write("Column B")
colC.write("Column C")

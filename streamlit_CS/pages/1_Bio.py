import streamlit as st
import os

st.title("My Bio")

# ---------- TODO: Replace with your own info ----------
NAME = "Ren"
PROGRAM = "Your Program / Computer Science / Role"
INTRO = (
    "Write 2–3 sentences about yourself: what you’re studying/working on, "
    "what excites you about data visualization or computing, etc."
)
FUN_FACTS = [
    "I love …",
    "I’m learning …",
    "I want to build a Network Project",
]
PHOTO_PATH = "Path(__file__).resolve().parent.parent / "assets" / "Ren_Photo.jpg"  # Put a file in repo root or set a URL

# ---------- Layout ----------
col1, col2 = st.columns([1, 2], vertical_alignment="center")

with col1:
        if photo_path.exists():
        st.image(str(photo_path), caption=NAME, use_container_width=True)
    else:
        st.info(
            "⚠️ Couldn't find the image. Make sure you have `Ren_Photo.jpg` inside an `assets` folder "
            "at the same level as your main Streamlit app."
        )
with col2:
    st.subheader(NAME)
    st.write(PROGRAM)
    st.write(INTRO)
    
st.markdown("### Fun facts")
for i, f in enumerate(FUN_FACTS, start=1):
    st.write(f"- {f}")

st.divider()
st.caption("Edit `pages/1_Bio.py` to customize this page.")

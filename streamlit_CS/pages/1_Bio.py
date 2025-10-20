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
def find_photo(filename="Ren_Photo.jpg"):
    # Try common locations for multipage apps
    try:
        script_dir = Path(__file__).resolve().parent
    except NameError:
        script_dir = Path.cwd()

    candidates = [
        script_dir / "assets" / filename,          # pages/assets/...
        script_dir.parent / "assets" / filename,   # root/assets/... (common)
        Path("assets") / filename,                 # cwd/assets/...
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return None

photo_src = find_photo("Ren_Photo.jpg")

# -------------------- LAYOUT --------------------
col1, col2 = st.columns([1, 2], vertical_alignment="center")

with col1:
    if photo_src:
        st.image(photo_src, caption=NAME, use_container_width=True)
    else:
        st.info(
            "📷 Place `Ren_Photo.jpg` inside an `assets/` folder at the app root "
            "or update the path in `find_photo()`."
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

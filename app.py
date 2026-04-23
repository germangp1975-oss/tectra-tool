import streamlit as st
import tempfile
from fem_toolV8 import analyze_file

st.set_page_config(page_title="TECTRA™ Tool", layout="centered")

# -------------------------------
# CONTROL DE USO
# -------------------------------
if "used" not in st.session_state:
    st.session_state.used = False

if "unlocked" not in st.session_state:
    st.session_state.unlocked = False

# -------------------------------
# HEADER
# -------------------------------
st.title("TECTRA™ — Structural Decision Tool")
st.markdown("Fast structural decision engine based on FEM results")
st.markdown("Not a simulation tool. A decision tool.")

st.markdown("---")

# -------------------------------
# BLOQUEO / ACCESO
# -------------------------------
if not st.session_state.unlocked:

    if st.session_state.used:
        st.error("Free trial already used")

        st.markdown("### 🔒 Unlock full access")
        st.markdown(
            "[👉 Pay here to unlock](https://www.tectra-tech.com/_paylink/AZ263VkL)"
        )

        code = st.text_input("Enter access code")

        if code == "TECTRA2026":
            st.session_state.unlocked = True
            st.success("Access granted")
        else:
            st.stop()

    else:
        st.info("You have 1 free analysis available")

# -------------------------------
# UI
# -------------------------------
uploaded_files = st.file_uploader(
    "Upload .vtu files",
    type=["vtu"],
    accept_multiple_files=True
)

yield_strength = st.number_input(
    "Yield strength (MPa) [optional]",
    value=250
)

run = st.button("Run Analysis")

# -------------------------------
# EJECUCIÓN
# -------------------------------
if run and uploaded_files:
    st.session_state.used = True

    results = []

    for file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name

        result = analyze_file(tmp_path, yield_strength)
        results.append((file.name, result))

    st.markdown("## Results")

    for name, res in results:
        st.markdown(f"### {name}")
        st.text(res)

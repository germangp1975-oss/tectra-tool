import streamlit as st
import tempfile
from fem_toolV8 import analyze_file

st.set_page_config(page_title="TECTRA FEM Tool", layout="centered")

st.title("TECTRA™ — Structural Insight Engine")
st.markdown("Upload a FEM file (.vtu, .vtk) for automated structural analysis")

uploaded_file = st.file_uploader("Select FEM file", type=["vtu", "vtk"])
yield_limit = st.number_input("Yield strength (MPa) [optional]", value=250)

if uploaded_file is not None:

    st.success("File successfully loaded")

    if st.button("Run Analysis"):

        # Create real temporary file ONLY at execution time
        with tempfile.NamedTemporaryFile(delete=False, suffix=".vtu") as tmp:
            tmp.write(uploaded_file.read())
            temp_path = tmp.name

        with st.spinner("Processing FEM data..."):
            result = analyze_file(temp_path, yield_limit)

        st.subheader("Analysis Results")
        st.text(result)

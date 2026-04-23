import streamlit as st
import tempfile
import os
from fem_toolV8 import analyze_file

st.set_page_config(page_title="TECTRA FEM Tool", layout="centered")

st.title("TECTRA™ — Structural Insight Engine")
st.markdown("Upload a FEM (.vtu) file for automated structural analysis")

uploaded_file = st.file_uploader("Select .vtu file", type=["vtu"])
yield_limit = st.number_input("Yield strength (MPa) [optional]", value=250)

if uploaded_file is not None:

    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".vtu") as tmp:
        tmp.write(uploaded_file.read())
        temp_path = tmp.name

    st.success("File successfully loaded")

    if st.button("Run Analysis"):

        with st.spinner("Processing FEM data..."):
            result = analyze_file(temp_path, yield_limit)

        st.subheader("Analysis Results")
        st.text(result)

    # Cleanup temporary file
    try:
        os.remove(temp_path)
    except:
        pass
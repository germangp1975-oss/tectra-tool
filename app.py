import streamlit as st
from fem_toolV8 import analyze_file

st.set_page_config(page_title="TECTRA Structural Insight Engine", layout="centered")

st.markdown(
    "<h2>TECTRA™ — Structural Insight Engine</h2>",
    unsafe_allow_html=True
)

st.markdown("Upload a FEM (.vtu) file for automated structural analysis")

uploaded_file = st.file_uploader("Select .vtu file", type=["vtu"])

yield_limit = st.number_input("Yield strength (MPa) [optional]", value=250)

if uploaded_file is not None:
    st.success("File successfully loaded")

    if st.button("Run Analysis"):
        with st.spinner("Processing FEM data..."):
            result = analyze_file(uploaded_file, yield_limit)

        st.markdown("## Analysis Results")
        st.text(result)

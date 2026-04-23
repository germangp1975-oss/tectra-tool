import streamlit as st
import tempfile
from fem_toolV9 import analyze_file

st.set_page_config(page_title="TECTRA FEM Tool", layout="centered")

st.title("TECTRA™ — Structural Insight Engine")
st.markdown("Automated structural assessment for FEM results")

uploaded_file = st.file_uploader("Upload FEM file (.vtu)", type=["vtu"])
yield_limit = st.number_input("Yield strength (MPa)", value=250.0)

if uploaded_file is not None:

    st.success("File loaded")

    if st.button("Run Analysis"):

        with tempfile.NamedTemporaryFile(delete=False, suffix=".vtu") as tmp:
            tmp.write(uploaded_file.read())
            temp_path = tmp.name

        with st.spinner("Processing FEM data..."):
            result = analyze_file(temp_path, yield_limit)

        st.subheader("Structural Assessment")

        # Mostrar resumen limpio arriba
        lines = result.split("\n")
        summary = []
        detailed = []

        for line in lines:
            if any(k in line for k in [
                "Score", "Risk", "Failure", "Fatigue", "CRITICAL LOCATION"
            ]):
                summary.append(line)
            else:
                detailed.append(line)

        st.text("\n".join(summary))

        # Detalle desplegable
        with st.expander("Detailed engineering data"):
            st.text("\n".join(detailed))

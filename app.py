import streamlit as st
import tempfile
from fem_toolV8 import analyze_file

st.set_page_config(page_title="TECTRA™ FEM Tool", layout="centered")

st.title("TECTRA™ — FEM Decision Engine")

uploaded_file = st.file_uploader("Upload .vtu file", type=["vtu"])

yield_strength = st.number_input(
    "Yield strength (MPa) [optional]",
    min_value=0.0,
    value=250.0
)

if uploaded_file is not None:

    with tempfile.NamedTemporaryFile(delete=False, suffix=".vtu") as tmp:
        tmp.write(uploaded_file.read())
        file_path = tmp.name

    with st.spinner("Analyzing..."):
        result = analyze_file(file_path, yield_strength)

    if "error" in result:
        st.error(result["error"])

    else:
        st.subheader("RESULT")

        st.write("**Decision:**", result["decision"])
        st.write("**Structure type:**", result["structure_type"])
        st.write("**Geometric risk:**", result["geometric_risk"])
        st.write("**Structural risk:**", result["structural_risk"])
        st.write("**Confidence:**", result["confidence"])

        st.subheader("Metrics")

        st.write("Max stress:", round(result["max_stress"], 2))
        st.write("Mean stress:", round(result["mean_stress"], 2))
        st.write("Ratio:", round(result["ratio"], 2))
        st.write("Critical %:", round(result["critical_percentage"], 2))

        if result["safety_factor"] is not None:
            st.write("Safety factor:", round(result["safety_factor"], 2))

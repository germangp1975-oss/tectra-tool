import streamlit as st
import tempfile
import os
from fem_toolV9 import analyze_file

st.set_page_config(page_title="TECTRA FEM Tool", layout="centered")

st.title("TECTRA™ — Structural Insight Engine")
st.markdown("Automated structural assessment for FEM results")

uploaded_file = st.file_uploader("Upload FEM file (.vtu)", type=["vtu"])
yield_limit = st.number_input("Yield strength (MPa)", value=250.0)

if uploaded_file:

    st.success("File loaded")

    if st.button("Run Analysis"):

        with tempfile.NamedTemporaryFile(delete=False, suffix=".vtu") as tmp:
            tmp.write(uploaded_file.read())
            path = tmp.name

        try:
            with st.spinner("Analyzing structure..."):
                result = analyze_file(path, yield_limit)

            if "error" in result:
                st.error(result["error"])
            else:

                # --- SCORE ---
                st.subheader("Structural Score")
                st.metric("Score", f"{result['score']} / 100")

                # --- RISK ---
                if result["risk"] == "LOW":
                    st.success(f"Risk Level: {result['risk']}")
                elif result["risk"] == "MEDIUM":
                    st.warning(f"Risk Level: {result['risk']}")
                else:
                    st.error(f"Risk Level: {result['risk']}")

                # --- METRICS ---
                st.subheader("Key Metrics")
                st.write(f"Max stress: {result['max_stress']:.2f}")
                st.write(f"Mean stress: {result['mean_stress']:.2f}")
                st.write(f"Critical points: {result['critical_points']}")
                st.write(f"Stress gradient: {result['gradient']:.2f}")

                # --- FAILURE ---
                st.subheader("Failure Mode")
                st.write(result["failure"])

                # --- ACTIONS ---
                st.subheader("Engineering Recommendations")
                for a in result["actions"]:
                    st.write(f"- {a}")

        finally:
            try:
                os.remove(path)
            except:
                pass
import streamlit as st
from fem_toolV8 import analyze_file

st.set_page_config(page_title="TECTRA FEM Tool", layout="centered")

st.markdown(
    "<h2>TECTRA™ — Structural Insight Engine</h2>",
    unsafe_allow_html=True
)

st.markdown("Sube un archivo FEM (.vtu) para análisis automático")

uploaded_file = st.file_uploader("Selecciona archivo .vtu", type=["vtu"])

yield_limit = st.number_input("Límite elástico (MPa) [opcional]", value=250)

if uploaded_file is not None:
    st.success("Archivo cargado correctamente")

    with open("temp.vtu", "wb") as f:
        f.write(uploaded_file.read())

    if st.button("Analizar"):
        with st.spinner("Analizando..."):
            result = analyze_file("temp.vtu", yield_limit)

        st.markdown("## Resultado del análisis")
        st.text(result)

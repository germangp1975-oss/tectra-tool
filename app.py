import streamlit as st
import tempfile
from fem_toolV9 import analyze_file

# SIEMPRE LO PRIMERO EN STREAMLIT
st.set_page_config(page_title="TECTRA Structural Insight Engine", layout="centered")

# --- PASSWORD PROTECTION ---
PASSWORD = "TECTRA72"

pwd = st.text_input("Enter password", type="password")

if pwd != PASSWORD:
    st.stop()

# --- UI ---
st.title("TECTRA™ — Structural Insight Engine")
st.markdown("Automated structural assessment for FEM results")

st.info(
    "Engineering evaluation based on classical solid mechanics criteria "
    "(Factor of Safety, stress distribution, and gradient analysis), "
    "aligned with general engineering practices (ASME / ISO approach). "
    "This tool provides decision-support insights, not certified validation."
)

# --- INPUTS ---
files = st.file_uploader("Upload FEM files (.vtu)", type=["vtu"], accept_multiple_files=True)
yield_limit = st.number_input("Yield strength (MPa)", value=250.0)

# --- PROCESS ---
if files:

    st.success(f"{len(files)} file(s) loaded")

    if st.button("Run Analysis"):

        results = []

        for file in files:

            with tempfile.NamedTemporaryFile(delete=False, suffix=".vtu") as tmp:
                tmp.write(file.read())
                temp_path = tmp.name

            res = analyze_file(temp_path, yield_limit)

            if "error" in res:
                st.error(f"{file.name}: {res['error']}")
                continue

            results.append((file.name, res))

        # --- RESULTS ---
        st.subheader("Structural Assessment")

        for name, r in results:

            st.markdown(f"### {name}")

            st.markdown(f"**Decision: {r['decision']}**")
            st.markdown(f"**Conclusion:** {r['conclusion']}")
            st.markdown(f"**Primary issue:** {r['primary_issue']}")

            st.write("---")

            st.write(f"Score: {r['score']:.1f} / 100")
            st.write(f"Risk Level: {r['risk']}")
            st.write(f"FoS: {r['FoS']:.2f} ({r['fos_level']})")

            st.write(f"Failure mode: {r['failure_mode']}")
            st.write(f"Structural behavior: {r['structural_mode']}")
            st.write(f"Geometry: {r['geom_flag']}")

            st.write(
                "Critical location:",
                f"x={r['location'][0]:.2f}, y={r['location'][1]:.2f}, z={r['location'][2]:.2f}"
            )

            st.write("Recommendations:")
            for a in r["actions"]:
                st.write("-", a)

        # --- COMPARISON ---
        if len(results) > 1:

            st.subheader("Comparative Analysis")

            best = max(results, key=lambda x: x[1]["score"])
            worst = min(results, key=lambda x: x[1]["score"])

            for name, r in results:
                st.write(f"{name} → Score: {r['score']:.1f} | FoS: {r['FoS']:.2f}")

            best_score = best[1]["score"]
            worst_score = worst[1]["score"]

            st.write("---")
            st.success(f"Best design: {best[0]} (Score: {best_score:.1f})")
            st.error(f"Worst design: {worst[0]} (Score: {worst_score:.1f})")

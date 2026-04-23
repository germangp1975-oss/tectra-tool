import streamlit as st
import subprocess
import tempfile
import os

st.set_page_config(page_title="FEM Tool PRO", layout="centered")

st.title("FEM Tool — Structural Insight Engine")
st.markdown("Upload one or more FEM result files (.vtu) for comparative diagnosis")

uploaded_files = st.file_uploader(
    "Select .vtu files",
    type=["vtu"],
    accept_multiple_files=True
)

yield_strength = st.text_input("Yield strength (MPa) [optional]", "250")


# -----------------------------
# OUTPUT PARSING
# -----------------------------
def parse_output(output):

    structure_type = ""
    geometric_risk = ""
    decision = ""

    for line in output.splitlines():

        if "Type:" in line:
            structure_type = line.split("Type:")[1].strip()

        if "Geometric risk:" in line:
            geometric_risk = line.split(":")[1].strip()

        if "Result:" in line:
            decision = line.split(":")[1].strip()

    return structure_type, geometric_risk, decision


# -----------------------------
# SCORING
# -----------------------------
def compute_score(structure_type, geometric_risk, decision):

    score = 100

    if decision == "NOT ACCEPTABLE":
        return 10

    if decision == "REVIEW":
        score -= 25

    if "NOTCH" in structure_type:
        score -= 25
    elif "TRANSITION" in structure_type:
        score -= 15

    if geometric_risk == "HIGH":
        score -= 25
    elif geometric_risk == "MEDIUM":
        score -= 10

    return max(10, score)


# -----------------------------
# INDIVIDUAL RESULT DISPLAY
# -----------------------------
def show_result(name, structure_type, geometric_risk, decision):

    score = compute_score(structure_type, geometric_risk, decision)

    st.markdown(f"### {name}")

    if decision == "ACCEPTABLE":
        st.success("🟢 DESIGN ACCEPTABLE")
    elif decision == "REVIEW":
        st.warning("🟡 GEOMETRY REVIEW REQUIRED")
    else:
        st.error("🔴 NOT ACCEPTABLE")

    st.progress(score / 100)
    st.write(f"Score: {score}/100")

    st.write(f"Type: {structure_type}")
    st.write(f"Risk: {geometric_risk}")
    st.write(f"Decision: {decision}")

    return score


# -----------------------------
# PROCESS
# -----------------------------
if uploaded_files:

    st.success(f"{len(uploaded_files)} files uploaded")

    if st.button("Run Analysis"):

        results = []

        for file in uploaded_files:

            with tempfile.NamedTemporaryFile(delete=False, suffix=".vtu") as tmp:
                tmp.write(file.read())
                temp_path = tmp.name

            input_data = temp_path + "\n" + yield_strength + "\n"

            result = subprocess.run(
                ["python", os.path.join(os.getcwd(), "fem_toolV8.py")],
                input=input_data,
                text=True,
                capture_output=True
            )

            if result.stdout:

                structure_type, geometric_risk, decision = parse_output(result.stdout)
                score = compute_score(structure_type, geometric_risk, decision)

                results.append({
                    "name": file.name,
                    "type": structure_type,
                    "risk": geometric_risk,
                    "decision": decision,
                    "score": score,
                    "raw": result.stdout
                })

            try:
                os.remove(temp_path)
            except:
                pass

        # -----------------------------
        # SORT BY SCORE
        # -----------------------------
        results = sorted(results, key=lambda x: x["score"], reverse=True)

        st.markdown("## Design Ranking")

        for i, r in enumerate(results, start=1):

            st.markdown(f"### #{i} — {r['name']}")

            if r["decision"] == "ACCEPTABLE":
                st.success("🟢 DESIGN ACCEPTABLE")
            elif r["decision"] == "REVIEW":
                st.warning("🟡 GEOMETRY REVIEW REQUIRED")
            else:
                st.error("🔴 NOT ACCEPTABLE")

            st.progress(r["score"] / 100)
            st.write(f"Score: {r['score']}/100")

            st.write(f"Type: {r['type']}")
            st.write(f"Risk: {r['risk']}")
            st.write(f"Decision: {r['decision']}")

            with st.expander("Full diagnostic output"):
                st.code(r["raw"])
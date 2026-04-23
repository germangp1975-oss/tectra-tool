import meshio
import numpy as np
import tempfile

def analyze_file(file, yield_limit=None):
    try:
        # 🔴 CLAVE: usar archivo temporal real
        with tempfile.NamedTemporaryFile(delete=False, suffix=".vtu") as tmp:
            tmp.write(file.getvalue())
            tmp_path = tmp.name

        mesh = meshio.read(tmp_path)

    except Exception as e:
        return f"File reading error: {str(e)}"

    output = []
    output.append("=== TECTRA FEM TOOL V8 — Structural Decision Engine ===\n")

    # -----------------------------
    # NODES
    # -----------------------------
    points = mesh.points
    output.append(f"Number of nodes: {len(points)}")

    # -----------------------------
    # DATA FIELDS
    # -----------------------------
    if not mesh.point_data:
        output.append("\n⚠️ No nodal data fields available")
        return "\n".join(output)

    output.append("\nAvailable data fields:")
    for key in mesh.point_data.keys():
        output.append(f" - {key}")

    # -----------------------------
    # STRESS DETECTION
    # -----------------------------
    stress = None
    stress_key = None

    for key in mesh.point_data.keys():
        key_lower = key.lower()
        if "stress" in key_lower or "tresca" in key_lower or "von" in key_lower:
            stress = mesh.point_data[key]
            stress_key = key
            break

    if stress is None:
        output.append("\n⚠️ No stress field detected")
        return "\n".join(output)

    output.append(f"\nDetected stress field: {stress_key}")

    stress = np.array(stress)

    if len(stress.shape) > 1:
        stress = np.linalg.norm(stress, axis=1)

    # -----------------------------
    # METRICS
    # -----------------------------
    max_stress = np.max(stress)
    mean_stress = np.mean(stress)
    min_stress = np.min(stress)

    output.append(f"\nMaximum stress: {round(max_stress, 2)} MPa")
    output.append(f"Mean stress: {round(mean_stress, 2)} MPa")
    output.append(f"Minimum stress: {round(min_stress, 2)} MPa")

    # -----------------------------
    # CRITICAL ZONES
    # -----------------------------
    threshold = np.percentile(stress, 95)
    num_critical = int(np.sum(stress >= threshold))

    output.append(f"\nCritical points (top 5% stress): {num_critical}")

    # -----------------------------
    # GRADIENT
    # -----------------------------
    gradients = []

    for i in range(len(points) - 1):
        dist = np.linalg.norm(points[i] - points[i+1])
        if dist > 0:
            gradients.append(abs(stress[i] - stress[i+1]) / dist)

    max_gradient = max(gradients) if gradients else 0
    output.append(f"Maximum stress gradient: {round(max_gradient, 2)}")

    # -----------------------------
    # ENGINEERING ASSESSMENT
    # -----------------------------
    output.append("\n=== ENGINEERING ASSESSMENT ===")

    if max_stress > mean_stress * 3:
        output.append("⚠️ High stress concentration detected")

    if max_gradient > mean_stress:
        output.append("⚠️ Significant stress gradient — possible geometric discontinuity")

    if yield_limit is not None:
        if max_stress > yield_limit:
            output.append("🚨 Yield strength exceeded — potential failure risk")
        else:
            output.append("✔ Stress levels within elastic limit")

    return "\n".join(output)

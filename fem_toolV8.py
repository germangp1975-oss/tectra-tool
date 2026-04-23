import meshio
import numpy as np
import io

def analyze_file(file, yield_limit=None):
    try:
        file_buffer = io.BytesIO(file.read())
        mesh = meshio.read(file_buffer, file_format="vtu")
    except Exception as e:
        return f"File reading error: {str(e)}"

    output = []
    output.append("=== TECTRA FEM TOOL V8 — Structural Decision Engine ===\n")

    points = mesh.points
    output.append(f"Number of nodes: {len(points)}")

    if not mesh.point_data:
        output.append("\n⚠️ No nodal data fields available")
        return "\n".join(output)

    output.append("\nAvailable data fields:")
    for key in mesh.point_data.keys():
        output.append(f" - {key}")

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

    max_stress = np.max(stress)
    mean_stress = np.mean(stress)
    min_stress = np.min(stress)

    output.append(f"\nMaximum stress: {round(max_stress, 2)} MPa")
    output.append(f"Mean stress: {round(mean_stress, 2)} MPa")
    output.append(f"Minimum stress: {round(min_stress, 2)} MPa")

    threshold = np.percentile(stress, 95)
    critical_mask = stress >= threshold
    num_critical = np.sum(critical_mask)

    output.append(f"\nCritical points (top 5% stress): {int(num_critical)}")

    gradients = []
    for i in range(len(points) - 1):
        dist = np.linalg.norm(points[i] - points[i+1])
        if dist > 0:
            gradients.append(abs(stress[i] - stress[i+1]) / dist)

    max_gradient = max(gradients) if gradients else 0
    output.append(f"Maximum stress gradient: {round(max_gradient, 2)}")

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

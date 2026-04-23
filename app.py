import meshio
import numpy as np

def analyze_file(file_path, yield_limit=None):

    try:
        try:
            # intento estándar
            mesh = meshio.read(file_path)

        except Exception:
            # fallback forzando formato VTU
            mesh = meshio.read(file_path, file_format="vtu")

    except Exception as e:
        return f"File reading error: {str(e)}"

    output = []
    output.append("=== TECTRA FEM TOOL V8 — Engineering Decision Engine ===\n")

    # NODES
    try:
        points = mesh.points
        output.append(f"Number of nodes: {len(points)}")
    except:
        output.append("No node data found")
        return "\n".join(output)

    # STRESS DETECTION
    stress = None

    for key in mesh.point_data.keys():
        if "stress" in key.lower() or "von" in key.lower():
            stress = mesh.point_data[key]
            break

    if stress is None:
        return "No stress field found in file"

    # if tensor → convert to magnitude
    if len(stress.shape) > 1:
        stress = np.linalg.norm(stress, axis=1)

    max_stress = float(np.max(stress))
    mean_stress = float(np.mean(stress))

    output.append(f"Max stress: {max_stress:.2f}")
    output.append(f"Mean stress: {mean_stress:.2f}")

    # CRITICAL ZONE
    threshold = np.percentile(stress, 95)
    critical_points = np.sum(stress >= threshold)

    output.append(f"Critical points (top 5%): {critical_points}")

    # GRADIENT
    coords = points
    gradients = []

    for i in range(len(coords) - 1):
        dist = np.linalg.norm(coords[i] - coords[i+1])
        if dist > 0:
            gradients.append(abs(stress[i] - stress[i+1]) / dist)

    max_gradient = max(gradients) if gradients else 0
    output.append(f"Max stress gradient: {max_gradient:.2f}")

    # ENGINEERING DECISION
    output.append("\n=== ENGINEERING DECISION ===")

    if max_stress > mean_stress * 3:
        output.append("Stress concentration detected")

    if yield_limit:
        if max_stress > yield_limit:
            output.append("Material failure risk: yield exceeded")
        else:
            output.append("Within elastic range")

    return "\n".join(output)

import meshio
import numpy as np

def analyze_file(file_path, yield_limit=None):

    try:
        mesh = meshio.read(file_path)
    except Exception as e:
        return f"File reading error: {str(e)}"

    result = []
    result.append("=== TECTRA FEM TOOL V8 — Engineering Decision Engine ===\n")

    points = mesh.points
    n_nodes = len(points)

    result.append(f"Number of nodes: {n_nodes}")

    if not mesh.point_data:
        result.append("No point data found in file.")
        return "\n".join(result)

    available_fields = list(mesh.point_data.keys())

    result.append("\nAvailable fields:")
    for f in available_fields:
        result.append(f" - {f}")

    # Try common stress field names
    stress_field = None
    for key in available_fields:
        if "stress" in key.lower():
            stress_field = key
            break

    if stress_field is None:
        result.append("\nNo stress field detected.")
        return "\n".join(result)

    stress = mesh.point_data[stress_field]

    if stress.ndim > 1:
        stress = np.linalg.norm(stress, axis=1)

    max_stress = np.max(stress)
    mean_stress = np.mean(stress)

    result.append(f"\nMax stress: {max_stress:.2f}")
    result.append(f"Mean stress: {mean_stress:.2f}")

    threshold = np.percentile(stress, 95)
    critical_points = np.sum(stress >= threshold)

    result.append(f"Critical points (top 5%): {critical_points}")

    # Gradient estimation
    gradients = []

    for i in range(len(points) - 1):
        dist = np.linalg.norm(points[i] - points[i+1])
        if dist > 0:
            gradients.append(abs(stress[i] - stress[i+1]) / dist)

    max_gradient = max(gradients) if gradients else 0
    result.append(f"Max stress gradient: {max_gradient:.2f}")

    result.append("\n=== ENGINEERING INTERPRETATION ===")

    if max_stress > mean_stress * 3:
        result.append("Stress concentration detected")

    if yield_limit:
        if max_stress > yield_limit:
            result.append("Yield limit exceeded")

    return "\n".join(result)

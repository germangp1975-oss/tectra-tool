import meshio
import numpy as np

def analyze_file(file_path, yield_limit=None):

    # Robust reading (handles VTU variations better)
    try:
        try:
            mesh = meshio.read(file_path)
        except Exception:
            mesh = meshio.read(file_path, file_format="vtu")
    except Exception as e:
        return f"File reading error: {str(e)}"

    result = []
    result.append("=== TECTRA FEM TOOL V8 — Engineering Decision Engine ===\n")

    # Nodes
    try:
        points = mesh.points
        n_nodes = len(points)
        result.append(f"Number of nodes: {n_nodes}")
    except Exception:
        return "Error: Unable to read node data."

    # Check data
    if not mesh.point_data:
        result.append("No point data found in file.")
        return "\n".join(result)

    available_fields = list(mesh.point_data.keys())

    result.append("\nAvailable fields:")
    for f in available_fields:
        result.append(f" - {f}")

    # Detect stress field automatically
    stress_field = None
    for key in available_fields:
        k = key.lower()
        if "stress" in k or "von" in k:
            stress_field = key
            break

    if stress_field is None:
        result.append("\nNo stress field detected.")
        return "\n".join(result)

    # Extract stress
    stress = mesh.point_data[stress_field]

    # Convert tensor → magnitude if needed
    if hasattr(stress, "ndim") and stress.ndim > 1:
        stress = np.linalg.norm(stress, axis=1)

    stress = np.array(stress, dtype=float)

    # Basic metrics
    max_stress = float(np.max(stress))
    mean_stress = float(np.mean(stress))

    result.append(f"\nMax stress: {max_stress:.2f}")
    result.append(f"Mean stress: {mean_stress:.2f}")

    # Critical zone
    threshold = np.percentile(stress, 95)
    critical_points = int(np.sum(stress >= threshold))

    result.append(f"Critical points (top 5%): {critical_points}")

    # Gradient estimation
    gradients = []
    for i in range(len(points) - 1):
        dist = np.linalg.norm(points[i] - points[i + 1])
        if dist > 0:
            gradients.append(abs(stress[i] - stress[i + 1]) / dist)

    max_gradient = max(gradients) if gradients else 0.0
    result.append(f"Max stress gradient: {max_gradient:.2f}")

    # Engineering interpretation
    result.append("\n=== ENGINEERING INTERPRETATION ===")

    if max_stress > mean_stress * 3:
        result.append("Stress concentration detected")

    if yield_limit:
        try:
            yl = float(yield_limit)
            if max_stress > yl:
                result.append("Yield limit exceeded")
            else:
                result.append("Within elastic range")
        except Exception:
            result.append("Invalid yield limit input")

    return "\n".join(result)

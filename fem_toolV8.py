import meshio
import numpy as np

def analyze_file(file_path, yield_limit=None):
    try:
        mesh = meshio.read(file_path)
    except Exception as e:
        return f"File reading error: {str(e)}"

    output = []
    output.append("=== TECTRA FEM Tool V8 — Engineering Decision Engine ===\n")

    # Nodes
    points = mesh.points
    output.append(f"Number of nodes: {len(points)}")

    # Available fields
    fields = mesh.point_data.keys()
    output.append("\nAvailable fields:")
    for f in fields:
        output.append(f" - {f}")

    # Automatic stress field detection
    stress_field = None
    for key in fields:
        if "stress" in key.lower() or "tresca" in key.lower():
            stress_field = key
            break

    if stress_field is None:
        return "No stress field detected in the file."

    stress = mesh.point_data[stress_field]

    # Ensure scalar field
    if len(stress.shape) > 1:
        stress = np.linalg.norm(stress, axis=1)

    # Metrics
    max_stress = np.max(stress)
    mean_stress = np.mean(stress)
    std_stress = np.std(stress)

    output.append("\n=== METRICS ===")
    output.append(f"Max stress: {round(max_stress, 2)}")
    output.append(f"Mean stress: {round(mean_stress, 2)}")
    output.append(f"Std stress: {round(std_stress, 2)}")

    # Critical zones
    threshold = np.percentile(stress, 95)
    critical = stress >= threshold
    num_critical = np.sum(critical)

    output.append(f"\nCritical points (top 5%): {num_critical}")

    # Gradient estimation
    gradients = []
    for i in range(len(points) - 1):
        dist = np.linalg.norm(points[i] - points[i + 1])
        if dist > 0:
            gradients.append(abs(stress[i] - stress[i + 1]) / dist)

    max_gradient = max(gradients) if gradients else 0
    output.append(f"Max gradient: {round(max_gradient, 2)}")

    # Decision engine
    output.append("\n=== DIAGNOSTIC ===")

    if max_stress > mean_stress * 3:
        output.append("High stress concentration detected")

    if yield_limit:
        if max_stress > yield_limit:
            output.append("Yield limit exceeded")
        else:
            output.append("Within elastic limit")

    if max_gradient > 100:
        output.append("Abrupt stress variation detected (possible notch effect)")

    if num_critical < len(stress) * 0.02:
        output.append("Highly localized stress concentration")
    else:
        output.append("More uniform stress distribution")

    return "\n".join(output)
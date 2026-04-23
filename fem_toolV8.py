import meshio
import numpy as np
import os

def analyze_file(file_path, yield_strength=None):

    output = []

    def log(txt):
        output.append(str(txt))

    log("=== FEM TOOL V8 — Engineering Decision Engine ===")

    # -----------------------------
    # VALIDATION
    # -----------------------------
    if not os.path.exists(file_path):
        return "ERROR: File not found"

    mesh = meshio.read(file_path)
    points = mesh.points
    num_nodes = len(points)

    log(f"Number of nodes: {num_nodes}")

    # -----------------------------
    # STRESS FIELD
    # -----------------------------
    stress = None
    field_name = None

    for key in mesh.point_data.keys():
        name = key.lower()
        if "tresca" in name or "mises" in name:
            stress = mesh.point_data[key]
            field_name = key
            break

    if stress is None:
        return "ERROR: Stress field not found"

    log(f"Using field: {field_name}")

    stress = np.array(stress)
    if len(stress.shape) > 1:
        stress = np.linalg.norm(stress, axis=1)
    stress = stress.flatten()

    # -----------------------------
    # FILTERING
    # -----------------------------
    p_low = np.quantile(stress, 0.01)
    p_high = np.quantile(stress, 0.99)
    stress_filtered = stress[(stress >= p_low) & (stress <= p_high)]

    # -----------------------------
    # STATISTICS
    # -----------------------------
    max_stress = np.max(stress)
    mean_stress = np.mean(stress_filtered)
    min_stress = np.min(stress)

    ratio = max_stress / mean_stress

    log("\n--- STATISTICS ---")
    log(f"Max stress: {max_stress:.3f}")
    log(f"Mean stress: {mean_stress:.3f}")
    log(f"Min stress: {min_stress:.3f}")
    log(f"Max/mean ratio: {ratio:.2f}")

    # -----------------------------
    # CRITICAL POINTS
    # -----------------------------
    threshold = np.quantile(stress, 0.95)
    critical_indices = np.where(stress >= threshold)[0]
    critical_points = points[critical_indices]

    num_critical = len(critical_indices)
    percentage = num_critical / num_nodes

    log("\n--- CRITICAL REGIONS ---")
    log(f"Critical points: {num_critical}")
    log(f"Critical percentage: {percentage*100:.2f}%")

    # -----------------------------
    # LOCATION
    # -----------------------------
    centroid = None
    max_point = None

    if len(critical_points) > 0:
        centroid = np.mean(critical_points, axis=0)
        max_point = points[np.argmax(stress)]

    # -----------------------------
    # SPATIAL NORMALIZATION
    # -----------------------------
    bbox = np.max(points, axis=0) - np.min(points, axis=0)
    size = np.linalg.norm(bbox)

    # -----------------------------
    # SPREAD
    # -----------------------------
    spread_norm = 0
    if len(critical_points) > 2:
        centroid_tmp = np.mean(critical_points, axis=0)
        distances = np.linalg.norm(critical_points - centroid_tmp, axis=1)
        spread = np.mean(distances)
        spread_norm = spread / size if size > 0 else 0

    log("\n--- DISTRIBUTION ---")
    log(f"Normalized spread: {spread_norm:.5f}")

    # -----------------------------
    # GRADIENT
    # -----------------------------
    gradients = []
    step = max(1, int(len(points) / 2000))

    for i in range(0, len(points) - step, step):
        d = np.linalg.norm(points[i] - points[i + step])
        if d > 0:
            gradients.append(abs(stress[i] - stress[i + step]) / d)

    max_gradient = max(gradients) if gradients else 0
    gradient_norm = max_gradient / max_stress if max_stress > 0 else 0

    log("\n--- GRADIENT ---")
    log(f"Normalized gradient: {gradient_norm:.3f}")

    # -----------------------------
    # CLASSIFICATION
    # -----------------------------
    if ratio < 1.5:
        structure_type = "Uniform stress distribution"

    elif ratio > 2:
        if percentage < 0.08:
            structure_type = "Localized stress concentration (NOTCH)"
        elif spread_norm > 0.08:
            structure_type = "Distributed concentration (HOLE)"
        else:
            structure_type = "Complex critical region"

    else:
        structure_type = "Structural transition (SECTION CHANGE)"

    # -----------------------------
    # GEOMETRIC RISK
    # -----------------------------
    if ratio > 3 or gradient_norm > 5:
        geometric_risk = "HIGH"
    elif ratio > 1.5:
        geometric_risk = "MEDIUM"
    else:
        geometric_risk = "LOW"

    # -----------------------------
    # SAFETY FACTOR
    # -----------------------------
    safety_factor = None
    structural_risk = "UNKNOWN"

    if yield_strength is not None:
        safety_factor = yield_strength / (max_stress / 1e6)

        if safety_factor < 1.5:
            structural_risk = "HIGH"
        elif safety_factor < 3:
            structural_risk = "MEDIUM"
        else:
            structural_risk = "LOW"

    # -----------------------------
    # FINAL DECISION
    # -----------------------------
    if safety_factor is not None:
        if safety_factor < 1.5:
            decision = "NOT ACCEPTABLE"
        elif geometric_risk in ["HIGH", "MEDIUM"]:
            decision = "REVIEW"
        else:
            decision = "ACCEPTABLE"
    else:
        decision = "REVIEW" if geometric_risk != "LOW" else "ACCEPTABLE"

    # -----------------------------
    # CONFIDENCE
    # -----------------------------
    if num_nodes > 2000:
        confidence = "HIGH"
    elif num_nodes > 500:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    # -----------------------------
    # OUTPUT
    # -----------------------------
    log("\n=== DIAGNOSIS ===")
    log(f"Type: {structure_type}")

    log("\n=== LOCATION ===")
    if centroid is not None:
        log(f"Critical centroid: {centroid}")
    if max_point is not None:
        log(f"Maximum stress point: {max_point}")

    log("\n=== RISK ANALYSIS ===")
    log(f"Geometric risk: {geometric_risk}")
    log(f"Structural risk: {structural_risk}")

    log("\n=== ENGINEERING DECISION ===")
    log(f"Result: {decision}")

    if safety_factor is not None:
        log(f"Safety factor: {safety_factor:.2f}")

    log(f"Confidence: {confidence}")

    log("\n=== RECOMMENDATIONS ===")

    if decision == "NOT ACCEPTABLE":
        log("- Immediate redesign required")
    elif decision == "REVIEW":
        log("- Optimize geometry")
        log("- Reduce stress concentrations")
    else:
        log("- Design acceptable")

    log("\nAnalysis complete")

    return "\n".join(output)

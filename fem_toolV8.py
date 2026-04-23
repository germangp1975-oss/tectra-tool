import meshio
import numpy as np
import os


def analyze_file(file_path, yield_strength=None):
    # -----------------------------
    # VALIDATION
    # -----------------------------
    if not os.path.exists(file_path):
        return {"error": "File not found"}

    try:
        mesh = meshio.read(file_path)
    except Exception as e:
        return {"error": f"Error reading file: {str(e)}"}

    points = mesh.points
    num_nodes = len(points)

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
        return {"error": "Stress field not found (Tresca or Mises required)"}

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
    max_stress = float(np.max(stress))
    mean_stress = float(np.mean(stress_filtered))
    min_stress = float(np.min(stress))

    ratio = max_stress / mean_stress if mean_stress != 0 else 0

    # -----------------------------
    # CRITICAL POINTS
    # -----------------------------
    threshold = np.quantile(stress, 0.95)
    critical_indices = np.where(stress >= threshold)[0]
    critical_points = points[critical_indices]

    num_critical = len(critical_indices)
    percentage = num_critical / num_nodes if num_nodes > 0 else 0

    # -----------------------------
    # LOCATION
    # -----------------------------
    centroid = None
    max_point = None

    if len(critical_points) > 0:
        centroid = np.mean(critical_points, axis=0).tolist()
        max_point = points[np.argmax(stress)].tolist()

    # -----------------------------
    # SPATIAL NORMALIZATION
    # -----------------------------
    bbox = np.max(points, axis=0) - np.min(points, axis=0)
    size = np.linalg.norm(bbox)

    # -----------------------------
    # SPREAD
    # -----------------------------
    spread_norm = 0
    if len(critical_points) > 2 and size > 0:
        centroid_tmp = np.mean(critical_points, axis=0)
        distances = np.linalg.norm(critical_points - centroid_tmp, axis=1)
        spread = np.mean(distances)
        spread_norm = spread / size

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
        try:
            # stress assumed in Pa → convert to MPa
            safety_factor = yield_strength / (max_stress / 1e6)

            if safety_factor < 1.5:
                structural_risk = "HIGH"
            elif safety_factor < 3:
                structural_risk = "MEDIUM"
            else:
                structural_risk = "LOW"
        except:
            safety_factor = None
            structural_risk = "UNKNOWN"

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
    return {
        "num_nodes": num_nodes,
        "field_used": field_name,
        "max_stress": max_stress,
        "mean_stress": mean_stress,
        "min_stress": min_stress,
        "ratio": ratio,
        "critical_points": num_critical,
        "critical_percentage": percentage,
        "centroid": centroid,
        "max_point": max_point,
        "spread_norm": spread_norm,
        "gradient_norm": gradient_norm,
        "structure_type": structure_type,
        "geometric_risk": geometric_risk,
        "structural_risk": structural_risk,
        "safety_factor": safety_factor,
        "decision": decision,
        "confidence": confidence
    }

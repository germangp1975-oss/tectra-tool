import meshio
import numpy as np

def analyze_file(file_path, yield_limit=None):

    try:
        mesh = meshio.read(file_path)
    except Exception as e:
        return f"File reading error: {str(e)}"

    result = []
    result.append("=== TECTRA V9 — Structural Insight Engine ===\n")

    # -------------------------
    # BASIC DATA
    # -------------------------
    points = mesh.points
    n_nodes = len(points)

    result.append(f"Number of nodes: {n_nodes}")

    if not mesh.point_data:
        result.append("No point data available in file.")
        return "\n".join(result)

    available_fields = list(mesh.point_data.keys())

    # -------------------------
    # DETECT STRESS FIELD
    # -------------------------
    stress_field = None
    for key in available_fields:
        if "mises" in key.lower():
            stress_field = key
            break

    if stress_field is None:
        for key in available_fields:
            if "stress" in key.lower():
                stress_field = key
                break

    if stress_field is None:
        result.append("No stress field detected.")
        return "\n".join(result)

    stress = mesh.point_data[stress_field]

    if stress.ndim > 1:
        stress = np.linalg.norm(stress, axis=1)

    # -------------------------
    # METRICS
    # -------------------------
    max_stress = float(np.max(stress))
    mean_stress = float(np.mean(stress))
    ratio = max_stress / (mean_stress + 1e-9)

    threshold = np.percentile(stress, 95)
    critical_mask = stress >= threshold
    critical_points_count = int(np.sum(critical_mask))

    # -------------------------
    # LOCATION (CRITICAL POINT)
    # -------------------------
    max_index = int(np.argmax(stress))
    critical_point = points[max_index]

    # -------------------------
    # GRADIENT
    # -------------------------
    gradients = []
    for i in range(len(points) - 1):
        dist = np.linalg.norm(points[i] - points[i+1])
        if dist > 0:
            gradients.append(abs(stress[i] - stress[i+1]) / dist)

    max_gradient = max(gradients) if gradients else 0

    # -------------------------
    # RISK LEVEL
    # -------------------------
    if ratio < 1.5:
        risk = "LOW"
    elif ratio < 3:
        risk = "MEDIUM"
    else:
        risk = "HIGH"

    if yield_limit and max_stress > yield_limit:
        risk = "CRITICAL"

    # -------------------------
    # FAILURE MODE
    # -------------------------
    if max_gradient > mean_stress:
        failure_mode = "Localized stress concentration (notch / hole / sharp transition)"
    elif ratio > 2:
        failure_mode = "Geometric stress amplification"
    else:
        failure_mode = "Distributed loading (no dominant geometric effect)"

    # -------------------------
    # FAILURE ORIGIN
    # -------------------------
    if yield_limit and max_stress > yield_limit:
        failure_origin = "Material yielding"
    elif ratio > 2:
        failure_origin = "Geometry-driven stress amplification"
    else:
        failure_origin = "Load distribution behavior"

    # -------------------------
    # FATIGUE ESTIMATION (APPROX)
    # -------------------------
    fatigue_indicator = ratio

    if fatigue_indicator > 2:
        fatigue_risk = "HIGH fatigue risk"
    elif fatigue_indicator > 1.5:
        fatigue_risk = "MODERATE fatigue risk"
    else:
        fatigue_risk = "LOW fatigue risk"

    # -------------------------
    # STRUCTURAL SCORE (0-100)
    # -------------------------
    score = max(0, 100 - (ratio * 20 + (max_gradient / (mean_stress + 1e-9)) * 10))
    score = min(100, score)

    # -------------------------
    # ENGINEERING ACTIONS
    # -------------------------
    actions = []

    if ratio > 2:
        actions.append("Smooth geometry transitions")

    if max_gradient > mean_stress:
        actions.append("Increase fillet radius")

    if yield_limit and max_stress > yield_limit:
        actions.append("Increase material strength or section thickness")

    if fatigue_indicator > 1.5:
        actions.append("Reduce cyclic stress amplitude")

    if not actions:
        actions.append("Design within acceptable limits")

    # -------------------------
    # REPORT
    # -------------------------
    result.append("\nSTRUCTURAL SCORE")
    result.append(f"Score: {score:.1f} / 100")
    result.append(f"Risk Level: {risk}")

    result.append("\nKEY METRICS")
    result.append(f"Max stress: {max_stress:.2f}")
    result.append(f"Mean stress: {mean_stress:.2f}")
    result.append(f"Critical points (top 5%): {critical_points_count}")
    result.append(f"Max stress gradient: {max_gradient:.2f}")

    result.append("\nCRITICAL LOCATION")
    result.append(f"x: {critical_point[0]:.3f}, y: {critical_point[1]:.3f}, z: {critical_point[2]:.3f}")

    result.append("\nFAILURE MODE")
    result.append(failure_mode)

    result.append("\nFAILURE ORIGIN")
    result.append(failure_origin)

    result.append("\nFATIGUE ASSESSMENT")
    result.append(fatigue_risk)

    result.append("\nENGINEERING RECOMMENDATIONS")
    for a in actions:
        result.append(f"- {a}")

    result.append("\nSTATUS")
    result.append("Analysis completed successfully")

    return "\n".join(result)

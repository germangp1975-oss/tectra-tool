import meshio
import numpy as np


def analyze_file(file_path, yield_limit=None):

    try:
        try:
            mesh = meshio.read(file_path)
        except:
            mesh = meshio.read(file_path, file_format="vtu")
    except Exception as e:
        return {"error": f"File reading error: {str(e)}"}

    points = mesh.points

    if not mesh.point_data:
        return {"error": "No point data found in file."}

    available_fields = list(mesh.point_data.keys())

    # --- STRESS FIELD ---
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
        return {"error": "No stress field detected."}

    stress = mesh.point_data[stress_field]

    if stress.ndim > 1:
        stress = np.linalg.norm(stress, axis=1)

    stress = np.array(stress, dtype=float)

    # --- METRICS ---
    max_stress = float(np.max(stress))
    mean_stress = float(np.mean(stress))

    ratio = max_stress / mean_stress if mean_stress > 0 else 0

    threshold = np.percentile(stress, 95)
    critical_points = int(np.sum(stress >= threshold))

    # --- GRADIENT ---
    gradients = []
    for i in range(len(points) - 1):
        dist = np.linalg.norm(points[i] - points[i + 1])
        if dist > 0:
            gradients.append(abs(stress[i] - stress[i + 1]) / dist)

    max_gradient = max(gradients) if gradients else 0.0

    # --- SCORE (0-100) ---
    score = 100

    score -= min(ratio * 10, 40)
    score -= min((max_gradient / (mean_stress + 1e-6)) * 10, 30)

    if yield_limit:
        yl = float(yield_limit)
        if max_stress > yl:
            score -= 30

    score = max(0, round(score, 1))

    # --- RISK LEVEL ---
    if score > 75:
        risk = "LOW"
    elif score > 50:
        risk = "MEDIUM"
    elif score > 25:
        risk = "HIGH"
    else:
        risk = "CRITICAL"

    # --- FAILURE MODE ---
    if ratio > 4 and max_gradient > mean_stress:
        failure = "Localized stress concentration (notch / hole)"
    elif ratio > 2:
        failure = "Geometric transition issue"
    else:
        failure = "No critical failure pattern detected"

    # --- ACTIONS ---
    actions = []

    if ratio > 3:
        actions.append("Smooth geometry transitions")
        actions.append("Increase fillet radius")

    if max_gradient > mean_stress:
        actions.append("Improve load path continuity")

    if yield_limit and max_stress > yield_limit:
        actions.append("Increase material strength or section thickness")

    return {
        "nodes": len(points),
        "max_stress": max_stress,
        "mean_stress": mean_stress,
        "critical_points": critical_points,
        "gradient": max_gradient,
        "score": score,
        "risk": risk,
        "failure": failure,
        "actions": actions
    }
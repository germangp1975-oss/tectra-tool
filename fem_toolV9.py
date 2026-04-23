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

    # --- STRESS FIELD DETECTION ---
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

    # --- BASIC METRICS ---
    max_stress = float(np.max(stress))
    mean_stress = float(np.mean(stress))
    ratio = max_stress / mean_stress if mean_stress > 0 else 0

    threshold = np.percentile(stress, 95)
    critical_mask = stress >= threshold
    critical_points = int(np.sum(critical_mask))

    # --- HOTSPOT ---
    idx_max = np.argmax(stress)
    hotspot = points[idx_max]

    # --- GRADIENT ---
    gradients = []
    for i in range(len(points) - 1):
        dist = np.linalg.norm(points[i] - points[i + 1])
        if dist > 0:
            gradients.append(abs(stress[i] - stress[i + 1]) / dist)

    max_gradient = max(gradients) if gradients else 0.0

    # --- SCORE ---
    score = 100
    score -= min(ratio * 10, 40)
    score -= min((max_gradient / (mean_stress + 1e-6)) * 10, 30)

    if yield_limit:
        yl = float(yield_limit)
        if max_stress > yl:
            score -= 30

    score = max(0, round(score, 1))

    # --- RISK ---
    if score > 75:
        risk = "LOW"
    elif score > 50:
        risk = "MEDIUM"
    elif score > 25:
        risk = "HIGH"
    else:
        risk = "CRITICAL"

    # --- SEVERITY ---
    if ratio > 4:
        severity = "EXTREME"
    elif ratio > 3:
        severity = "SEVERE"
    elif ratio > 2:
        severity = "MODERATE"
    else:
        severity = "LOW"

    # --- FAILURE TYPE ---
    if ratio > 4 and max_gradient > mean_stress:
        failure = "Localized geometric discontinuity (notch / hole / sharp transition)"
        origin = "GEOMETRIC"
    elif ratio > 2:
        failure = "Load redistribution / section transition issue"
        origin = "STRUCTURAL"
    else:
        failure = "No dominant failure mechanism"
        origin = "UNDEFINED"

    # --- FATIGUE RISK (heuristic) ---
    fatigue_risk = "LOW"

    if ratio > 3 and max_gradient > mean_stress:
        fatigue_risk = "HIGH"
    elif ratio > 2:
        fatigue_risk = "MODERATE"

    # --- ACTIONS ---
    actions = []

    if origin == "GEOMETRIC":
        actions.append("Smooth geometric discontinuities")
        actions.append("Increase fillet radii")
        actions.append("Avoid sharp transitions")

    if origin == "STRUCTURAL":
        actions.append("Improve load distribution")
        actions.append("Reinforce critical sections")

    if fatigue_risk != "LOW":
        actions.append("Check fatigue life under cyclic loading")
        actions.append("Reduce stress concentration zones")

    if yield_limit and max_stress > yield_limit:
        actions.append("Material yielding expected — redesign required")

    # --- RETURN ---
    return {
        "nodes": len(points),
        "max_stress": max_stress,
        "mean_stress": mean_stress,
        "ratio": ratio,
        "critical_points": critical_points,
        "gradient": max_gradient,
        "score": score,
        "risk": risk,
        "severity": severity,
        "failure": failure,
        "origin": origin,
        "fatigue_risk": fatigue_risk,
        "hotspot": hotspot.tolist(),
        "actions": actions,
        "status": "Analysis complete"
    }
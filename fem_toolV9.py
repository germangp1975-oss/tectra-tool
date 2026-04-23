import meshio
import numpy as np

def analyze_file(file_path, yield_limit=None):

    try:
        mesh = meshio.read(file_path)
    except Exception as e:
        return {"error": f"File reading error: {str(e)}"}

    points = mesh.points
    n_nodes = len(points)

    if not mesh.point_data:
        return {"error": "No point data available"}

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
        return {"error": "No stress field detected"}

    stress = mesh.point_data[stress_field]

    if stress.ndim > 1:
        stress = np.linalg.norm(stress, axis=1)

    # -------------------------
    # UNIDADES → MPa
    # -------------------------
    stress = stress / 1e6

    # -------------------------
    # METRICS
    # -------------------------
    max_stress = float(np.max(stress))
    mean_stress = float(np.mean(stress))

    threshold = np.percentile(stress, 95)
    critical_mask = stress >= threshold
    critical_points_count = int(np.sum(critical_mask))

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
    # FACTOR DE SEGURIDAD
    # -------------------------
    if yield_limit:
        FoS = yield_limit / (max_stress + 1e-9)
    else:
        FoS = None

    if FoS is not None:
        if FoS > 2:
            fos_level = "SAFE"
        elif FoS > 1.2:
            fos_level = "MARGINAL"
        elif FoS > 1:
            fos_level = "AT RISK"
        else:
            fos_level = "FAILURE"
    else:
        fos_level = "UNKNOWN"

    # -------------------------
    # NUEVAS MÉTRICAS CLAVE
    # -------------------------
    stress_ratio = max_stress / (mean_stress + 1e-9)
    gradient_ratio = max_gradient / (max_stress + 1e-9)

    # -------------------------
    # STRUCTURAL SCORE REAL
    # -------------------------
    if FoS is not None:
        material_score = min(100, FoS * 40)
    else:
        material_score = 50

    penalty_stress = min(40, (stress_ratio - 1) * 20)
    penalty_gradient = min(30, gradient_ratio * 50)

    structural_score = material_score - penalty_stress - penalty_gradient
    score = max(0, min(100, structural_score))

    # -------------------------
    # FAILURE MODE
    # -------------------------
    if FoS is not None and FoS < 1:
        failure_mode = "STATIC FAILURE (yielding)"
    elif yield_limit and max_stress > 0.6 * yield_limit:
        failure_mode = "FATIGUE RISK ZONE"
    else:
        failure_mode = "ELASTIC BEHAVIOR"

    # -------------------------
    # GEOMETRIC DETECTION
    # -------------------------
    if max_gradient > (max_stress * 0.3):
        geom_flag = "Stress concentration consistent with geometric discontinuity"
    else:
        geom_flag = "No dominant geometric stress concentration"

    # -------------------------
    # RISK BASADO EN SCORE
    # -------------------------
    if score > 85:
        risk = "LOW"
    elif score > 60:
        risk = "MODERATE"
    elif score > 40:
        risk = "HIGH"
    else:
        risk = "CRITICAL"

    # -------------------------
    # ACTIONS
    # -------------------------
    actions = []

    if geom_flag != "No dominant geometric stress concentration":
        actions.append("Smooth geometry transitions / increase fillet radius")

    if FoS is not None and FoS < 1:
        actions.append("Increase section thickness or material strength")

    if yield_limit and max_stress > 0.6 * yield_limit:
        actions.append("Reduce cyclic loading / assess fatigue design")

    if not actions:
        actions.append("Design within acceptable mechanical limits")

    return {
        "nodes": n_nodes,
        "max_stress": max_stress,
        "mean_stress": mean_stress,
        "critical_points": critical_points_count,
        "max_gradient": max_gradient,
        "location": critical_point,
        "FoS": FoS,
        "fos_level": fos_level,
        "score": score,
        "risk": risk,
        "failure_mode": failure_mode,
        "geom_flag": geom_flag,
        "actions": actions
    }
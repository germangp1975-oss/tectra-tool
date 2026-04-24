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

    # DETECT STRESS FIELD
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

    # UNIDADES → MPa
    stress = stress / 1e6

    # METRICS
    max_stress = float(np.max(stress))
    mean_stress = float(np.mean(stress) + 1e-9)

    threshold = np.percentile(stress, 95)
    critical_mask = stress >= threshold
    critical_points_count = int(np.sum(critical_mask))

    max_index = int(np.argmax(stress))
    critical_point = points[max_index]

    # GRADIENT
    gradients = []
    for i in range(len(points) - 1):
        dist = np.linalg.norm(points[i] - points[i+1])
        if dist > 0:
            gradients.append(abs(stress[i] - stress[i+1]) / dist)

    max_gradient = max(gradients) if gradients else 0

    # FACTOR DE SEGURIDAD
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

    # MÉTRICAS AVANZADAS
    stress_ratio = max_stress / mean_stress
    gradient_ratio = max_gradient / (max_stress + 1e-9)

    # SCORE ESTRUCTURAL
    if FoS is not None:
        material_score = min(100, FoS * 40)
    else:
        material_score = 50

    penalty_stress = max(0, min(40, (stress_ratio - 1) * 20))
    penalty_gradient = max(0, min(30, gradient_ratio * 50))

    structural_score = material_score - penalty_stress - penalty_gradient
    score = max(0, min(100, structural_score))

    # FATIGA SIMPLIFICADA
    if yield_limit:
        fatigue_ratio = max_stress / yield_limit
    else:
        fatigue_ratio = 0

    if fatigue_ratio > 0.8:
        fatigue_level = "VERY HIGH"
    elif fatigue_ratio > 0.6:
        fatigue_level = "HIGH"
    elif fatigue_ratio > 0.4:
        fatigue_level = "MODERATE"
    else:
        fatigue_level = "LOW"

    # FAILURE MODE AVANZADO
    if FoS is not None and FoS < 1:
        failure_mode = "STATIC FAILURE (yielding)"
    elif stress_ratio > 3:
        failure_mode = "GEOMETRIC FAILURE DRIVER"
    elif fatigue_ratio > 0.6:
        failure_mode = "FATIGUE-DRIVEN RISK"
    else:
        failure_mode = "ELASTIC BEHAVIOR"

    # DETECCIÓN GEOMÉTRICA
    if max_gradient > (max_stress * 0.3):
        geom_flag = "Stress concentration consistent with geometric discontinuity"
    else:
        geom_flag = "No dominant geometric stress concentration"

    # COMPORTAMIENTO ESTRUCTURAL
    if stress_ratio > 3:
        structural_mode = "SEVERE STRESS CONCENTRATION"
    elif stress_ratio > 2:
        structural_mode = "MODERATE STRESS AMPLIFICATION"
    elif gradient_ratio > 0.2:
        structural_mode = "GEOMETRIC DISCONTINUITY EFFECT"
    else:
        structural_mode = "UNIFORM STRESS DISTRIBUTION"

    # RIESGO GLOBAL
    if score > 85:
        risk = "LOW"
    elif score > 60:
        risk = "MODERATE"
    elif score > 40:
        risk = "HIGH"
    else:
        risk = "CRITICAL"

    # -------------------------
    # DECISION LAYER
    # -------------------------
    if score >= 85:
        decision = "ACCEPT"
    elif score >= 60:
        decision = "ACCEPT WITH CAUTION"
    elif score >= 40:
        decision = "REVIEW REQUIRED"
    else:
        decision = "REJECT"

    # PROBLEMA PRINCIPAL
    if failure_mode == "GEOMETRIC FAILURE DRIVER":
        primary_issue = "Geometric stress concentration"
    elif failure_mode == "FATIGUE-DRIVEN RISK":
        primary_issue = "Fatigue risk"
    elif failure_mode == "STATIC FAILURE (yielding)":
        primary_issue = "Material failure risk"
    else:
        primary_issue = "No critical issue"

    # MENSAJE FINAL
    if decision == "ACCEPT":
        conclusion = "Design is structurally efficient and suitable for use"
    elif decision == "ACCEPT WITH CAUTION":
        conclusion = "Design is acceptable but could be improved"
    elif decision == "REVIEW REQUIRED":
        conclusion = f"Design requires review due to {primary_issue.lower()}"
    else:
        conclusion = f"Design not recommended due to {primary_issue.lower()}"

    # ACCIONES
    actions = []

    if geom_flag != "No dominant geometric stress concentration":
        actions.append("Smooth geometry transitions / increase fillet radius")

    if FoS is not None and FoS < 1:
        actions.append("Increase section thickness or material strength")

    if fatigue_ratio > 0.6:
        actions.append("Reduce cyclic loading / redesign for fatigue resistance")

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
        "fatigue_level": fatigue_level,
        "structural_mode": structural_mode,
        "geom_flag": geom_flag,
        "decision": decision,
        "primary_issue": primary_issue,
        "conclusion": conclusion,
        "actions": actions
    }
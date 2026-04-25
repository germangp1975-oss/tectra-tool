import meshio
import numpy as np


# =========================
# VON MISES
# =========================
def compute_von_mises(stress_tensor):
    sxx = stress_tensor[:, 0]
    syy = stress_tensor[:, 1]
    szz = stress_tensor[:, 2]
    sxy = stress_tensor[:, 3]
    sxz = stress_tensor[:, 4]
    syz = stress_tensor[:, 5]

    vm = np.sqrt(
        0.5 * (
            (sxx - syy)**2 +
            (syy - szz)**2 +
            (szz - sxx)**2 +
            6 * (sxy**2 + sxz**2 + syz**2)
        )
    )
    return vm


# =========================
# CLUSTERS CRÍTICOS
# =========================
def compute_clusters(points, stress, threshold_percent=95, distance_factor=0.02):

    threshold = np.percentile(stress, threshold_percent)
    critical_indices = np.where(stress >= threshold)[0]

    if len(critical_indices) == 0:
        return []

    bbox_size = np.max(points, axis=0) - np.min(points, axis=0)
    base_dist = np.linalg.norm(bbox_size) * distance_factor

    clusters = []
    visited = set()

    for idx in critical_indices:
        if idx in visited:
            continue

        cluster = [idx]
        visited.add(idx)
        stack = [idx]

        while stack:
            current = stack.pop()
            current_point = points[current]

            for other_idx in critical_indices:
                if other_idx in visited:
                    continue

                dist = np.linalg.norm(points[other_idx] - current_point)

                if dist < base_dist:
                    cluster.append(other_idx)
                    visited.add(other_idx)
                    stack.append(other_idx)

        clusters.append(cluster)

    return clusters


def analyze_file(file_path, yield_limit=None):

    # =========================
    # CARGA
    # =========================
    try:
        mesh = meshio.read(file_path)
    except Exception as e:
        return {"error": f"File reading error: {str(e)}"}

    points = mesh.points
    n_nodes = len(points)

    if not mesh.point_data:
        return {"error": "No point data available"}

    available_fields = list(mesh.point_data.keys())

    # =========================
    # DETECTAR TENSIONES
    # =========================
    stress = None

    # Buscar von Mises directo
    for key in available_fields:
        if "mises" in key.lower():
            stress = mesh.point_data[key]
            break

    # Si no existe → calcular desde tensor
    if stress is None:
        for key in available_fields:
            data = mesh.point_data[key]
            if isinstance(data, np.ndarray):
                if data.ndim == 2 and data.shape[1] >= 6:
                    try:
                        stress = compute_von_mises(data)
                        break
                    except:
                        continue

    if stress is None:
        return {"error": "No valid stress data found"}

    if isinstance(stress, np.ndarray) and stress.ndim > 1:
        stress = stress[:, 0]

    stress = np.array(stress, dtype=float)

    # =========================
    # DESPLAZAMIENTOS
    # =========================
    displacement = None

    for key in available_fields:
        if "disp" in key.lower():
            data = mesh.point_data[key]
            if isinstance(data, np.ndarray):
                if data.ndim == 2 and data.shape[1] >= 3:
                    displacement = np.linalg.norm(data[:, :3], axis=1)
                    break

    if displacement is None:
        displacement = np.zeros_like(stress)

    # =========================
    # NORMALIZAR UNIDADES
    # =========================
    if np.max(stress) > 1e5:
        stress = stress / 1e6

    # =========================
    # MÉTRICAS
    # =========================
    max_stress = float(np.max(stress))
    mean_stress = float(np.mean(stress) + 1e-9)

    max_disp = float(np.max(displacement))
    mean_disp = float(np.mean(displacement) + 1e-9)

    threshold = np.percentile(stress, 95)
    critical_mask = stress >= threshold
    critical_points_count = int(np.sum(critical_mask))

    max_index = int(np.argmax(stress))
    critical_point = points[max_index]

    p95 = np.percentile(stress, 95)
    p50 = np.percentile(stress, 50)

    stress_ratio = max_stress / (p50 + 1e-9)
    concentration_ratio = p95 / (p50 + 1e-9)

    disp_ratio = max_disp / (mean_disp + 1e-9)

    # =========================
    # CLUSTERS
    # =========================
    clusters = compute_clusters(points, stress)
    num_clusters = len(clusters)
    largest_cluster_size = max([len(c) for c in clusters]) if clusters else 0

    cluster_ratio = largest_cluster_size / n_nodes if n_nodes > 0 else 0

    # =========================
    # FACTOR DE SEGURIDAD
    # =========================
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

    # =========================
    # SCORE
    # =========================
    if FoS is not None:
        material_score = min(100, FoS * 40)
    else:
        material_score = 50

    penalty_stress = max(0, min(40, (stress_ratio - 1) * 15))
    penalty_concentration = max(0, min(30, (concentration_ratio - 1) * 20))
    penalty_disp = max(0, min(20, (disp_ratio - 1) * 10))
    penalty_cluster = max(0, min(20, cluster_ratio * 100))

    structural_score = material_score - penalty_stress - penalty_concentration - penalty_disp - penalty_cluster
    score = max(0, min(100, structural_score))

    # =========================
    # FATIGA
    # =========================
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

    # =========================
    # FAILURE MODE
    # =========================
    if FoS is not None and FoS < 1:
        failure_mode = "STATIC FAILURE (yielding)"
    elif cluster_ratio > 0.05:
        failure_mode = "EXTENDED CRITICAL REGION"
    elif disp_ratio > 3:
        failure_mode = "GLOBAL DEFORMATION ISSUE"
    elif stress_ratio > 3:
        failure_mode = "GEOMETRIC FAILURE DRIVER"
    elif fatigue_ratio > 0.6:
        failure_mode = "FATIGUE-DRIVEN RISK"
    else:
        failure_mode = "ELASTIC BEHAVIOR"

    # =========================
    # GEOMETRÍA
    # =========================
    if concentration_ratio > 2:
        geom_flag = "Stress concentration consistent with geometric discontinuity"
    else:
        geom_flag = "No dominant geometric stress concentration"

    # =========================
    # COMPORTAMIENTO
    # =========================
    if disp_ratio > 3:
        structural_mode = "GLOBAL FLEXIBILITY"
    elif stress_ratio > 3:
        structural_mode = "SEVERE STRESS CONCENTRATION"
    elif stress_ratio > 2:
        structural_mode = "MODERATE STRESS AMPLIFICATION"
    else:
        structural_mode = "UNIFORM STRESS DISTRIBUTION"

    # =========================
    # RIESGO
    # =========================
    if score > 85:
        risk = "LOW"
    elif score > 60:
        risk = "MODERATE"
    elif score > 40:
        risk = "HIGH"
    else:
        risk = "CRITICAL"

    # =========================
    # DECISIÓN
    # =========================
    if score >= 85:
        decision = "ACCEPT"
    elif score >= 60:
        decision = "ACCEPT WITH CAUTION"
    elif score >= 40:
        decision = "REVIEW REQUIRED"
    else:
        decision = "REJECT"

    # =========================
    # PROBLEMA PRINCIPAL
    # =========================
    if failure_mode == "EXTENDED CRITICAL REGION":
        primary_issue = "Large critical stress region"
    elif failure_mode == "GLOBAL DEFORMATION ISSUE":
        primary_issue = "Excessive deformation"
    elif failure_mode == "GEOMETRIC FAILURE DRIVER":
        primary_issue = "Geometric stress concentration"
    elif failure_mode == "FATIGUE-DRIVEN RISK":
        primary_issue = "Fatigue risk"
    elif failure_mode == "STATIC FAILURE (yielding)":
        primary_issue = "Material failure risk"
    else:
        primary_issue = "No critical issue"

    # =========================
    # CONCLUSIÓN
    # =========================
    if decision == "ACCEPT":
        conclusion = "Design is structurally efficient and suitable for use"
    elif decision == "ACCEPT WITH CAUTION":
        conclusion = "Design is acceptable but could be improved"
    elif decision == "REVIEW REQUIRED":
        conclusion = f"Design requires review due to {primary_issue.lower()}"
    else:
        conclusion = f"Design not recommended due to {primary_issue.lower()}"

    # =========================
    # ACCIONES
    # =========================
    actions = []

    if cluster_ratio > 0.05:
        actions.append("Redesign to reduce extended stress concentration region")

    if geom_flag != "No dominant geometric stress concentration":
        actions.append("Smooth geometry transitions / increase fillet radius")

    if disp_ratio > 3:
        actions.append("Increase stiffness / reduce deformation")

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
        "location": critical_point,
        "max_displacement": max_disp,
        "num_critical_clusters": num_clusters,
        "largest_cluster_size": largest_cluster_size,
        "cluster_ratio": cluster_ratio,
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

import meshio
import numpy as np


def analyze_file(file_path, yield_strength=None):
    try:
        mesh = meshio.read(file_path)

        # Buscar campo de tensiones
        stress = None
        for key in mesh.point_data.keys():
            if "stress" in key.lower():
                stress = mesh.point_data[key]
                break

        if stress is None:
            return {"error": "No stress field found in .vtu file"}

        stress = np.array(stress)

        # Si es tensorial, reducir a escalar (norma)
        if len(stress.shape) > 1:
            stress = np.linalg.norm(stress, axis=1)

        max_stress = float(np.max(stress))
        mean_stress = float(np.mean(stress))

        ratio = max_stress / mean_stress if mean_stress != 0 else 0

        threshold = np.percentile(stress, 95)
        critical = stress[stress >= threshold]
        critical_percentage = (len(critical) / len(stress)) * 100

        # Clasificación geométrica
        if ratio < 1.5:
            structure_type = "Uniform"
        elif ratio < 3:
            structure_type = "Moderate concentration"
        else:
            structure_type = "Severe concentration"

        # Riesgo geométrico
        if ratio < 2:
            geometric_risk = "Low"
        elif ratio < 4:
            geometric_risk = "Medium"
        else:
            geometric_risk = "High"

        # Riesgo estructural
        structural_risk = "Unknown"
        safety_factor = None

        if yield_strength and yield_strength > 0:
            safety_factor = yield_strength / max_stress

            if safety_factor > 2:
                structural_risk = "Low"
            elif safety_factor > 1:
                structural_risk = "Medium"
            else:
                structural_risk = "Failure risk"

        # Decisión final
        if structural_risk == "Failure risk" or geometric_risk == "High":
            decision = "REDESIGN REQUIRED"
        elif geometric_risk == "Medium":
            decision = "OPTIMIZATION ADVISED"
        else:
            decision = "STRUCTURE OK"

        # Confianza
        if ratio < 2:
            confidence = "High"
        elif ratio < 4:
            confidence = "Medium"
        else:
            confidence = "Low"

        return {
            "max_stress": max_stress,
            "mean_stress": mean_stress,
            "ratio": ratio,
            "critical_percentage": critical_percentage,
            "structure_type": structure_type,
            "geometric_risk": geometric_risk,
            "structural_risk": structural_risk,
            "safety_factor": safety_factor,
            "decision": decision,
            "confidence": confidence,
        }

    except Exception as e:
        return {"error": str(e)}

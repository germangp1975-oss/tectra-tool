import meshio
import numpy as np

def analyze_file(file, yield_limit=None):
    try:
        # Leer directamente el archivo subido (buffer de Streamlit)
        mesh = meshio.read(file)
    except Exception as e:
        return f"Error leyendo archivo: {str(e)}"

    output = []
    output.append("=== FEM TOOL V8 — Engineering Decision Engine ===\n")

    # -----------------------------
    # NODOS
    # -----------------------------
    points = mesh.points
    output.append(f"Número de nodos: {len(points)}")

    # -----------------------------
    # DATOS DISPONIBLES
    # -----------------------------
    if not mesh.point_data:
        output.append("\n⚠️ No hay datos asociados a los nodos")
        return "\n".join(output)

    output.append("\nCampos disponibles:")
    for key in mesh.point_data.keys():
        output.append(f" - {key}")

    # -----------------------------
    # DETECTAR CAMPO DE TENSIONES
    # -----------------------------
    stress = None
    stress_key = None

    for key in mesh.point_data.keys():
        key_lower = key.lower()

        if (
            "stress" in key_lower or
            "tresca" in key_lower or
            "von" in key_lower
        ):
            stress = mesh.point_data[key]
            stress_key = key
            break

    if stress is None:
        output.append("\n⚠️ No se encontró campo de tensiones")
        return "\n".join(output)

    output.append(f"\nCampo de tensiones detectado: {stress_key}")

    stress = np.array(stress)

    # Si es tensorial → reducir a magnitud
    if len(stress.shape) > 1:
        stress = np.linalg.norm(stress, axis=1)

    # -----------------------------
    # MÉTRICAS PRINCIPALES
    # -----------------------------
    max_stress = np.max(stress)
    mean_stress = np.mean(stress)
    min_stress = np.min(stress)

    output.append(f"\nMax stress: {round(max_stress, 2)}")
    output.append(f"Mean stress: {round(mean_stress, 2)}")
    output.append(f"Min stress: {round(min_stress, 2)}")

    # -----------------------------
    # PUNTOS CRÍTICOS
    # -----------------------------
    threshold = np.percentile(stress, 95)
    critical_mask = stress >= threshold
    num_critical = np.sum(critical_mask)

    output.append(f"\nPuntos críticos (top 5%): {int(num_critical)}")

    # -----------------------------
    # GRADIENTE DE TENSIONES (simple)
    # -----------------------------
    gradients = []

    for i in range(len(points) - 1):
        dist = np.linalg.norm(points[i] - points[i+1])
        if dist > 0:
            grad = abs(stress[i] - stress[i+1]) / dist
            gradients.append(grad)

    max_gradient = max(gradients) if gradients else 0
    output.append(f"Max gradient: {round(max_gradient, 2)}")

    # -----------------------------
    # DIAGNÓSTICO
    # -----------------------------
    output.append("\n=== RESULTADO ===")

    if max_stress > mean_stress * 3:
        output.append("⚠️ Concentración de tensiones detectada")

    if max_gradient > mean_stress:
        output.append("⚠️ Alto gradiente de tensiones (posible discontinuidad)")

    if yield_limit is not None:
        if max_stress > yield_limit:
            output.append("🚨 Supera límite elástico")
        else:
            output.append("✔ Dentro del límite elástico")

    return "\n".join(output)

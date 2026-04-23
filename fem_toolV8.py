import meshio
import numpy as np

def analyze_file(file_path, yield_limit=None):
    try:
        mesh = meshio.read(file_path)
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
    # CAMPOS DISPONIBLES
    # -----------------------------
    fields = mesh.point_data.keys()
    output.append("\nCampos disponibles:")
    for f in fields:
        output.append(f" - {f}")

    # -----------------------------
    # DETECCIÓN AUTOMÁTICA DE STRESS
    # -----------------------------
    stress_field = None

    for key in fields:
        if "stress" in key.lower() or "tresca" in key.lower():
            stress_field = key
            break

    if stress_field is None:
        return "No se encontró campo de tensiones en el archivo."

    stress = mesh.point_data[stress_field]

    # Asegurar array 1D
    if len(stress.shape) > 1:
        stress = np.linalg.norm(stress, axis=1)

    # -----------------------------
    # MÉTRICAS
    # -----------------------------
    max_stress = np.max(stress)
    mean_stress = np.mean(stress)
    std_stress = np.std(stress)

    output.append("\n=== MÉTRICAS ===")
    output.append(f"Max stress: {round(max_stress, 2)}")
    output.append(f"Mean stress: {round(mean_stress, 2)}")
    output.append(f"Std stress: {round(std_stress, 2)}")

    # -----------------------------
    # DETECCIÓN DE ZONAS CRÍTICAS
    # -----------------------------
    threshold = np.percentile(stress, 95)
    critical = stress >= threshold
    num_critical = np.sum(critical)

    output.append(f"\nPuntos críticos (top 5%): {num_critical}")

    # -----------------------------
    # GRADIENTE APROX
    # -----------------------------
    gradients = []

    for i in range(len(points) - 1):
        dist = np.linalg.norm(points[i] - points[i + 1])
        if dist > 0:
            gradients.append(abs(stress[i] - stress[i + 1]) / dist)

    max_gradient = max(gradients) if gradients else 0
    output.append(f"Max gradient: {round(max_gradient, 2)}")

    # -----------------------------
    # ENGINE DE DECISIÓN
    # -----------------------------
    output.append("\n=== DIAGNÓSTICO ===")

    if max_stress > mean_stress * 3:
        output.append("⚠️ Alta concentración de tensiones")

    if yield_limit:
        if max_stress > yield_limit:
            output.append("❌ Supera límite elástico")
        else:
            output.append("✔ Dentro de límite elástico")

    if max_gradient > 100:
        output.append("⚠️ Cambio brusco de tensiones (posible entalla)")

    if num_critical < len(stress) * 0.02:
        output.append("⚠️ Concentración localizada (punto crítico)")
    else:
        output.append("✔ Distribución más uniforme")

    return "\n".join(output)
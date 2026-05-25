from app.config import LIMITES_INCLUSION, CA_P_MIN, CA_P_MAX


def calcular_composicion(ingredientes_activos, total_kg):
    totales = {
        'proteina': 0.0, 'em_kcal': 0.0, 'fibra': 0.0, 'grasa': 0.0,
        'calcio': 0.0, 'fosforo': 0.0, 'lisina': 0.0, 'metionina': 0.0,
        'colina_mgr': 0.0,
    }
    nutrientes = list(totales.keys())
    ingredientes_result = []

    for ing in ingredientes_activos:
        if ing.get('tanteo_kg', 0) <= 0:
            continue
        proporcion = ing['tanteo_kg'] / total_kg if total_kg > 0 else 0
        ing_result = dict(ing)
        ing_result['porcentaje'] = proporcion * 100
        for nut in nutrientes:
            valor = ing.get(nut, 0) * proporcion
            clave_aportada = f'{nut}_aportada' if nut not in ('calcio', 'fosforo') else f'{nut}_aportado'
            ing_result[clave_aportada] = valor
            totales[nut] += valor
        ingredientes_result.append(ing_result)

    return totales, ingredientes_result


def calcular_costo(ingredientes_activos, total_kg):
    costo_total = sum(
        ing.get('tanteo_kg', 0) * ing.get('precio_kg', 0)
        for ing in ingredientes_activos
        if ing.get('tanteo_kg', 0) > 0
    )
    costo_por_kg = costo_total / total_kg if total_kg > 0 else 0
    return costo_por_kg, costo_por_kg * 1000


def validar_salud(totales, ingredientes_activos, total_kg):
    alertas = []

    ca = totales.get('calcio', 0)
    p = totales.get('fosforo', 0)
    if p > 0:
        ratio_cap = ca / p
        if not (CA_P_MIN <= ratio_cap <= CA_P_MAX):
            alertas.append(
                f"Relación Ca:P = {ratio_cap:.2f} (rango normal: {CA_P_MIN}-{CA_P_MAX})"
            )

    if total_kg > 0:
        for ing in ingredientes_activos:
            nombre = ing.get('nombre', '').lower()
            for limite_nombre, limite in LIMITES_INCLUSION.items():
                if limite_nombre in nombre:
                    porcentaje = (ing.get('tanteo_kg', 0) / total_kg) * 100
                    if porcentaje > limite:
                        alertas.append(
                            f"{ing.get('nombre', '')}: {porcentaje:.1f}% supera el límite de {limite}%"
                        )

            tms = ing.get('tms', 0)
            if tms > 0:
                porcentaje = (ing.get('tanteo_kg', 0) / total_kg) * 100
                if porcentaje > tms:
                    alertas.append(
                        f"{ing.get('nombre', '')}: {porcentaje:.1f}% supera TMS de {tms}%"
                    )

    return alertas


def normalizar_para_radar(valores, total_kg):
    if total_kg <= 0:
        return valores
    factor = total_kg / 100
    return {k: v / factor for k, v in valores.items()}


def sugerir_ajuste(nutriente, valor_actual, valor_objetivo, ingredientes_activos, total_kg):
    if total_kg <= 0:
        return None

    diferencia = valor_objetivo - valor_actual
    if abs(diferencia) < 0.1:
        return None

    sugerencias = []
    for ing in ingredientes_activos:
        contenido = ing.get(nutriente, 0)
        if contenido > 0 and diferencia > 0:
            sugerencias.append({
                'nombre': ing.get('nombre', ''),
                'accion': 'aumentar',
                'contenido': contenido,
                'eficiencia': contenido
            })
        elif contenido > 0 and diferencia < 0:
            sugerencias.append({
                'nombre': ing.get('nombre', ''),
                'accion': 'disminuir',
                'contenido': contenido,
                'eficiencia': contenido
            })

    if sugerencias:
        sugerencias.sort(key=lambda x: x['eficiencia'], reverse=(diferencia > 0))
        return sugerencias[:3]

    return None

import numpy as np
from scipy.optimize import linprog


NUTRIENTES = [
    'proteina', 'em_kcal', 'fibra', 'grasa',
    'calcio', 'fosforo', 'lisina', 'metionina', 'colina_mgr'
]


def calcular_formulacion_inversa(ingredientes, metas_min, metas_max, limites_ing, total_kg):
    n = len(ingredientes)
    if n == 0:
        return None, ['No hay ingredientes disponibles']

    costos = [ing.get('precio_kg', 0) for ing in ingredientes]

    A_eq = [np.ones(n)]
    b_eq = [1.0]

    A_ub = []
    b_ub = []

    for nutriente in NUTRIENTES:
        min_val = metas_min.get(nutriente)
        max_val = metas_max.get(nutriente)

        if min_val is not None and min_val > 0:
            fila = [-ing.get(nutriente, 0) for ing in ingredientes]
            A_ub.append(fila)
            b_ub.append(-min_val)

        if max_val is not None and max_val > 0:
            fila = [ing.get(nutriente, 0) for ing in ingredientes]
            A_ub.append(fila)
            b_ub.append(max_val)

    bounds = []
    for i, ing in enumerate(ingredientes):
        nombre = ing.get('nombre', '').lower()
        lim_min = 0.0
        lim_max = 1.0

        if nombre in limites_ing:
            l_min, l_max = limites_ing[nombre]
            lim_min = l_min / 100.0
            lim_max = l_max / 100.0

        bounds.append((lim_min, lim_max))

    try:
        resultado = linprog(
            costos,
            A_ub=np.array(A_ub) if A_ub else None,
            b_ub=np.array(b_ub) if b_ub else None,
            A_eq=np.array(A_eq),
            b_eq=np.array(b_eq),
            bounds=bounds,
            method='highs'
        )

        if resultado.success:
            formulacion = {}
            for i, ing in enumerate(ingredientes):
                porcentaje = resultado.x[i] * 100
                if porcentaje > 0.01:
                    formulacion[ing.get('id', i)] = {
                        'porcentaje': porcentaje,
                        'kg': (porcentaje / 100) * total_kg,
                        'costo': (porcentaje / 100) * total_kg * ing.get('precio_kg', 0),
                    }
            return formulacion, None
        else:
            return None, diagnosticar_infeasibilidad(ingredientes, metas_min, metas_max)
    except Exception as e:
        return None, [f'Error en optimización: {str(e)}']


def diagnosticar_infeasibilidad(ingredientes, metas_min, metas_max):
    problemas = []

    for nutriente in NUTRIENTES:
        min_val = metas_min.get(nutriente)
        max_val = metas_max.get(nutriente)

        if min_val is not None and min_val > 0:
            max_posible = max(ing.get(nutriente, 0) for ing in ingredientes)
            if min_val > max_posible:
                nombre_nut = _nombre_nutriente(nutriente)
                ing_mas_rico = max(ingredientes, key=lambda x: x.get(nutriente, 0))
                problemas.append(
                    f"{nombre_nut}: pides mínimo {min_val}% pero el ingrediente más rico "
                    f"({ing_mas_rico['nombre']}) tiene {max_posible}%"
                )

        if max_val is not None and max_val > 0:
            min_posible = min(ing.get(nutriente, 0) for ing in ingredientes)
            if max_val < min_posible:
                nombre_nut = _nombre_nutriente(nutriente)
                ing_mas_pobre = min(ingredientes, key=lambda x: x.get(nutriente, 0))
                problemas.append(
                    f"{nombre_nut}: pides máximo {max_val}% pero el ingrediente más bajo "
                    f"({ing_mas_pobre['nombre']}) tiene {min_posible}%"
                )

    if not problemas:
        problemas.append(
            "Las restricciones de inclusión mínima/máxima de ingredientes "
            "hacen imposible encontrar una solución. Amplía los rangos."
        )

    return problemas


def _nombre_nutriente(nutriente):
    nombres = {
        'proteina': 'Proteína',
        'em_kcal': 'EM Kcal/kg',
        'fibra': 'Fibra',
        'grasa': 'Grasa',
        'calcio': 'Calcio',
        'fosforo': 'Fósforo',
        'lisina': 'Lisina',
        'metionina': 'Metionina',
        'colina_mgr': 'Colina',
    }
    return nombres.get(nutriente, nutriente)

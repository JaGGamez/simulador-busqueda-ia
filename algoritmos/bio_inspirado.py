"""
bio_inspirado.py — Optimización por Colonia de Hormigas (ACO) como generador.

Protocolo de yield (al final de cada iteración de la colonia):
  Mientras itera → yield ("buscando",  feromonas, mejor_camino_hasta_ahora, metricas)
  Al converger   → yield ("encontrado", feromonas, mejor_camino, metricas)
  Sin solución   → yield ("sin_solucion", feromonas, [], metricas)

El visualizador usa la matriz `feromonas` para dibujar el mapa de calor.
"""

from __future__ import annotations
import random
import math
from typing import Dict, Generator, List, Optional, Tuple

from entorno import Mapa, Nodo
from metricas import Metricas


# ------------------------------------------------------------------
# Parámetros ACO por defecto
# ------------------------------------------------------------------

ALFA = 1.0          # Peso de la feromona
BETA = 2.0          # Peso de la heurística (1/costo)
RHO = 0.1           # Tasa de evaporación global
Q = 100.0           # Constante de depósito de feromona
N_HORMIGAS = 20     # Número de hormigas por iteración
MAX_ITER = 80       # Iteraciones máximas de la colonia
FER_INICIAL = 1.0   # Feromona inicial en cada arista


# ------------------------------------------------------------------
# Construcción de camino para una hormiga (greedy probabilístico)
# ------------------------------------------------------------------

def _construir_camino(
    mapa: Mapa,
    feromonas: Dict[Tuple[Nodo, Nodo], float],
    inicio: Nodo,
    destino: Nodo,
    max_pasos: int,
) -> Optional[List[Nodo]]:
    """
    Una hormiga construye un camino desde inicio hasta destino.
    Usa selección de ruleta ponderada por feromona y heurística.
    Retorna None si no llega al destino dentro de max_pasos.
    """
    actual = inicio
    visitados = {actual}
    camino = [actual]

    for _ in range(max_pasos):
        if actual == destino:
            return camino

        vecinos_raw = mapa.obtener_vecinos(actual)
        # Filtra vecinos ya visitados para evitar ciclos
        candidatos = [(v, c) for v, c in vecinos_raw if v not in visitados]

        if not candidatos:
            break

        # Calcula atractivos: τ^α * η^β  donde η = 1/costo
        pesos: List[float] = []
        for vecino, costo in candidatos:
            tau = feromonas.get((actual, vecino), FER_INICIAL)
            eta = 1.0 / costo if costo > 0 else 1.0
            pesos.append((tau ** ALFA) * (eta ** BETA))

        total = sum(pesos)
        if total == 0:
            break

        # Selección por ruleta
        r = random.random() * total
        acum = 0.0
        siguiente = candidatos[0][0]
        for (vecino, _), peso in zip(candidatos, pesos):
            acum += peso
            if acum >= r:
                siguiente = vecino
                break

        camino.append(siguiente)
        visitados.add(siguiente)
        actual = siguiente

    return camino if camino[-1] == destino else None


# ------------------------------------------------------------------
# Costo de un camino
# ------------------------------------------------------------------

def _costo_camino(mapa: Mapa, camino: List[Nodo]) -> float:
    return sum(mapa.costo(n) for n in camino[1:])


# ------------------------------------------------------------------
# Generador ACO
# ------------------------------------------------------------------

def aco_generator(
    mapa: Mapa,
    metricas: Metricas,
    n_hormigas: int = N_HORMIGAS,
    max_iter: int = MAX_ITER,
    alfa: float = ALFA,
    beta: float = BETA,
    rho: float = RHO,
    q: float = Q,
) -> Generator:
    """
    Generador ACO que cede el estado de las feromonas tras cada iteración.

    Yields:
        Tupla (estado, feromonas_dict, mejor_camino, metricas) donde:
          - feromonas_dict: {(nodo_a, nodo_b): valor_feromona}
    """
    inicio = mapa.inicio
    destino = mapa.destino
    max_pasos = mapa.filas * mapa.columnas * 2  # límite holgado

    # Inicializar feromonas en todas las aristas válidas
    feromonas: Dict[Tuple[Nodo, Nodo], float] = {}
    for f in range(mapa.filas):
        for c in range(mapa.columnas):
            nodo = (f, c)
            if not mapa.es_valido(nodo):
                continue
            for vecino, _ in mapa.obtener_vecinos(nodo):
                feromonas[(nodo, vecino)] = FER_INICIAL

    mejor_camino: Optional[List[Nodo]] = None
    mejor_costo = float("inf")

    metricas.iniciar()

    for iteracion in range(1, max_iter + 1):
        metricas.iteraciones = iteracion
        caminos_iter: List[List[Nodo]] = []

        # --- Fase de construcción ---
        for _ in range(n_hormigas):
            camino = _construir_camino(mapa, feromonas, inicio, destino, max_pasos)
            if camino is not None:
                caminos_iter.append(camino)

        # --- Actualizar mejor solución global ---
        for camino in caminos_iter:
            costo = _costo_camino(mapa, camino)
            if costo < mejor_costo:
                mejor_costo = costo
                mejor_camino = camino

        # --- Evaporación global ---
        for arista in feromonas:
            feromonas[arista] *= (1.0 - rho)
            feromonas[arista] = max(feromonas[arista], 1e-6)  # mínimo numérico

        # --- Depósito de feromona por las hormigas exitosas ---
        for camino in caminos_iter:
            costo = _costo_camino(mapa, camino)
            delta = q / costo if costo > 0 else 0.0
            for i in range(len(camino) - 1):
                arista = (camino[i], camino[i + 1])
                arista_inv = (camino[i + 1], camino[i])
                feromonas[arista] = feromonas.get(arista, FER_INICIAL) + delta
                feromonas[arista_inv] = feromonas.get(arista_inv, FER_INICIAL) + delta

        yield ("buscando", feromonas, mejor_camino or [], metricas)

    # Fin de iteraciones
    metricas.detener()

    if mejor_camino is not None:
        metricas.costo_ruta = mejor_costo
        yield ("encontrado", feromonas, mejor_camino, metricas)
    else:
        yield ("sin_solucion", feromonas, [], metricas)

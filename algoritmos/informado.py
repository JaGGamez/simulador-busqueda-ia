"""
informado.py — Algoritmo A* implementado como generador de Python.

Cada llamada a next() expande un único nodo, permitiendo que pygame
repinte la cuadrícula entre expansiones sin bloquear la UI.

Protocolo de yield:
  Mientras busca  → yield ("buscando", visitados, frontera, camino_parcial, metricas)
  Al encontrar    → yield ("encontrado", visitados, frontera, camino, metricas)
  Sin solución    → yield ("sin_solucion", visitados, set(), [], metricas)

Recordar qu yield sirve como alternativa al return clasico. El yield permite hacer un return, pero paso a paso. 
Un return normal devuelve y calcula todo antes del return, el yield va paso a paso a traves del next().
Por la naturaleza del proyecto, donde se usa pygame, es necesario usar el yield para visualizar el paso a paso 
de la solucion de la busqueda inteligente, en este caso con el A*. De otra manera la animacion no se apreciaria como un paso a paso de busqueda.
  
"""

from __future__ import annotations
import heapq
from typing import Dict, Generator, List, Optional, Set, Tuple

from entorno import Mapa, Nodo
from metricas import Metricas


# ------------------------------------------------------------------
# Heurística Manhattan
# ------------------------------------------------------------------

def _heuristica(a: Nodo, b: Nodo) -> int:
    """Distancia Manhattan entre dos nodos."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


# ------------------------------------------------------------------
# Reconstrucción de camino
# ------------------------------------------------------------------

def _reconstruir_camino(padres: Dict[Nodo, Optional[Nodo]], destino: Nodo) -> List[Nodo]:
    """Traza el camino desde el destino hasta el origen usando el diccionario de padres."""
    camino: List[Nodo] = []
    actual: Optional[Nodo] = destino
    while actual is not None:
        camino.append(actual)
        actual = padres.get(actual)
    camino.reverse()
    return camino


# ------------------------------------------------------------------
# Generador A*
# ------------------------------------------------------------------

def astar_generator(
    mapa: Mapa,
    metricas: Metricas,
) -> Generator:
    """
    Generador A* que cede el estado de la búsqueda en cada expansión.

    Args:
        mapa:     Instancia de Mapa con grilla, inicio y destino.
        metricas: Objeto Metricas donde se registran nodos y costo.

    Yields:
        Tupla (estado, visitados, frontera, camino, metricas) donde:
          - estado:   "buscando" | "encontrado" | "sin_solucion"
          - visitados: set de Nodo ya cerrados
          - frontera:  set de Nodo en la cola abierta
          - camino:    lista de Nodo (vacía mientras busca, completa al terminar)
    """
    inicio = mapa.inicio
    destino = mapa.destino

    # g_costo[n] = costo acumulado más bajo conocido hasta n
    g_costo: Dict[Nodo, float] = {inicio: 0.0}
    padres: Dict[Nodo, Optional[Nodo]] = {inicio: None}

    # Heap: (f, contador_desempate, nodo)
    contador = 0
    heap: List[Tuple[float, int, Nodo]] = []
    heapq.heappush(heap, (0.0 + _heuristica(inicio, destino), contador, inicio))

    visitados: Set[Nodo] = set()
    en_frontera: Set[Nodo] = {inicio}

    metricas.iniciar()

    while heap:
        _, _, actual = heapq.heappop(heap)

        if actual in visitados:
            continue
        visitados.add(actual)
        en_frontera.discard(actual)
        metricas.nodos_expandidos += 1

        # Meta alcanzada
        if actual == destino:
            metricas.detener()
            camino = _reconstruir_camino(padres, destino)
            metricas.costo_ruta = g_costo[destino]
            yield ("encontrado", visitados, en_frontera, camino, metricas)
            return

        for vecino, costo_paso in mapa.obtener_vecinos(actual):
            if vecino in visitados:
                continue
            nuevo_g = g_costo[actual] + costo_paso
            if nuevo_g < g_costo.get(vecino, float("inf")):
                g_costo[vecino] = nuevo_g
                padres[vecino] = actual
                f = nuevo_g + _heuristica(vecino, destino)
                contador += 1
                heapq.heappush(heap, (f, contador, vecino))
                en_frontera.add(vecino)

        yield ("buscando", visitados, en_frontera, [], metricas)

    # Cola vacía sin encontrar destino
    metricas.detener()
    yield ("sin_solucion", visitados, set(), [], metricas)

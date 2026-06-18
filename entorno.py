"""
entorno.py — Carga y representación del mapa de búsqueda.

El mapa es una cuadrícula de enteros donde:
  0 → obstáculo (intransitable)
  1 → costo 1 (terreno llano)
  2 → costo 2 (terreno moderado)
  3 → costo 3 (terreno pesado)
"""

from __future__ import annotations
from typing import List, Tuple, Optional


# Tipo alias para un nodo (fila, columna)
Nodo = Tuple[int, int]


class Mapa:
    """Representa el entorno de búsqueda leído desde un archivo .txt."""

    # Movimientos ortogonales: arriba, abajo, izquierda, derecha
    _DIRECCIONES: List[Tuple[int, int]] = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def __init__(self, ruta_archivo: str) -> None:
        self.ruta_archivo = ruta_archivo
        self.grilla: List[List[int]] = []
        self.filas: int = 0
        self.columnas: int = 0
        self.inicio: Nodo = (0, 0)
        self.destino: Nodo = (0, 0)

        self._cargar(ruta_archivo)
        self.inicio = self._buscar_primera_celda_valida()
        self.destino = self._buscar_ultima_celda_valida()

    # ------------------------------------------------------------------
    # Carga del archivo
    # ------------------------------------------------------------------

    def _cargar(self, ruta: str) -> None:
        """Lee el archivo .txt y construye la grilla de enteros."""
        with open(ruta, "r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea:
                    continue
                fila = [int(v) for v in linea.split()]
                self.grilla.append(fila)

        self.filas = len(self.grilla)
        if self.filas == 0:
            raise ValueError(f"El archivo '{ruta}' no contiene datos válidos.")
        self.columnas = len(self.grilla[0])

    # ------------------------------------------------------------------
    # Búsqueda de inicio / destino
    # ------------------------------------------------------------------

    def _buscar_primera_celda_valida(self) -> Nodo:
        """Devuelve la primera celda transitable comenzando desde (0,0)."""
        for f in range(self.filas):
            for c in range(self.columnas):
                if self.grilla[f][c] != 0:
                    return (f, c)
        raise ValueError("No existe ninguna celda transitable en el mapa.")

    def _buscar_ultima_celda_valida(self) -> Nodo:
        """Devuelve la última celda transitable comenzando desde la esquina inferior derecha."""
        for f in range(self.filas - 1, -1, -1):
            for c in range(self.columnas - 1, -1, -1):
                if self.grilla[f][c] != 0:
                    return (f, c)
        raise ValueError("No existe ninguna celda transitable en el mapa.")

    # ------------------------------------------------------------------
    # Interfaz pública
    # ------------------------------------------------------------------

    def es_valido(self, nodo: Nodo) -> bool:
        """Retorna True si el nodo está dentro de los límites y no es obstáculo."""
        f, c = nodo
        return (
            0 <= f < self.filas
            and 0 <= c < self.columnas
            and self.grilla[f][c] != 0
        )

    def costo(self, nodo: Nodo) -> int:
        """Devuelve el costo de entrar al nodo (valor de la celda)."""
        f, c = nodo
        return self.grilla[f][c]

    def obtener_vecinos(self, nodo: Nodo) -> List[Tuple[Nodo, int]]:
        """
        Retorna los vecinos ortogonales transitables del nodo dado.

        Returns:
            Lista de tuplas (nodo_vecino, costo_de_transición).
        """
        f, c = nodo
        vecinos: List[Tuple[Nodo, int]] = []
        for df, dc in self._DIRECCIONES:
            vecino = (f + df, c + dc)
            if self.es_valido(vecino):
                vecinos.append((vecino, self.costo(vecino)))
        return vecinos

    def obtener_grilla(self) -> List[List[int]]:
        """Devuelve una copia de la grilla (para evitar mutaciones externas)."""
        return [fila[:] for fila in self.grilla]

    def __repr__(self) -> str:
        return (
            f"Mapa('{self.ruta_archivo}', {self.filas}x{self.columnas}, "
            f"inicio={self.inicio}, destino={self.destino})"
        )

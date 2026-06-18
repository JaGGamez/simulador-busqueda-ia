"""
metricas.py — Temporizador y contadores de rendimiento para los algoritmos.

El tiempo medido es puramente computacional: el Visualizador NO debe
interferir con el cronómetro (el timer solo corre mientras el generador
del algoritmo está activo, no durante los frames de pygame).
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Metricas:
    """Acumula estadísticas de una ejecución algorítmica."""

    nombre_algoritmo: str
    nodos_expandidos: int = 0
    iteraciones: int = 0          # Usado por ACO
    costo_ruta: float = 0.0
    _inicio_tiempo: float = field(default=0.0, repr=False)
    _fin_tiempo: float = field(default=0.0, repr=False)
    _corriendo: bool = field(default=False, repr=False)

    # ------------------------------------------------------------------
    # Control del temporizador
    # ------------------------------------------------------------------

    def iniciar(self) -> None:
        """Inicia el cronómetro computacional."""
        self._inicio_tiempo = time.perf_counter()
        self._corriendo = True

    def detener(self) -> None:
        """Detiene el cronómetro y congela el tiempo transcurrido."""
        if self._corriendo:
            self._fin_tiempo = time.perf_counter()
            self._corriendo = False

    @property
    def tiempo_segundos(self) -> float:
        """Tiempo total de ejecución en segundos."""
        if self._corriendo:
            return time.perf_counter() - self._inicio_tiempo
        return self._fin_tiempo - self._inicio_tiempo

    # ------------------------------------------------------------------
    # Impresión de resultados
    # ------------------------------------------------------------------

    def imprimir_tabla(self) -> None:
        """Imprime una tabla formateada con todas las métricas en consola."""
        ancho = 50
        sep = "-" * ancho

        print(f"\n{'=' * ancho}")
        print(f"  RESULTADOS - {self.nombre_algoritmo}")
        print(f"{'=' * ancho}")
        print(f"  {'Tiempo de ejecucion':<28} {self.tiempo_segundos * 1000:.4f} ms")
        print(f"  {sep}")
        if self.iteraciones > 0:
            print(f"  {'Iteraciones (colonia)':<28} {self.iteraciones}")
        else:
            print(f"  {'Nodos expandidos':<28} {self.nodos_expandidos}")
        print(f"  {sep}")
        if self.costo_ruta > 0:
            print(f"  {'Costo total de la ruta':<28} {self.costo_ruta:.1f}")
        else:
            print(f"  {'Costo total de la ruta':<28} No encontrada")
        print(f"{'=' * ancho}\n")

"""
Paquete de algoritmos de búsqueda.

Exporta los generadores de cada algoritmo para que visualizador.py
pueda invocarlos de forma uniforme con next().
"""

from algoritmos.informado import astar_generator
from algoritmos.bio_inspirado import aco_generator

__all__ = ["astar_generator", "aco_generator"]

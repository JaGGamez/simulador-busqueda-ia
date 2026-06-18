"""
visualizador.py — Motor de animación pygame para el simulador de búsqueda.

Ciclo principal:
  1. Calcula el tamaño de celda en función del mapa y la resolución disponible.
  2. En cada frame llama a next(generador) para avanzar UN paso del algoritmo.
  3. Repinta la cuadrícula con los estados devueltos por el generador.
  4. Cuando el algoritmo termina, muestra el camino final durante DELAY_FINAL ms
     y luego cierra la ventana.

Colores:
  A*  : frontera → azul claro, visitados → azul oscuro, camino → amarillo
  ACO : mapa de calor de feromonas (rojo con alpha), camino → amarillo
"""

from __future__ import annotations
import sys
import math
from typing import Any, Dict, Generator, List, Optional, Set, Tuple

import pygame

from entorno import Mapa, Nodo


# ------------------------------------------------------------------
# Paleta de colores
# ------------------------------------------------------------------

COLOR_FONDO      = (20,  20,  20)
COLOR_OBSTACULO  = (15,  15,  15)
COLOR_COSTO_1    = (210, 180, 140)   # café claro (terreno básico)
COLOR_COSTO_2    = ( 80, 160,  80)   # verde (vegetación)
COLOR_COSTO_3    = (100,  80,  60)   # café oscuro (terreno pesado)
COLOR_GRID       = ( 40,  40,  40)   # líneas de la cuadrícula

COLOR_INICIO     = ( 50, 220,  50)   # verde brillante
COLOR_DESTINO    = (220,  50,  50)   # rojo brillante

# A*
COLOR_VISITADO   = ( 30,  80, 160)   # azul oscuro
COLOR_FRONTERA   = (100, 180, 240)   # azul claro
COLOR_CAMINO     = (255, 220,   0)   # amarillo

# ACO — el calor de feromonas se calcula dinámicamente
COLOR_ACO_BAJA   = (  0,   0,   0, 0)    # transparente (feromona mínima)
COLOR_ACO_ALTA   = (220,  30,  30, 180)  # rojo semitransparente

# HUD
COLOR_TEXTO      = (230, 230, 230)
COLOR_HUD_BG     = ( 0,   0,   0, 160)

# Configuración visual
MARGEN_HUD          = 6     # píxeles de margen para el panel de texto
DELAY_FINAL         = 3000  # ms que se muestra el camino final antes de cerrar
CELDA_MIN      = 12    # tamaño mínimo de celda en píxeles
CELDA_MAX      = 60    # tamaño máximo de celda en píxeles
PANTALLA_MAX_W = 1280
PANTALLA_MAX_H = 800


# ------------------------------------------------------------------
# Helpers de color
# ------------------------------------------------------------------

def _color_terreno(valor: int) -> Tuple[int, int, int]:
    return {1: COLOR_COSTO_1, 2: COLOR_COSTO_2, 3: COLOR_COSTO_3}.get(valor, COLOR_OBSTACULO)


def _interpolar_color(
    c1: Tuple[int, int, int],
    c2: Tuple[int, int, int],
    t: float,
) -> Tuple[int, int, int]:
    """Interpolación lineal entre dos colores RGB. t ∈ [0,1]."""
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


# ------------------------------------------------------------------
# Clase principal
# ------------------------------------------------------------------

class Visualizador:
    """Gestiona la ventana pygame y anima el generador del algoritmo."""

    def __init__(self, mapa: Mapa, titulo: str = "Simulador de Búsqueda") -> None:
        self.mapa = mapa
        self.titulo = titulo

        pygame.init()
        pygame.display.set_caption(titulo)

        self.celda = self._calcular_tamano_celda()
        ancho = mapa.columnas * self.celda
        alto  = mapa.filas   * self.celda + 32  # espacio para HUD en la parte inferior
        self.pantalla = pygame.display.set_mode((ancho, alto))
        self.reloj = pygame.time.Clock()
        self.fuente = pygame.font.SysFont("monospace", 13, bold=False)
        self.fuente_bold = pygame.font.SysFont("monospace", 14, bold=True)

        # Superficie de overlay para feromonas (ACO) con alpha por píxel
        self.overlay = pygame.Surface((ancho, mapa.filas * self.celda), pygame.SRCALPHA)

    # ------------------------------------------------------------------
    # Cálculo de tamaño de celda
    # ------------------------------------------------------------------

    def _calcular_tamano_celda(self) -> int:
        celda_w = PANTALLA_MAX_W // self.mapa.columnas
        celda_h = (PANTALLA_MAX_H - 32) // self.mapa.filas
        return max(CELDA_MIN, min(CELDA_MAX, min(celda_w, celda_h)))

    # ------------------------------------------------------------------
    # Dibujo del mapa base
    # ------------------------------------------------------------------

    def _dibujar_mapa_base(self) -> None:
        """Dibuja el terreno sin estados de algoritmo."""
        c = self.celda
        for f in range(self.mapa.filas):
            for col in range(self.mapa.columnas):
                valor = self.mapa.grilla[f][col]
                rect = pygame.Rect(col * c, f * c, c, c)
                pygame.draw.rect(self.pantalla, _color_terreno(valor), rect)
                pygame.draw.rect(self.pantalla, COLOR_GRID, rect, 1)

        # Inicio y destino (siempre encima del terreno)
        fi, ci = self.mapa.inicio
        fd, cd = self.mapa.destino
        pygame.draw.rect(self.pantalla, COLOR_INICIO,
                         pygame.Rect(ci * c + 2, fi * c + 2, c - 4, c - 4))
        pygame.draw.rect(self.pantalla, COLOR_DESTINO,
                         pygame.Rect(cd * c + 2, fd * c + 2, c - 4, c - 4))

    # ------------------------------------------------------------------
    # Dibujo de estados A*
    # ------------------------------------------------------------------

    def _dibujar_astar(
        self,
        visitados: Set[Nodo],
        frontera: Set[Nodo],
        camino: List[Nodo],
    ) -> None:
        c = self.celda
        for nodo in visitados:
            f, col = nodo
            if nodo in (self.mapa.inicio, self.mapa.destino):
                continue
            pygame.draw.rect(self.pantalla, COLOR_VISITADO,
                             pygame.Rect(col * c + 1, f * c + 1, c - 2, c - 2))

        for nodo in frontera:
            f, col = nodo
            if nodo in (self.mapa.inicio, self.mapa.destino):
                continue
            pygame.draw.rect(self.pantalla, COLOR_FRONTERA,
                             pygame.Rect(col * c + 1, f * c + 1, c - 2, c - 2))

        for nodo in camino:
            f, col = nodo
            if nodo in (self.mapa.inicio, self.mapa.destino):
                continue
            pygame.draw.rect(self.pantalla, COLOR_CAMINO,
                             pygame.Rect(col * c + 1, f * c + 1, c - 2, c - 2))

    # ------------------------------------------------------------------
    # Dibujo del mapa de calor de feromonas (ACO)
    # ------------------------------------------------------------------

    def _dibujar_feromonas(
        self,
        feromonas: Dict[Tuple[Nodo, Nodo], float],
        camino: List[Nodo],
    ) -> None:
        c = self.celda
        self.overlay.fill((0, 0, 0, 0))

        if not feromonas:
            self.pantalla.blit(self.overlay, (0, 0))
            return

        # Valor máximo de feromona para normalizar
        valores = list(feromonas.values())
        fer_max = max(valores) if valores else 1.0
        fer_min = min(valores) if valores else 0.0
        rango = fer_max - fer_min if fer_max > fer_min else 1.0

        # Acumular feromona por celda (promedio de aristas entrantes)
        celda_fer: Dict[Nodo, float] = {}
        conteo: Dict[Nodo, int] = {}
        for (_, dest), val in feromonas.items():
            celda_fer[dest] = celda_fer.get(dest, 0.0) + val
            conteo[dest] = conteo.get(dest, 0) + 1

        for nodo, total in celda_fer.items():
            f, col = nodo
            media = total / conteo[nodo]
            t = (media - fer_min) / rango
            alpha = int(30 + 180 * t)
            r = int(50 + 200 * t)
            g = int(10 * (1 - t))
            b = 10
            pygame.draw.rect(
                self.overlay,
                (r, g, b, alpha),
                pygame.Rect(col * c, f * c, c, c),
            )

        self.pantalla.blit(self.overlay, (0, 0))

        # Camino encima del mapa de calor
        for nodo in camino:
            f, col = nodo
            if nodo in (self.mapa.inicio, self.mapa.destino):
                continue
            pygame.draw.rect(self.pantalla, COLOR_CAMINO,
                             pygame.Rect(col * c + 1, f * c + 1, c - 2, c - 2))

    # ------------------------------------------------------------------
    # HUD (panel de texto inferior)
    # ------------------------------------------------------------------

    def _dibujar_hud(self, estado: str, metricas: Any) -> None:
        ancho, alto = self.pantalla.get_size()
        y_hud = self.mapa.filas * self.celda

        hud_rect = pygame.Rect(0, y_hud, ancho, alto - y_hud)
        pygame.draw.rect(self.pantalla, (30, 30, 30), hud_rect)

        partes = [
            f"Alg: {metricas.nombre_algoritmo}",
            f"Estado: {estado}",
        ]
        if metricas.iteraciones > 0:
            partes.append(f"Iter: {metricas.iteraciones}")
        else:
            partes.append(f"Nodos: {metricas.nodos_expandidos}")

        if metricas.costo_ruta > 0:
            partes.append(f"Costo: {metricas.costo_ruta:.0f}")

        if estado in ("encontrado", "sin_solucion"):
            partes.append("ESC para salir")

        texto = "   |   ".join(partes)
        sup = self.fuente.render(texto, True, COLOR_TEXTO)
        self.pantalla.blit(sup, (MARGEN_HUD, y_hud + MARGEN_HUD))

    # ------------------------------------------------------------------
    # Bucle de animación principal
    # ------------------------------------------------------------------

    def ejecutar(self, generador: Generator, algoritmo: str = "astar") -> None:
        """
        Corre el bucle pygame consumiendo el generador frame a frame.

        Args:
            generador: Generador del algoritmo (astar_generator o aco_generator).
            algoritmo: "astar" | "aco" — determina qué capa de visualización usar.
        """
        es_aco = (algoritmo.lower() == "aco")
        terminado = False
        estado_actual = "buscando"
        ultimo_yield: Any = None

        while True:
            # --- Eventos ---
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)

            # --- Avanzar algoritmo ---
            if not terminado:
                try:
                    ultimo_yield = next(generador)
                    estado_actual = ultimo_yield[0]
                    if estado_actual in ("encontrado", "sin_solucion"):
                        terminado = True
                except StopIteration:
                    terminado = True

            # --- Renderizado ---
            self.pantalla.fill(COLOR_FONDO)
            self._dibujar_mapa_base()

            if ultimo_yield is not None:
                if es_aco:
                    _, feromonas, camino, metricas = ultimo_yield
                    self._dibujar_feromonas(feromonas, camino)
                else:
                    _, visitados, frontera, camino, metricas = ultimo_yield
                    self._dibujar_astar(visitados, frontera, camino)

                self._dibujar_hud(estado_actual, metricas)

            pygame.display.flip()
            self.reloj.tick(60)

            # Cuando termina el algoritmo, el bucle sigue corriendo
            # pero ya no llama a next(). La ventana permanece abierta
            # hasta que el usuario cierre o pulse ESC.

        pygame.quit()

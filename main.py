"""
main.py — Punto de entrada del Simulador Interactivo de Algoritmos de Búsqueda.

Uso desde terminal:
  python main.py --mapa mapas/mapa_medio.txt --algoritmo astar
  python main.py --mapa mapas/mapa_complejo.txt --algoritmo aco
  python main.py --mapa mapas/mapa_basico.txt --algoritmo astar --velocidad 30

Flags disponibles:
  --mapa        Ruta al archivo .txt del mapa (requerido)
  --algoritmo   "astar" o "aco" (requerido)
  --velocidad   Frames por segundo de la animación [1-120] (opcional, default=60)
  --hormigas    Número de hormigas por iteración ACO (opcional, default=20)
  --iteraciones Iteraciones máximas ACO (opcional, default=80)
"""

from __future__ import annotations
import argparse
import sys
import os


def _construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Simulador comparativo de algoritmos de búsqueda con pygame.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ejemplos:\n"
            "  python main.py --mapa mapas/mapa_basico.txt --algoritmo astar\n"
            "  python main.py --mapa mapas/mapa_medio.txt  --algoritmo aco\n"
            "  python main.py --mapa mapas/mapa_complejo.txt --algoritmo aco "
            "--hormigas 30 --iteraciones 100\n"
        ),
    )
    parser.add_argument(
        "--mapa",
        required=True,
        help="Ruta al archivo .txt del mapa (relativa al directorio de main.py)",
    )
    parser.add_argument(
        "--algoritmo",
        required=True,
        choices=["astar", "aco"],
        help="Algoritmo a ejecutar: 'astar' (A*) o 'aco' (Colonia de Hormigas)",
    )
    parser.add_argument(
        "--velocidad",
        type=int,
        default=60,
        metavar="FPS",
        help="Velocidad de animación en FPS [1-120] (default: 60)",
    )
    parser.add_argument(
        "--hormigas",
        type=int,
        default=20,
        metavar="N",
        help="Número de hormigas por iteración (solo ACO, default: 20)",
    )
    parser.add_argument(
        "--iteraciones",
        type=int,
        default=80,
        metavar="N",
        help="Iteraciones máximas de la colonia (solo ACO, default: 80)",
    )
    return parser


def main() -> None:
    # Garantiza que los imports relativos funcionen aunque se llame desde otro CWD
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    parser = _construir_parser()
    args = parser.parse_args()

    # Resolver ruta del mapa relativa al directorio del script
    ruta_mapa = args.mapa
    if not os.path.isabs(ruta_mapa):
        ruta_mapa = os.path.join(script_dir, ruta_mapa)

    if not os.path.exists(ruta_mapa):
        parser.error(f"No se encontró el archivo de mapa: {ruta_mapa}")

    velocidad = max(1, min(120, args.velocidad))

    # ------------------------------------------------------------------
    # Importaciones tardías (requieren el path correcto)
    # ------------------------------------------------------------------
    from entorno import Mapa
    from metricas import Metricas
    from visualizador import Visualizador

    # ------------------------------------------------------------------
    # Cargar mapa
    # ------------------------------------------------------------------
    print(f"\nCargando mapa: {ruta_mapa}")
    try:
        mapa = Mapa(ruta_mapa)
    except Exception as exc:
        print(f"[ERROR] No se pudo cargar el mapa: {exc}")
        sys.exit(1)

    print(f"  Tamaño : {mapa.filas} x {mapa.columnas}")
    print(f"  Inicio : {mapa.inicio}")
    print(f"  Destino: {mapa.destino}")

    # ------------------------------------------------------------------
    # Instanciar métricas y generador
    # ------------------------------------------------------------------
    nombre = "A* (Manhattan)" if args.algoritmo == "astar" else "ACO (Colonia de Hormigas)"
    metricas = Metricas(nombre_algoritmo=nombre)

    if args.algoritmo == "astar":
        from algoritmos.informado import astar_generator
        generador = astar_generator(mapa, metricas)
        print(f"\nEjecutando A* sobre '{os.path.basename(ruta_mapa)}'...")
    else:
        from algoritmos.bio_inspirado import aco_generator
        generador = aco_generator(
            mapa,
            metricas,
            n_hormigas=args.hormigas,
            max_iter=args.iteraciones,
        )
        print(
            f"\nEjecutando ACO sobre '{os.path.basename(ruta_mapa)}' "
            f"({args.hormigas} hormigas, {args.iteraciones} iter.)..."
        )

    # ------------------------------------------------------------------
    # Visualizador pygame
    # ------------------------------------------------------------------
    titulo = f"Búsqueda — {nombre} | {os.path.basename(ruta_mapa)}"
    viz = Visualizador(mapa, titulo=titulo)
    viz.ejecutar(generador, algoritmo=args.algoritmo)

    # ------------------------------------------------------------------
    # Imprimir métricas finales en consola
    # ------------------------------------------------------------------
    metricas.imprimir_tabla()


if __name__ == "__main__":
    main()

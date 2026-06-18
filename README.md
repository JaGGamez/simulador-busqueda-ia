# Simulador Interactivo y Comparativo de Algoritmos de Búsqueda

Visualizador animado de algoritmos de búsqueda sobre cuadrículas de costo variable, construido con Python y pygame. Permite comparar A* y Optimización por Colonia de Hormigas (ACO) en tiempo real desde la terminal.

---

## Requisitos

- Python 3.10 o superior
- pygame 2.x

```bash
pip install pygame
```

---

## Estructura del proyecto

```
simulador_busqueda/
├── main.py               # Punto de entrada (CLI con argparse)
├── entorno.py            # Clase Mapa: carga .txt, vecinos, costos
├── visualizador.py       # Motor de animación pygame
├── metricas.py           # Temporizador y tabla de resultados
├── algoritmos/
│   ├── __init__.py
│   ├── informado.py      # A* como generador Python
│   └── bio_inspirado.py  # ACO como generador Python
└── mapas/
    ├── mapa_basico.txt   # Cuadrícula 10×10
    ├── mapa_medio.txt    # Cuadrícula 15×15
    └── mapa_complejo.txt # Cuadrícula 20×20
```

---

## Uso

Todos los comandos se ejecutan desde dentro del directorio `simulador_busqueda/`.

```bash
cd simulador_busqueda
```

### A* sobre distintos mapas

```bash
python main.py --mapa mapas/mapa_basico.txt   --algoritmo astar
python main.py --mapa mapas/mapa_medio.txt    --algoritmo astar
python main.py --mapa mapas/mapa_complejo.txt --algoritmo astar
```

### ACO sobre distintos mapas

```bash
python main.py --mapa mapas/mapa_basico.txt   --algoritmo aco
python main.py --mapa mapas/mapa_medio.txt    --algoritmo aco --hormigas 25 --iteraciones 100
python main.py --mapa mapas/mapa_complejo.txt --algoritmo aco --hormigas 30 --iteraciones 120
```

### Flags disponibles

| Flag | Tipo | Default | Descripción |
|---|---|---|---|
| `--mapa` | `str` | — | Ruta al archivo `.txt` del mapa **(requerido)** |
| `--algoritmo` | `astar` \| `aco` | — | Algoritmo a ejecutar **(requerido)** |
| `--hormigas` | `int` | `20` | Hormigas por iteración (solo ACO) |
| `--iteraciones` | `int` | `80` | Iteraciones máximas de la colonia (solo ACO) |

---

## Formato de los mapas

Los mapas son archivos `.txt` con valores enteros separados por espacios, uno por celda:

| Valor | Significado | Color en pantalla |
|---|---|---|
| `0` | Obstáculo (intransitable) | Negro |
| `1` | Terreno básico — costo 1 | Café claro |
| `2` | Vegetación — costo 2 | Verde |
| `3` | Terreno pesado — costo 3 | Café oscuro |

El **inicio** se fija automáticamente en la primera celda transitable (esquina superior izquierda) y el **destino** en la última (esquina inferior derecha).

### Ejemplo de mapa 5×5

```
1 1 0 1 1
1 0 0 0 1
1 1 2 0 1
0 0 2 1 1
1 1 2 1 1
```

Para agregar un mapa propio, basta con crear un nuevo `.txt` con el mismo formato y pasarlo con `--mapa`.

---

## Algoritmos implementados

### A* (`--algoritmo astar`)

Búsqueda informada con función de costo `f(n) = g(n) + h(n)`.

- **g(n):** costo acumulado real desde el inicio hasta el nodo `n`.
- **h(n):** heurística admisible de Distancia Manhattan hasta el destino.
- Garantiza el camino de **costo mínimo** cuando la heurística no sobreestima.

**Colores en pantalla:**

| Elemento | Color |
|---|---|
| Nodos en la frontera (cola abierta) | Azul claro |
| Nodos ya expandidos (cola cerrada) | Azul oscuro |
| Camino final | Amarillo |
| Inicio | Verde brillante |
| Destino | Rojo brillante |

### ACO — Colonia de Hormigas (`--algoritmo aco`)

Metaheurística bio-inspirada basada en el comportamiento de hormigas reales.

- Cada hormiga construye un camino de inicio a destino usando **selección probabilística por ruleta** ponderada por feromona (`τ^α`) y heurística (`η^β = (1/costo)^β`).
- Al final de cada iteración: las feromonas se **evaporan** globalmente (`×(1−ρ)`) y las hormigas que llegaron al destino depositan feromona proporcional a `Q / costo_camino`.
- El resultado es **heurístico**: no garantiza el óptimo, pero converge a soluciones de buena calidad.

**Parámetros ACO por defecto:**

| Parámetro | Valor | Significado |
|---|---|---|
| α (alfa) | 1.0 | Peso de la feromona |
| β (beta) | 2.0 | Peso de la heurística |
| ρ (rho) | 0.1 | Tasa de evaporación |
| Q | 100.0 | Constante de depósito |

**Colores en pantalla:**

| Elemento | Color |
|---|---|
| Mapa de calor de feromonas | Rojo con transparencia (más intenso = más feromona) |
| Mejor camino encontrado hasta la iteración actual | Amarillo |

---

## Arquitectura de animación

Los algoritmos están implementados como **generadores Python** (`yield`). El ciclo principal de pygame avanza la búsqueda llamando `next(generador)` en cada frame, lo que permite repintar la ventana entre cada paso sin bloquear la interfaz.

```
Frame N:  next(gen) → expande nodo / itera colonia → yield estado
Frame N+1: pygame repinta con el estado recibido
Frame N+2: next(gen) → ...
```

Esto significa que la animación no usa hilos ni temporizadores artificiales: la velocidad visual es simplemente la de ejecución del algoritmo.

---

## Métricas en consola

Al cerrar la ventana, `main.py` imprime una tabla con:

- **Tiempo de ejecución computacional** (en milisegundos, sin contar el tiempo que la ventana estuvo abierta).
- **Nodos expandidos** (A*) o **iteraciones de la colonia** (ACO).
- **Costo total** de la ruta encontrada.

Ejemplo de salida:

```
==================================================
  RESULTADOS - A* (Manhattan)
==================================================
  Tiempo de ejecucion          0.4044 ms
  --------------------------------------------------
  Nodos expandidos             70
  --------------------------------------------------
  Costo total de la ruta       18.0
==================================================
```

---

## Controles de la ventana

| Acción | Efecto |
|---|---|
| Cerrar ventana (×) | Termina la simulación |
| `ESC` | Termina la simulación |

La ventana permanece abierta al finalizar el algoritmo hasta que el usuario la cierre manualmente.

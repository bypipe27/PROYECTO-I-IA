import random
import string
from collections import deque


# =============================================================================
# 1. GENERAR GRAFO DAG DESAFIANTE
# =============================================================================
def generar_grafo_dag(n=13, densidad=0.45):
    """
    Genera un grafo dirigido acíclico (DAG) aleatorio con estructura
    desafiante para el Escape Room Solver.

    Parámetros ajustados respecto a la versión anterior:
      - n=13 en lugar de 11: más nodos dan más recorrido al BFS/DFS y
        permiten que haya más nodos bloqueados sin agotar el grafo.
      - densidad=0.45 en lugar de 0.3: más aristas cruzadas crean
        rutas alternativas que hacen visible la diferencia entre BFS y
        DFS, y obligan al algoritmo a decidir qué camino explorar primero.

    Estructura de construcción (4 pasos garantizan conectividad y desafío):
      1. Camino troncal A→B→...→M: garantiza que siempre exista al
         menos un camino completo de inicio a fin.
      2. Atajos largos (salto 2-5): crean rutas cortas que BFS puede
         preferir sobre el camino troncal.
      3. Aristas cruzadas densas: aumentan las bifurcaciones que el
         algoritmo debe evaluar.
      4. Aristas de rescate: evitan que nodos intermedios queden como
         callejones sin salida, lo que haría el grafo trivial.
    """
    nodos = list(string.ascii_uppercase[:n])
    grafo = {nodo: [] for nodo in nodos}

    # PASO 1: camino troncal — garantiza que siempre haya solución
    for i in range(len(nodos) - 1):
        grafo[nodos[i]].append(nodos[i + 1])

    # PASO 2: atajos largos hacia adelante (salto de 2 a 5 posiciones)
    # Permiten rutas alternativas más cortas en número de saltos
    for i in range(len(nodos) - 1):
        max_salto = min(len(nodos) - i - 1, 5)
        for _ in range(random.randint(0, 3)):
            if max_salto >= 2:
                salto   = random.randint(2, max_salto)
                destino = nodos[i + salto]
                if destino not in grafo[nodos[i]]:
                    grafo[nodos[i]].append(destino)

    # PASO 3: aristas cruzadas con mayor densidad
    # Crean bifurcaciones que hacen más visible el comportamiento del
    # algoritmo de búsqueda al elegir qué camino explorar primero
    for i in range(len(nodos) - 2):
        if random.random() < densidad:
            posibles = [nodos[j] for j in range(i + 2, min(i + 6, len(nodos)))]
            if posibles:
                destino = random.choice(posibles)
                if destino not in grafo[nodos[i]]:
                    grafo[nodos[i]].append(destino)

    # PASO 4: aristas de rescate — ningún nodo intermedio sin salida
    for i in range(len(nodos) - 1):
        if not grafo[nodos[i]]:
            grafo[nodos[i]].append(nodos[i + 1])

    return grafo, nodos[0], nodos[-1]


# =============================================================================
# 2. GENERAR NODOS BLOQUEADOS DE FORMA ESTRATÉGICA
# =============================================================================
def generar_bloqueados(grafo, inicio, objetivo, max_bloqueados=5):
    """
    Selecciona nodos bloqueados de forma estratégica para maximizar el
    desafío y la visibilidad de las funcionalidades del proyecto.

    Cambios respecto a la versión anterior (random.sample puro):
      - Se identifican los nodos con mayor tráfico entrante (in-degree),
        es decir, aquellos a los que llegan más aristas. Bloquear estos
        nodos obliga al algoritmo a resolver más puzzles antes de avanzar,
        ya que son cruces importantes del grafo.
      - Se garantiza que al menos la mitad de los bloqueados sean nodos
        de alto tráfico, haciendo los puzzles más relevantes para la
        búsqueda global.
      - Se mantiene un mínimo de 3 y un máximo de 5 bloqueados para
        que siempre haya suficiente actividad de A* visible.
    """
    nodos      = list(grafo.keys())
    candidatos = [n for n in nodos if n != inicio and n != objetivo]

    # Calcular in-degree de cada nodo candidato
    in_degree = {n: 0 for n in candidatos}
    for origen in grafo:
        for destino in grafo[origen]:
            if destino in in_degree:
                in_degree[destino] += 1

    # Separar candidatos en alta prioridad (≥2 aristas entrantes) y resto
    alta_prioridad = [n for n, d in in_degree.items() if d >= 2]
    resto          = [n for n in candidatos if n not in alta_prioridad]

    cantidad = random.randint(3, min(max_bloqueados, len(candidatos) // 2))

    # Garantizar al menos la mitad de los bloqueados con alto tráfico
    n_alta = min(len(alta_prioridad), max(cantidad // 2, 1))
    elegidos_alta = random.sample(alta_prioridad, n_alta) if alta_prioridad else []

    # Completar con nodos del resto si hacen falta
    n_resto  = cantidad - len(elegidos_alta)
    elegidos_resto = random.sample(resto, min(n_resto, len(resto))) if resto else []

    return set(elegidos_alta + elegidos_resto)

# =========================
# 3. ANÁLISIS DEL GRAFO
# # =========================
# def analizar_grafo(grafo):
#     """
#     Analiza propiedades estructurales del grafo
#     """
#     print("\n=== ANÁLISIS DEL GRAFO ===")
    
#     # In-degree (cuántas aristas llegan)
#     in_degree = {nodo: 0 for nodo in grafo}
#     for origen in grafo:
#         for destino in grafo[origen]:
#             in_degree[destino] += 1
    
#     # Out-degree (cuántas aristas salen)
#     out_degree = {nodo: len(vecinos) for nodo, vecinos in grafo.items()}
    
#     # Nodos fuente (sin predecesores)
#     fuentes = [n for n, deg in in_degree.items() if deg == 0]
    
#     # Nodos sumidero (sin sucesores)
#     sumideros = [n for n, deg in out_degree.items() if deg == 0]
    
#     # Nodos de alto tráfico (muchos predecesores)
#     alto_trafico = sorted(in_degree.items(), key=lambda x: x[1], reverse=True)[:3]
    
#     print(f"Nodos fuente (sin predecesores): {fuentes}")
#     print(f"Nodos sumidero (sin sucesores): {sumideros}")
#     print(f"Nodos con más tráfico entrante: {alto_trafico}")
    
#     # Contar aristas totales
#     total_aristas = sum(len(vecinos) for vecinos in grafo.values())
#     print(f"Total de aristas: {total_aristas}")
#     print(f"Densidad promedio: {total_aristas / len(grafo):.2f} aristas/nodo")

# =========================
# 4. VISUALIZACIÓN DEL GRAFO
# =========================
def visualizar_grafo(grafo, bloqueados=None, camino=None):
    """
    Muestra el grafo en formato legible con decoradores
    """
    print("\n=== ESTRUCTURA DEL GRAFO ===")
    
    for nodo, vecinos in grafo.items():
        # Decorar nodos especiales
        decorador = ""
        if bloqueados and nodo in bloqueados:
            decorador = " 🚫 [BLOQUEADO]"
        elif camino and nodo in camino:
            decorador = " ✅ [EN CAMINO]"
        
        vecinos_str = ", ".join(vecinos) if vecinos else "(sin salida)"
        print(f"{nodo}{decorador} → {vecinos_str}")

# =========================
# 5. EJECUCIÓN PRINCIPAL
# =========================
if __name__ == "__main__":
    
    # Generar grafo
    grafo, inicio, objetivo = generar_grafo_dag(n=11, densidad=0.3)
    
    # Generar bloqueados
    bloqueados = generar_bloqueados(grafo, inicio, objetivo)
    
    # Mostrar configuración
    print(f"\n🎯 Inicio: {inicio}")
    print(f"🏁 Objetivo: {objetivo}")
    print(f"🚫 Nodos bloqueados: {sorted(bloqueados)}")
    
    # Analizar grafo
    #analizar_grafo(grafo)
    
    # Visualizar grafo
    visualizar_grafo(grafo, bloqueados)
    
    from logica.busqueda import bfs

    # Ejecutar BFS
    print("\n" + "=" * 60)
    print("EJECUTANDO BFS")
    print("=" * 60)
    
    resultado = bfs(grafo, inicio, objetivo, bloqueados)
    
    # Mostrar resultados
    print("\n" + "=" * 60)
    print("RESULTADOS")
    print("=" * 60)
    
    if resultado["exito"]:
        print(f"✅ Camino encontrado: {' → '.join(resultado['camino'])}")
        print(f"   Longitud del camino: {len(resultado['camino'])} nodos")
    else:
        print("❌ No se encontró camino al objetivo")
    
    print(f"\n📊 MÉTRICAS:")
    print(f"   Nodos expandidos: {resultado['nodos_expandidos']}")
    print(f"   Profundidad máxima alcanzada: {resultado['profundidad']}")
    print(f"   Tiempo de ejecución: {resultado['tiempo']:.6f} segundos")
    print(f"   Bloqueados encontrados: {resultado['bloqueados_encontrados']}")
    
    # Visualizar el camino encontrado
    if resultado["exito"]:
        visualizar_grafo(grafo, bloqueados, resultado["camino"])
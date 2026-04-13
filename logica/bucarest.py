import heapq
import math
import random
import time


class Ciudad:
    """Representa una ciudad con nombre y coordenadas."""

    def __init__(self, nombre, x, y):
        self.nombre = nombre
        self.x = x
        self.y = y

    def __repr__(self):
        return f"{self.nombre}({self.x},{self.y})"


def distancia_euclidiana(ciudad1, ciudad2):
    dx = ciudad1.x - ciudad2.x
    dy = ciudad1.y - ciudad2.y
    return math.sqrt(dx**2 + dy**2)


def heuristica(ciudad_actual, ciudad_meta, ciudades):
    return distancia_euclidiana(ciudades[ciudad_actual], ciudades[ciudad_meta])


def generar_grafo_ciudades(num_ciudades=7, ancho=500, alto=400, min_costo=20, max_costo=150):
    nombres_ciudades = [
        "Arad", "Bucarest", "Craiova", "Dobreta", "Eforie",
        "Fagaras", "Giurgiu", "Hirsova", "Iasi", "Lugoj",
        "Mehadia", "Neamt", "Oradea", "Pitesti", "Rimnicu",
        "Sibiu", "Timisoara", "Urziceni", "Vaslui", "Zerind",
    ]

    nombres = random.sample(nombres_ciudades, num_ciudades)

    ciudades = {}
    inicio_nombre = nombres[0]
    meta_nombre = nombres[-1]

    ciudades[inicio_nombre] = Ciudad(inicio_nombre, random.randint(0, 50), random.randint(alto - 50, alto))
    ciudades[meta_nombre] = Ciudad(meta_nombre, random.randint(ancho - 50, ancho), random.randint(0, 50))

    for nombre in nombres[1:-1]:
        ciudades[nombre] = Ciudad(nombre, random.randint(50, ancho - 50), random.randint(50, alto - 50))

    grafo = {nombre: {} for nombre in nombres}

    ciudades_conectadas = [inicio_nombre]
    ciudades_restantes = nombres[1:]

    while ciudades_restantes:
        origen = random.choice(ciudades_conectadas)
        destino = random.choice(ciudades_restantes)
        dist = distancia_euclidiana(ciudades[origen], ciudades[destino])
        costo = max(min_costo, min(int(dist * 0.5) + random.randint(-20, 20), max_costo))

        grafo[origen][destino] = costo
        grafo[destino][origen] = costo

        ciudades_conectadas.append(destino)
        ciudades_restantes.remove(destino)

    num_aristas_extra = random.randint(num_ciudades, num_ciudades * 2)
    for _ in range(num_aristas_extra):
        origen, destino = random.sample(nombres, 2)
        if destino in grafo[origen]:
            continue

        dist = distancia_euclidiana(ciudades[origen], ciudades[destino])
        costo = max(min_costo, min(int(dist * 0.5) + random.randint(-20, 20), max_costo))

        grafo[origen][destino] = costo
        grafo[destino][origen] = costo

    return grafo, ciudades, inicio_nombre, meta_nombre


def reconstruir_camino(origen, destino, padres):
    camino = [destino]
    while camino[-1] != origen:
        camino.append(padres[camino[-1]])
    camino.reverse()
    return camino


def calcular_costo_camino(camino, grafo):
    if len(camino) < 2:
        return 0

    costo_total = 0
    for indice in range(len(camino) - 1):
        costo_total += grafo[camino[indice]][camino[indice + 1]]
    return costo_total


def a_star(grafo, ciudades, inicio, meta):
    frontera = []
    heapq.heappush(frontera, (heuristica(inicio, meta, ciudades), 0, inicio))

    padres = {}
    g_mejor = {inicio: 0}
    visitados = set()

    inicio_tiempo = time.time()

    while frontera:
        _, costo_actual, ciudad = heapq.heappop(frontera)

        if ciudad in visitados:
            continue

        visitados.add(ciudad)

        if ciudad == meta:
            camino = reconstruir_camino(inicio, meta, padres)
            return {
                "algoritmo": "A*",
                "camino": camino,
                "costo": costo_actual,
                "nodos_expandidos": len(visitados),
                "tiempo": time.time() - inicio_tiempo,
            }

        for vecino, costo in grafo[ciudad].items():
            nuevo_g = costo_actual + costo
            if nuevo_g < g_mejor.get(vecino, float("inf")):
                g_mejor[vecino] = nuevo_g
                padres[vecino] = ciudad
                nuevo_f = nuevo_g + heuristica(vecino, meta, ciudades)
                heapq.heappush(frontera, (nuevo_f, nuevo_g, vecino))

    return None


def generar_subproblema_bucarest(clave, ancho=500, alto=320, min_costo=20, max_costo=150):
    rng = random

    nombres_ciudades = [
        "Arad", "Bucarest", "Craiova", "Dobreta", "Eforie",
        "Fagaras", "Giurgiu", "Hirsova", "Iasi", "Lugoj",
        "Mehadia", "Neamt", "Oradea", "Pitesti", "Rimnicu",
        "Sibiu", "Timisoara", "Urziceni", "Vaslui", "Zerind",
    ]

    meta_nombre = "Bucarest"
    inicio_nombre = rng.choice([nombre for nombre in nombres_ciudades if nombre != meta_nombre])

    candidatos = [
        nombre for nombre in nombres_ciudades
        if nombre not in {inicio_nombre, meta_nombre}
    ]
    intermedios = rng.sample(candidatos, rng.randint(2, 4))
    nombres = [inicio_nombre] + intermedios + [meta_nombre]

    ciudades = {}
    ciudades[inicio_nombre] = Ciudad(
        inicio_nombre,
        rng.randint(0, 50),
        rng.randint(alto - 50, alto),
    )
    ciudades[meta_nombre] = Ciudad(
        meta_nombre,
        rng.randint(ancho - 50, ancho),
        rng.randint(0, 50),
    )

    for nombre in intermedios:
        ciudades[nombre] = Ciudad(
            nombre,
            rng.randint(70, ancho - 70),
            rng.randint(70, alto - 70),
        )

    grafo_local = {nombre: [] for nombre in nombres}

    for indice in range(len(nombres) - 1):
        origen = nombres[indice]
        destino = nombres[indice + 1]
        dist = distancia_euclidiana(ciudades[origen], ciudades[destino])
        costo = max(min_costo, min(int(dist * 0.5) + rng.randint(-2, 4), max_costo))
        grafo_local[origen].append((destino, costo))

    for indice in range(len(nombres) - 2):
        max_salto = len(nombres) - indice - 1
        if max_salto >= 2 and rng.random() < 0.6:
            salto = rng.randint(2, max_salto)
            origen = nombres[indice]
            destino = nombres[indice + salto]
            if destino not in [vecino for vecino, _ in grafo_local[origen]]:
                dist = distancia_euclidiana(ciudades[origen], ciudades[destino])
                costo = max(min_costo, min(int(dist * 0.5) + rng.randint(-2, 4), max_costo))
                grafo_local[origen].append((destino, costo))

    return grafo_local, ciudades, inicio_nombre, meta_nombre


def astar_subproblema_pasos(nodo_bloqueado):
    grafo_local, ciudades, inicio, objetivo = generar_subproblema_bucarest(nodo_bloqueado)
    heuristica_local = {
        nodo: distancia_euclidiana(ciudad, ciudades[objetivo])
        for nodo, ciudad in ciudades.items()
    }

    inicio_tiempo = time.time()

    yield {
        "tipo": "local_inicio",
        "inicio": inicio,
        "objetivo": objetivo,
        "grafo_local": grafo_local,
        "heuristica": heuristica_local,
    }

    frontera = [(heuristica_local[inicio], 0, inicio, [inicio])]
    mejor_costo = {inicio: 0}
    visitados = set()
    expandidos = 0

    while frontera:
        f_actual, g_actual, nodo, camino = heapq.heappop(frontera)

        if nodo in visitados:
            continue

        visitados.add(nodo)
        expandidos += 1

        yield {
            "tipo": "local_expandir",
            "nodo": nodo,
            "g": g_actual,
            "f": f_actual,
            "camino": camino,
        }

        if nodo == objetivo:
            yield {
                "tipo": "local_fin",
                "resultado": {
                    "exito": True,
                    "camino": camino,
                    "nodos_expandidos": expandidos,
                    "costo_total": g_actual,
                    "tiempo": time.time() - inicio_tiempo,
                    "inicio": inicio,
                    "objetivo": objetivo,
                    "grafo_local": grafo_local,
                    "heuristica": heuristica_local,
                },
            }
            return

        for vecino, costo in grafo_local.get(nodo, []):
            nuevo_g = g_actual + costo
            if nuevo_g < mejor_costo.get(vecino, float("inf")):
                mejor_costo[vecino] = nuevo_g
                nuevo_f = nuevo_g + heuristica_local.get(vecino, 0)
                heapq.heappush(frontera, (nuevo_f, nuevo_g, vecino, camino + [vecino]))
                yield {
                    "tipo": "local_descubrir",
                    "vecino": vecino,
                    "g": nuevo_g,
                    "f": nuevo_f,
                }

    yield {
        "tipo": "local_fin",
        "resultado": {
            "exito": False,
            "camino": None,
            "nodos_expandidos": expandidos,
            "costo_total": 0,
            "tiempo": time.time() - inicio_tiempo,
            "inicio": inicio,
            "objetivo": objetivo,
            "grafo_local": grafo_local,
            "heuristica": heuristica_local,
        },
    }


def mostrar_grafo(grafo, ciudades):
    print("\nGrafo generado:\n")
    for ciudad in sorted(grafo.keys()):
        coord = ciudades[ciudad]
        print(f"{ciudad} [{coord.x}, {coord.y}]")
        for vecino, costo in sorted(grafo[ciudad].items()):
            print(f"  -> {vecino}: {costo}")


def mostrar_heuristica(ciudades, meta):
    print("\nHeuristica a la meta:\n")
    for nombre, ciudad in sorted(ciudades.items(), key=lambda item: heuristica(item[0], meta, ciudades)):
        print(f"{nombre}: {heuristica(nombre, meta, ciudades):.2f}")


def mostrar_resultado(resultado):
    if not resultado:
        print("No se encontro camino.")
        return

    print("\nResultado A*:\n")
    print("Camino:", " -> ".join(resultado["camino"]))
    print("Costo total:", resultado["costo"])
    print("Nodos expandidos:", resultado["nodos_expandidos"])
    print(f"Tiempo: {resultado['tiempo'] * 1000:.4f} ms")


if __name__ == "__main__":
    grafo, ciudades, inicio, meta = generar_grafo_ciudades(
        num_ciudades=7,
        ancho=500,
        alto=400,
        min_costo=20,
        max_costo=150,
    )

    print("Inicio:", inicio)
    print("Meta:", meta)

    mostrar_grafo(grafo, ciudades)
    mostrar_heuristica(ciudades, meta)

    resultado = a_star(grafo, ciudades, inicio, meta)
    mostrar_resultado(resultado)
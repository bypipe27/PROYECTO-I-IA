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


def generar_subproblema_bucarest(clave,ancho=500, alto=320, min_costo=20, max_costo=150):
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

    inicio_tiempo = time.time()

    # Para mantener compatibilidad con la interfaz, generamos un diccionario heuristica igual al anterior
    heuristica_dict = {nodo: heuristica(nodo, objetivo, ciudades) for nodo in ciudades}

    yield {
        "tipo": "local_inicio",
        "inicio": inicio,
        "objetivo": objetivo,
        "grafo_local": grafo_local,
        "heuristica": heuristica_dict,
    }

    frontera = [(heuristica(inicio, objetivo, ciudades), 0, inicio, [inicio])]
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
                    "heuristica": heuristica_dict,
                },
            }
            return

        for vecino, costo in grafo_local.get(nodo, []):
            nuevo_g = g_actual + costo
            if nuevo_g < mejor_costo.get(vecino, float("inf")):
                mejor_costo[vecino] = nuevo_g
                nuevo_f = nuevo_g + heuristica(vecino, objetivo, ciudades)
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
            "heuristica": heuristica_dict,
        },
    }



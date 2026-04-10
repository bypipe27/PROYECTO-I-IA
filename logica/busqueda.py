from collections import deque
import heapq
import time


def _registrar_bloqueado(vecino, nodos_bloqueados_encontrados):
	if vecino not in nodos_bloqueados_encontrados:
		nodos_bloqueados_encontrados.append(vecino)


def _resultado(camino, nodos_expandidos, max_profundidad, inicio_tiempo, nodos_bloqueados_encontrados, exito):
	return {
		"camino": camino,
		"nodos_expandidos": nodos_expandidos,
		"profundidad": max_profundidad,
		"tiempo": time.time() - inicio_tiempo,
		"bloqueados_encontrados": nodos_bloqueados_encontrados,
		"exito": exito,
	}


def _crear_subproblema(nodo_bloqueado):
	inicio = f"{nodo_bloqueado}_S"
	objetivo = f"{nodo_bloqueado}_G"
	p1 = f"{nodo_bloqueado}_P1"
	p2 = f"{nodo_bloqueado}_P2"

	base = ord(nodo_bloqueado) - ord("A") + 1
	costo_directo = 3 + (base % 3)
	costo_atajo_1 = 1 + (base % 2)
	costo_atajo_2 = 2

	grafo_local = {
		inicio: [(p1, costo_atajo_1), (p2, costo_directo)],
		p1: [(objetivo, costo_atajo_2)],
		p2: [(objetivo, 2 + (base % 2))],
		objetivo: [],
	}

	heuristica = {
		inicio: 2,
		p1: 1,
		p2: 2,
		objetivo: 0,
	}

	return grafo_local, inicio, objetivo, heuristica


def resolver_subproblema_astar(nodo_bloqueado):
	grafo_local, inicio, objetivo, heuristica = _crear_subproblema(nodo_bloqueado)
	inicio_tiempo = time.time()
	eventos = []

	frontera = [(heuristica[inicio], 0, inicio, [inicio])]
	mejor_costo = {inicio: 0}
	visitados = set()
	expandidos = 0

	while frontera:
		f_actual, g_actual, nodo, camino = heapq.heappop(frontera)
		if nodo in visitados:
			continue

		visitados.add(nodo)
		expandidos += 1
		eventos.append(f"Expandiendo {nodo} (g={g_actual}, f={f_actual})")

		if nodo == objetivo:
			return {
				"exito": True,
				"camino": camino,
				"nodos_expandidos": expandidos,
				"costo_total": g_actual,
				"tiempo": time.time() - inicio_tiempo,
				"inicio": inicio,
				"objetivo": objetivo,
				"eventos": eventos,
			}

		for vecino, costo in grafo_local.get(nodo, []):
			nuevo_costo = g_actual + costo
			if nuevo_costo < mejor_costo.get(vecino, float("inf")):
				mejor_costo[vecino] = nuevo_costo
				prioridad = nuevo_costo + heuristica.get(vecino, 0)
				heapq.heappush(frontera, (prioridad, nuevo_costo, vecino, camino + [vecino]))
				eventos.append(f"Descubierto {vecino} (g={nuevo_costo}, f={prioridad})")

	return {
		"exito": False,
		"camino": None,
		"nodos_expandidos": expandidos,
		"costo_total": 0,
		"tiempo": time.time() - inicio_tiempo,
		"inicio": inicio,
		"objetivo": objetivo,
		"eventos": eventos,
	}


def _recorrer_pasos(grafo, inicio, objetivo, bloqueados=None, modo="bfs"):
	bloqueados = bloqueados or set()
	es_anchura = modo == "bfs"
	if es_anchura:
		frontera = deque([(inicio, [inicio], 0)])
		extraer = frontera.popleft
		agregar = frontera.append
	else:
		frontera = [(inicio, [inicio], 0)]
		extraer = frontera.pop
		agregar = frontera.append

	visitados = set()
	en_frontera = {inicio}
	nodos_expandidos = 0
	max_profundidad = 0
	nodos_bloqueados_encontrados = []
	inicio_tiempo = time.time()
	encontrado = False
	camino_encontrado = None
	subproblemas_resueltos = 0
	subproblemas_fallidos = 0
	total_expandidos_local = 0
	total_costo_local = 0

	while frontera:
		nodo, camino, profundidad = extraer()
		en_frontera.discard(nodo)

		if nodo in visitados:
			yield {
				"tipo": "saltear",
				"nodo": nodo,
				"camino": camino,
				"profundidad": profundidad,
				"visitados": set(visitados),
				"frontera": set(en_frontera),
			}
			continue

		visitados.add(nodo)
		nodos_expandidos += 1
		max_profundidad = max(max_profundidad, profundidad)
		yield {
			"tipo": "expandir",
			"nodo": nodo,
			"camino": camino,
			"profundidad": profundidad,
			"visitados": set(visitados),
			"frontera": set(en_frontera),
		}

		if nodo == objetivo:
			encontrado = True
			camino_encontrado = camino
			yield {
				"tipo": "objetivo",
				"nodo": nodo,
				"camino": camino,
				"profundidad": profundidad,
				"visitados": set(visitados),
				"frontera": set(en_frontera),
			}
			break

		vecinos = list(grafo.get(nodo, []))
		if not es_anchura:
			vecinos = list(reversed(vecinos))

		for vecino in vecinos:
			if vecino in bloqueados:
				_registrar_bloqueado(vecino, nodos_bloqueados_encontrados)
				yield {
					"tipo": "bloqueado",
					"nodo": nodo,
					"vecino": vecino,
					"camino": camino,
					"profundidad": profundidad,
					"visitados": set(visitados),
					"frontera": set(en_frontera),
				}

				resultado_local = resolver_subproblema_astar(vecino)
				yield {
					"tipo": "subproblema_inicio",
					"nodo": nodo,
					"vecino": vecino,
					"inicio_local": resultado_local["inicio"],
					"objetivo_local": resultado_local["objetivo"],
				}

				for evento in resultado_local["eventos"]:
					yield {
						"tipo": "subproblema_evento",
						"vecino": vecino,
						"mensaje": evento,
					}

				total_expandidos_local += resultado_local["nodos_expandidos"]
				total_costo_local += resultado_local["costo_total"]

				if resultado_local["exito"]:
					subproblemas_resueltos += 1
					bloqueados.discard(vecino)
					yield {
						"tipo": "desbloqueado",
						"nodo": nodo,
						"vecino": vecino,
						"resultado_local": resultado_local,
					}

					if vecino not in visitados and vecino not in en_frontera:
						agregar((vecino, camino + [vecino], profundidad + 1))
						en_frontera.add(vecino)
						yield {
							"tipo": "descubrir",
							"nodo": nodo,
							"vecino": vecino,
							"camino": camino,
							"camino_vecino": camino + [vecino],
							"profundidad": profundidad + 1,
							"visitados": set(visitados),
							"frontera": set(en_frontera),
						}
				else:
					subproblemas_fallidos += 1
					yield {
						"tipo": "subproblema_fallido",
						"nodo": nodo,
						"vecino": vecino,
						"resultado_local": resultado_local,
					}

				continue

			if vecino not in visitados and vecino not in en_frontera:
				agregar((vecino, camino + [vecino], profundidad + 1))
				en_frontera.add(vecino)
				yield {
					"tipo": "descubrir",
					"nodo": nodo,
					"vecino": vecino,
					"camino": camino,
					"camino_vecino": camino + [vecino],
					"profundidad": profundidad + 1,
					"visitados": set(visitados),
					"frontera": set(en_frontera),
				}

	yield {
		"tipo": "fin",
		"camino": camino_encontrado,
		"nodos_expandidos": nodos_expandidos,
		"profundidad": max_profundidad,
		"tiempo": time.time() - inicio_tiempo,
		"bloqueados_encontrados": nodos_bloqueados_encontrados,
		"exito": encontrado,
		"subproblemas_resueltos": subproblemas_resueltos,
		"subproblemas_fallidos": subproblemas_fallidos,
		"expandidos_local_total": total_expandidos_local,
		"costo_local_total": total_costo_local,
		"visitados": set(visitados),
		"frontera": set(en_frontera),
	}


def bfs_pasos(grafo, inicio, objetivo, bloqueados=None):
	yield from _recorrer_pasos(grafo, inicio, objetivo, bloqueados, modo="bfs")


def dfs_pasos(grafo, inicio, objetivo, bloqueados=None):
	yield from _recorrer_pasos(grafo, inicio, objetivo, bloqueados, modo="dfs")


def _resolver(generator):
	ultimo = None
	for ultimo in generator:
		pass
	if ultimo is None:
		return _resultado(None, 0, 0, time.time(), [], False)
	if ultimo.get("tipo") == "fin":
		return ultimo
	if ultimo.get("tipo") == "objetivo":
		return {
			"camino": ultimo["camino"],
			"nodos_expandidos": ultimo.get("nodos_expandidos", 0),
			"profundidad": ultimo.get("profundidad", 0),
			"tiempo": ultimo.get("tiempo", 0.0),
			"bloqueados_encontrados": ultimo.get("bloqueados_encontrados", []),
			"exito": True,
		}
	return ultimo


def bfs(grafo, inicio, objetivo, bloqueados=None):
	return _resolver(bfs_pasos(grafo, inicio, objetivo, bloqueados))


def dfs(grafo, inicio, objetivo, bloqueados=None):
	return _resolver(dfs_pasos(grafo, inicio, objetivo, bloqueados))
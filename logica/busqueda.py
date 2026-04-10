from collections import deque
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
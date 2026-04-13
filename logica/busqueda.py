from collections import deque
import time

from logica.bucarest import astar_subproblema_pasos


def _resultado(camino, nodos_expandidos, max_profundidad, inicio_tiempo,
				   nodos_bloqueados_encontrados, exito):
	return {
		"camino": camino,
		"nodos_expandidos": nodos_expandidos,
		"profundidad": max_profundidad,
		"tiempo": time.time() - inicio_tiempo,
		"bloqueados_encontrados": nodos_bloqueados_encontrados,
		"exito": exito,
	}


def _recorrer_pasos(grafo, inicio, objetivo, bloqueados=None, modo="bfs"):
	bloqueados_activos = set(bloqueados) if bloqueados else set()
	ya_desbloqueados = set()
	nodos_bloqueados_encontrados = []
	subproblemas_resueltos = 0
	subproblemas_fallidos = 0
	expandidos_local_total = 0
	costo_local_total = 0

	es_anchura = (modo == "bfs")
	if es_anchura:
		frontera = deque([(inicio, [inicio], 0)])
		extraer = frontera.popleft
		agregar = frontera.append
	else:
		frontera = [(inicio, [inicio], 0)]
		extraer = frontera.pop
		agregar = frontera.append

	visitados              = set()
	en_frontera            = {inicio}
	nodos_expandidos       = 0
	max_profundidad        = 0
	inicio_tiempo          = time.time()
	encontrado             = False
	camino_encontrado      = None

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
			if vecino in bloqueados_activos and vecino not in ya_desbloqueados:
				if vecino not in nodos_bloqueados_encontrados:
					nodos_bloqueados_encontrados.append(vecino)

				yield {"tipo": "bloqueado", "nodo": nodo, "vecino": vecino,
					   "camino": camino, "profundidad": profundidad,
					   "visitados": set(visitados), "frontera": set(en_frontera)}

				resultado_local = None
				for paso_local in astar_subproblema_pasos(vecino):
					tipo_local = paso_local["tipo"]

					if tipo_local == "local_inicio":
						yield {"tipo": "subproblema_inicio", "nodo": nodo, "vecino": vecino,
						       "inicio_local": paso_local["inicio"],
						       "objetivo_local": paso_local["objetivo"],
						       "resultado_local": paso_local}
					elif tipo_local == "local_expandir":
						yield {"tipo": "subproblema_evento", "vecino": vecino,
						       "mensaje": f"Expandiendo {paso_local['nodo']} "
						                  f"(g={paso_local['g']:.2f}, f={paso_local['f']:.2f})"}
					elif tipo_local == "local_descubrir":
						yield {"tipo": "subproblema_evento", "vecino": vecino,
						       "mensaje": f"  → Descubierto {paso_local['vecino']} "
						                  f"(g={paso_local['g']:.2f}, f={paso_local['f']:.2f})"}
					elif tipo_local == "local_fin":
						resultado_local = paso_local["resultado"]

				if resultado_local is None:
					resultado_local = {
						"exito": False,
						"nodos_expandidos": 0,
						"costo_total": 0,
						"camino": None,
					}

				expandidos_local_total += resultado_local["nodos_expandidos"]
				costo_local_total += resultado_local["costo_total"]

				if resultado_local["exito"]:
					subproblemas_resueltos += 1
					bloqueados_activos.discard(vecino)
					ya_desbloqueados.add(vecino)
					yield {"tipo": "desbloqueado", "nodo": nodo, "vecino": vecino,
					       "resultado_local": resultado_local}

					if vecino not in visitados and vecino not in en_frontera:
						agregar((vecino, camino + [vecino], profundidad + 1))
						en_frontera.add(vecino)
						yield {"tipo": "descubrir", "nodo": nodo, "vecino": vecino,
						       "camino": camino, "camino_vecino": camino + [vecino],
						       "profundidad": profundidad + 1, "visitados": set(visitados),
						       "frontera": set(en_frontera)}
				else:
					subproblemas_fallidos += 1
					yield {"tipo": "subproblema_fallido", "nodo": nodo, "vecino": vecino,
					       "resultado_local": resultado_local}
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
		"tipo":                   "fin",
		"camino":                 camino_encontrado,
		"nodos_expandidos":       nodos_expandidos,
		"profundidad":            max_profundidad,
		"tiempo":                 time.time() - inicio_tiempo,
		"bloqueados_encontrados": nodos_bloqueados_encontrados,
		"exito":                  encontrado,
		"subproblemas_resueltos": subproblemas_resueltos,
		"subproblemas_fallidos":  subproblemas_fallidos,
		"expandidos_local_total": expandidos_local_total,
		"costo_local_total":      costo_local_total,
		"visitados":              set(visitados),
		"frontera":               set(en_frontera),
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
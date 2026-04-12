from collections import deque
import heapq
import time


def _registrar_bloqueado(vecino, nodos_bloqueados_encontrados):
	if vecino not in nodos_bloqueados_encontrados:
		nodos_bloqueados_encontrados.append(vecino)


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


def _crear_subproblema(nodo_bloqueado):
	inicio   = f"{nodo_bloqueado}_S"
	objetivo = f"{nodo_bloqueado}_G"
	p1       = f"{nodo_bloqueado}_P1"
	p2       = f"{nodo_bloqueado}_P2"

	base           = ord(nodo_bloqueado[0]) - ord("A") + 1
	costo_directo  = 3 + (base % 3)
	costo_atajo_1  = 1 + (base % 2)
	costo_atajo_2  = 2

	grafo_local = {
		inicio:   [(p1, costo_atajo_1), (p2, costo_directo)],
		p1:       [(objetivo, costo_atajo_2)],
		p2:       [(objetivo, 2 + (base % 2))],
		objetivo: [],
	}

	heuristica = {
		inicio:   2,
		p1:       1,
		p2:       2,
		objetivo: 0,
	}

	return grafo_local, inicio, objetivo, heuristica


def astar_pasos(nodo_bloqueado):
	"""
	Generador A* paso a paso para el subproblema de un nodo bloqueado.
	Cada expansión produce un yield independiente, permitiendo que la UI
	muestre cada paso con su propio tick del timer en lugar de ejecutar
	todo el algoritmo de golpe antes de devolver el control.

	Tipos de eventos emitidos:
	  - "local_inicio"   : metadatos del subproblema (grafo, heurística)
	  - "local_expandir" : se expande un nodo del subgrafo
	  - "local_descubrir": se añade un vecino a la frontera local
	  - "local_fin"      : resultado final (exito/fracaso) con estadísticas
	"""
	grafo_local, inicio, objetivo, heuristica = _crear_subproblema(nodo_bloqueado)
	inicio_tiempo = time.time()

	# Primer yield: metadatos para que la UI dibuje el subgrafo inmediatamente
	yield {
		"tipo":        "local_inicio",
		"inicio":      inicio,
		"objetivo":    objetivo,
		"grafo_local": grafo_local,
		"heuristica":  heuristica,
	}

	frontera    = [(heuristica[inicio], 0, inicio, [inicio])]
	mejor_costo = {inicio: 0}
	visitados   = set()
	expandidos  = 0
	resultado   = None

	while frontera:
		f_actual, g_actual, nodo, camino = heapq.heappop(frontera)

		if nodo in visitados:
			continue

		visitados.add(nodo)
		expandidos += 1

		# Un yield por cada nodo expandido — el timer lo muestra paso a paso
		yield {
			"tipo":   "local_expandir",
			"nodo":   nodo,
			"g":      g_actual,
			"f":      f_actual,
			"camino": camino,
		}

		if nodo == objetivo:
			resultado = {
				"exito":            True,
				"camino":           camino,
				"nodos_expandidos": expandidos,
				"costo_total":      g_actual,
				"tiempo":           time.time() - inicio_tiempo,
				"inicio":           inicio,
				"objetivo":         objetivo,
				"grafo_local":      grafo_local,
				"heuristica":       heuristica,
			}
			break

		for vecino, costo in grafo_local.get(nodo, []):
			nuevo_costo = g_actual + costo
			if nuevo_costo < mejor_costo.get(vecino, float("inf")):
				mejor_costo[vecino] = nuevo_costo
				prioridad = nuevo_costo + heuristica.get(vecino, 0)
				heapq.heappush(frontera, (prioridad, nuevo_costo, vecino, camino + [vecino]))
				yield {
					"tipo":     "local_descubrir",
					"vecino":   vecino,
					"g":        nuevo_costo,
					"f":        prioridad,
				}

	if resultado is None:
		resultado = {
			"exito":            False,
			"camino":           None,
			"nodos_expandidos": expandidos,
			"costo_total":      0,
			"tiempo":           time.time() - inicio_tiempo,
			"inicio":           inicio,
			"objetivo":         objetivo,
			"grafo_local":      grafo_local,
			"heuristica":       heuristica,
		}

	yield {"tipo": "local_fin", "resultado": resultado}


def _recorrer_pasos(grafo, inicio, objetivo, bloqueados=None, modo="bfs"):
	bloqueados_activos = set(bloqueados) if bloqueados else set()
	ya_desbloqueados   = set()

	es_anchura = (modo == "bfs")
	if es_anchura:
		frontera = deque([(inicio, [inicio], 0)])
		extraer  = frontera.popleft
		agregar  = frontera.append
	else:
		frontera = [(inicio, [inicio], 0)]
		extraer  = frontera.pop
		agregar  = frontera.append

	visitados              = set()
	en_frontera            = {inicio}
	nodos_expandidos       = 0
	max_profundidad        = 0
	nodos_bloqueados_enc   = []
	inicio_tiempo          = time.time()
	encontrado             = False
	camino_encontrado      = None
	subproblemas_resueltos = 0
	subproblemas_fallidos  = 0
	total_expandidos_local = 0
	total_costo_local      = 0

	while frontera:
		nodo, camino, profundidad = extraer()
		en_frontera.discard(nodo)

		if nodo in visitados:
			yield {"tipo": "saltear", "nodo": nodo, "camino": camino,
				   "profundidad": profundidad, "visitados": set(visitados),
				   "frontera": set(en_frontera)}
			continue

		visitados.add(nodo)
		nodos_expandidos += 1
		max_profundidad   = max(max_profundidad, profundidad)

		yield {"tipo": "expandir", "nodo": nodo, "camino": camino,
			   "profundidad": profundidad, "visitados": set(visitados),
			   "frontera": set(en_frontera)}

		if nodo == objetivo:
			encontrado        = True
			camino_encontrado = camino
			yield {"tipo": "objetivo", "nodo": nodo, "camino": camino,
				   "profundidad": profundidad, "visitados": set(visitados),
				   "frontera": set(en_frontera)}
			break

		vecinos = list(grafo.get(nodo, []))
		if not es_anchura:
			vecinos = list(reversed(vecinos))

		for vecino in vecinos:

			# --- Nodo bloqueado que todavía no fue resuelto ---
			if vecino in bloqueados_activos and vecino not in ya_desbloqueados:
				_registrar_bloqueado(vecino, nodos_bloqueados_enc)

				# Avisar a la UI que encontramos un nodo bloqueado
				yield {"tipo": "bloqueado", "nodo": nodo, "vecino": vecino,
					   "camino": camino, "profundidad": profundidad,
					   "visitados": set(visitados), "frontera": set(en_frontera)}

				# Ejecutar A* como generador paso a paso.
				# Cada yield llega a la UI como un tick independiente del timer,
				# así la búsqueda global se detiene visualmente mientras el
				# subproblema se resuelve nodo por nodo.
				resultado_local = None
				for paso_local in astar_pasos(vecino):
					tipo_local = paso_local["tipo"]

					if tipo_local == "local_inicio":
						# Primer paso: la UI dibuja el subgrafo
						yield {"tipo": "subproblema_inicio", "nodo": nodo, "vecino": vecino,
							   "inicio_local": paso_local["inicio"],
							   "objetivo_local": paso_local["objetivo"],
							   "resultado_local": paso_local}

					elif tipo_local == "local_expandir":
						yield {"tipo": "subproblema_evento", "vecino": vecino,
							   "mensaje": f"Expandiendo {paso_local['nodo']} "
							              f"(g={paso_local['g']}, f={paso_local['f']})"}

					elif tipo_local == "local_descubrir":
						yield {"tipo": "subproblema_evento", "vecino": vecino,
							   "mensaje": f"  → Descubierto {paso_local['vecino']} "
							              f"(g={paso_local['g']}, f={paso_local['f']})"}

					elif tipo_local == "local_fin":
						resultado_local = paso_local["resultado"]

				total_expandidos_local += resultado_local["nodos_expandidos"]
				total_costo_local      += resultado_local["costo_total"]

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

			# --- Nodo ya desbloqueado previamente ---
			if vecino in ya_desbloqueados:
				if vecino not in visitados and vecino not in en_frontera:
					agregar((vecino, camino + [vecino], profundidad + 1))
					en_frontera.add(vecino)
					yield {"tipo": "descubrir", "nodo": nodo, "vecino": vecino,
						   "camino": camino, "camino_vecino": camino + [vecino],
						   "profundidad": profundidad + 1, "visitados": set(visitados),
						   "frontera": set(en_frontera)}
				continue

			# --- Nodo libre normal ---
			if vecino not in visitados and vecino not in en_frontera:
				agregar((vecino, camino + [vecino], profundidad + 1))
				en_frontera.add(vecino)
				yield {"tipo": "descubrir", "nodo": nodo, "vecino": vecino,
					   "camino": camino, "camino_vecino": camino + [vecino],
					   "profundidad": profundidad + 1, "visitados": set(visitados),
					   "frontera": set(en_frontera)}

	yield {
		"tipo":                   "fin",
		"camino":                 camino_encontrado,
		"nodos_expandidos":       nodos_expandidos,
		"profundidad":            max_profundidad,
		"tiempo":                 time.time() - inicio_tiempo,
		"bloqueados_encontrados": nodos_bloqueados_enc,
		"exito":                  encontrado,
		"subproblemas_resueltos": subproblemas_resueltos,
		"subproblemas_fallidos":  subproblemas_fallidos,
		"expandidos_local_total": total_expandidos_local,
		"costo_local_total":      total_costo_local,
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
			"camino":                  ultimo["camino"],
			"nodos_expandidos":        ultimo.get("nodos_expandidos", 0),
			"profundidad":             ultimo.get("profundidad", 0),
			"tiempo":                  ultimo.get("tiempo", 0.0),
			"bloqueados_encontrados":  ultimo.get("bloqueados_encontrados", []),
			"exito":                   True,
		}
	return ultimo


def bfs(grafo, inicio, objetivo, bloqueados=None):
	return _resolver(bfs_pasos(grafo, inicio, objetivo, bloqueados))


def dfs(grafo, inicio, objetivo, bloqueados=None):
	return _resolver(dfs_pasos(grafo, inicio, objetivo, bloqueados))

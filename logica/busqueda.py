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
	"""
	Genera un subgrafo aleatorio único para el acertijo de cada nodo bloqueado.

	Antes, todos los subgrafos tenían exactamente la misma estructura:
	4 nodos fijos con 2 rutas paralelas. Eso hacía que el panel A* siempre
	se viera igual sin importar qué nodo se estaba desbloqueando.

	Ahora cada subgrafo se genera de forma aleatoria con:
	  - Entre 2 y 4 nodos intermedios (distinto número cada vez)
	  - Aristas aleatorias hacia adelante entre intermedios (estructura libre)
	  - Costos aleatorios entre 1 y 6 en cada arista
	  - Se garantiza que el objetivo siempre es alcanzable desde el inicio,
	    conectando en cadena los nodos y luego añadiendo aristas extra al azar

	Esto hace que cada puzzle sea visualmente distinto y conceptualmente
	propio del nodo que lo generó, cumpliendo con el requisito del proyecto
	de que cada nodo bloqueado tenga su propio subespacio de estados.

	Usamos random.seed basado en el nombre del nodo para que el mismo nodo
	bloqueado siempre genere el mismo puzzle dentro de una misma ejecución,
	evitando que el subgrafo cambie si el nodo se encuentra más de una vez.
	"""
	import random

	# Semilla fija por nodo: el mismo nodo bloqueado siempre da el mismo puzzle
	rng = random.Random(hash(nodo_bloqueado) & 0xFFFF)

	inicio   = f"{nodo_bloqueado}_S"
	objetivo = f"{nodo_bloqueado}_G"

	# Número aleatorio de nodos intermedios: entre 2 y 4
	n_intermedios = rng.randint(2, 4)
	intermedios   = [f"{nodo_bloqueado}_N{i+1}" for i in range(n_intermedios)]

	# Todos los nodos del subgrafo en orden de inicio a objetivo
	todos = [inicio] + intermedios + [objetivo]

	# Inicializar grafo vacío
	grafo_local = {nodo: [] for nodo in todos}

	# PASO 1: cadena troncal inicio → N1 → N2 → ... → objetivo
	# Garantiza que siempre exista al menos un camino completo
	for i in range(len(todos) - 1):
		costo = rng.randint(1, 6)
		grafo_local[todos[i]].append((todos[i + 1], costo))

	# PASO 2: aristas adicionales aleatorias hacia adelante
	# Saltan al menos 2 posiciones para crear atajos interesantes
	# (igual que en el grafo global, pero a escala pequeña)
	for i in range(len(todos) - 1):
		max_salto = len(todos) - i - 1
		if max_salto >= 2:
			# Con probabilidad 0.5 se agrega un atajo desde este nodo
			if rng.random() < 0.5:
				salto   = rng.randint(2, max_salto)
				destino = todos[i + salto]
				# Evitar duplicados
				if destino not in [v for v, _ in grafo_local[todos[i]]]:
					costo = rng.randint(1, 6)
					grafo_local[todos[i]].append((destino, costo))

	return grafo_local, inicio, objetivo


def _calcular_heuristica(grafo_local, objetivo):
	"""
	Heurística: Distancia de aristas mínimas hasta el objetivo
	            multiplicada por el costo mínimo de arista del subgrafo.

	Nombre formal: heurística de costo mínimo acumulado por saltos (o
	               'uniform-cost lower bound'), una variante de la
	               heurística de distancia de saltos ponderada.

	Fórmula aplicada:
	    h(n) = saltos_minimos(n → objetivo) × costo_minimo_arista

	Dónde:
	    - saltos_minimos: número de aristas en el camino más corto
	      (en cantidad de pasos, sin considerar costos) desde n
	      hasta el objetivo. Se obtiene con un BFS inverso desde
	      el objetivo recorriendo el grafo con aristas invertidas.
	    - costo_minimo_arista: el menor costo encontrado entre todas
	      las aristas del subgrafo. Es el "piso" del costo por paso.

	Por qué es admisible:
	    El costo real de cualquier camino desde n hasta el objetivo
	    nunca puede ser menor que (saltos necesarios × costo mínimo
	    por salto). Al usar el mínimo nunca sobreestimamos, lo que
	    garantiza que A* encuentre siempre la solución óptima.

	Por qué es mejor que la heurística fija anterior:
	    La anterior asignaba valores fijos (2, 1, 2, 0) sin relación
	    con la estructura real del grafo. Esta se calcula a partir
	    del grafo generado, por lo que se adapta a cualquier subgrafo
	    sin importar sus costos o su topología.
	"""
	# --- Paso 1: encontrar el costo mínimo de arista en todo el subgrafo ---
	costo_minimo = float("inf")
	for vecinos in grafo_local.values():
		for (_, costo) in vecinos:
			if costo < costo_minimo:
				costo_minimo = costo
	# Si el grafo no tiene aristas (solo el nodo objetivo), el costo mínimo es 0
	if costo_minimo == float("inf"):
		costo_minimo = 0

	# --- Paso 2: BFS inverso desde el objetivo para contar saltos mínimos ---
	# Construimos el grafo con aristas invertidas para recorrerlo
	# "hacia atrás" desde el objetivo
	grafo_inv = {}
	for u, vecinos in grafo_local.items():
		for (v, _) in vecinos:
			grafo_inv.setdefault(v, []).append(u)

	saltos = {objetivo: 0}
	cola   = deque([objetivo])
	while cola:
		nodo = cola.popleft()
		for predecesor in grafo_inv.get(nodo, []):
			if predecesor not in saltos:
				saltos[predecesor] = saltos[nodo] + 1
				cola.append(predecesor)

	# --- Paso 3: h(n) = saltos_minimos(n) × costo_minimo ---
	# Los nodos sin camino al objetivo reciben infinito para que A*
	# no los considere como rutas válidas
	heuristica = {}
	for nodo in grafo_local:
		if nodo in saltos:
			heuristica[nodo] = saltos[nodo] * costo_minimo
		else:
			heuristica[nodo] = float("inf")

	return heuristica


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
	grafo_local, inicio, objetivo = _crear_subproblema(nodo_bloqueado)
	# Calcular la heurística a partir de la estructura real del subgrafo
	heuristica = _calcular_heuristica(grafo_local, objetivo)
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

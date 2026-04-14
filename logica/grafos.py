import random
import string

# =========================
# 1. GENERAR GRAFO DAG MEJORADO (11 nodos)
# =========================
def generar_grafo_dag(n=11, densidad=0.3):
    nodos = list(string.ascii_uppercase[:n])
    grafo = {nodo: [] for nodo in nodos}
    
    # PASO 1: Crear camino principal desde A hasta K
    for i in range(len(nodos) - 1):
        grafo[nodos[i]].append(nodos[i + 1])
    
    # PASO 2: Agregar aristas adicionales (solo hacia adelante, evita ciclos)
    for i in range(len(nodos) - 1):
        # Calcular cuántos saltos adelante puede alcanzar
        max_salto = min(len(nodos) - i - 1, 4)  # Máximo 4 niveles adelante
        
        # Determinar número de aristas adicionales
        num_aristas_extra = random.randint(0, 2)
        
        for _ in range(num_aristas_extra):
            # Saltar al menos 2 posiciones (para crear atajos interesantes)
            if max_salto >= 2:
                salto = random.randint(2, max_salto)
                destino = nodos[i + salto]
                
                # Agregar solo si no existe ya (evitar duplicados)
                if destino not in grafo[nodos[i]]:
                    grafo[nodos[i]].append(destino)
    
    # PASO 3: Agregar algunas conexiones cruzadas para densidad
    for i in range(len(nodos) - 2):
        if random.random() < densidad:
            # Conectar a un nodo en el "siguiente nivel"
            posibles = [nodos[j] for j in range(i + 2, min(i + 5, len(nodos)))]
            if posibles:
                destino = random.choice(posibles)
                if destino not in grafo[nodos[i]]:
                    grafo[nodos[i]].append(destino)
    
    # PASO 4: Asegurar que ningún nodo intermedio quede como sumidero
    # (excepto el último)
    for i in range(len(nodos) - 1):
        if not grafo[nodos[i]]:
            # Si un nodo no tiene salidas, conectarlo al siguiente
            grafo[nodos[i]].append(nodos[i + 1])
    
    inicio = nodos[0]
    objetivo = nodos[-1]
    
    return grafo, inicio, objetivo

# =========================
# 2. NODOS BLOQUEADOS (2 a 5) - MEJORADO
# =========================
def generar_bloqueados(grafo, inicio, objetivo, max_bloqueados=5):
    
    nodos = list(grafo.keys())
    candidatos = [n for n in nodos if n != inicio and n != objetivo]
    
    # Evitar bloquear demasiados nodos críticos
    cantidad = random.randint(2, min(max_bloqueados, len(candidatos) // 2))
    bloqueados = set(random.sample(candidatos, cantidad))
    
    return bloqueados


# =========================
# 3. VISUALIZACIÓN DEL GRAFO
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


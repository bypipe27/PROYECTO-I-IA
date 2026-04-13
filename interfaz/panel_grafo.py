import math

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygonF
from PyQt5.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsPolygonItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# ---------------------------------------------------------------------------
# Paleta de colores — 4 estados de nodo + amarillo para el actual
# ---------------------------------------------------------------------------
COLOR_INICIO     = QColor("#4CAF50")   # verde    — nodo inicial
COLOR_OBJETIVO   = QColor("#EF5350")   # rojo     — nodo objetivo / final
COLOR_DISPONIBLE = QColor("#42A5F5")   # azul     — disponible, desbloqueado, frontera, visitado
COLOR_BLOQUEADO  = QColor("#90A4AE")   # gris     — bloqueado (sin resolver)
COLOR_ACTUAL     = QColor("#FDD835")   # amarillo — nodo expandiéndose ahora
COLOR_BORDE      = QColor("#FFFFFF")
COLOR_ARISTA     = QColor("#B0BEC5")
COLOR_FONDO      = QColor("#FAFAFA")

# El subgrafo A* reutiliza la misma paleta
COLOR_SUB_ARISTA = QColor("#90A4AE")

RADIO         = 20
SEPARACION_X  = 140
SEPARACION_Y  = 100


# ---------------------------------------------------------------------------
# Componentes gráficos compartidos
# ---------------------------------------------------------------------------

class NodoItem(QGraphicsEllipseItem):
    def __init__(self, nodo_id: str, x: float, y: float, color: QColor):
        super().__init__(-RADIO, -RADIO, RADIO * 2, RADIO * 2)
        self.setPos(x, y)
        self._label = QGraphicsTextItem(nodo_id, self)
        self._label.setFont(QFont("Monospace", 9, QFont.Bold))
        self._label.setDefaultTextColor(Qt.GlobalColor.white)
        rect = self._label.boundingRect()
        self._label.setPos(-rect.width() / 2, -rect.height() / 2)
        self.actualizar_color(color)

    def actualizar_color(self, color: QColor):
        self.setBrush(QBrush(color))
        self.setPen(QPen(COLOR_BORDE, 2))


def _dibujar_flecha(scene: QGraphicsScene, x1, y1, x2, y2,
                    color: QColor = None, peso: str = ""):
    """Dibuja una arista con punta de flecha y etiqueta de costo opcional."""
    color = color or COLOR_ARISTA
    dx, dy = x2 - x1, y2 - y1
    dist = math.hypot(dx, dy)
    if dist == 0:
        return

    ux, uy = dx / dist, dy / dist
    sx, sy = x1 + ux * RADIO, y1 + uy * RADIO
    ex, ey = x2 - ux * RADIO, y2 - uy * RADIO

    linea = QGraphicsLineItem(sx, sy, ex, ey)
    linea.setPen(QPen(color, 1.5))
    scene.addItem(linea)

    angulo = math.atan2(ey - sy, ex - sx)
    tam = 10
    p1 = QPointF(ex + tam * math.cos(angulo + math.radians(150)),
                 ey + tam * math.sin(angulo + math.radians(150)))
    p2 = QPointF(ex + tam * math.cos(angulo - math.radians(150)),
                 ey + tam * math.sin(angulo - math.radians(150)))
    punta = QGraphicsPolygonItem(QPolygonF([QPointF(ex, ey), p1, p2]))
    punta.setBrush(QBrush(color))
    punta.setPen(QPen(Qt.PenStyle.NoPen))
    scene.addItem(punta)

    # Etiqueta de costo sobre la arista
    if peso:
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        lbl = QGraphicsTextItem(str(peso))
        lbl.setFont(QFont("Monospace", 8))
        lbl.setDefaultTextColor(QColor("#455A64"))
        lbl.setPos(mx - lbl.boundingRect().width() / 2,
                   my - lbl.boundingRect().height() / 2 - 8)
        scene.addItem(lbl)


def _calcular_posiciones(grafo: dict) -> dict:
    from collections import deque
    inicio = next(iter(grafo))
    nivel  = {inicio: 0}
    cola   = deque([inicio])
    while cola:
        nodo = cola.popleft()
        for vecino in grafo.get(nodo, []):
            if isinstance(vecino, tuple):
                vecino = vecino[0]
            if vecino not in nivel:
                nivel[vecino] = nivel[nodo] + 1
                cola.append(vecino)

    por_nivel = {}
    for nodo, niv in nivel.items():
        por_nivel.setdefault(niv, []).append(nodo)

    posiciones = {}
    for niv, nodos in por_nivel.items():
        total = len(nodos)
        for i, nodo in enumerate(sorted(nodos)):
            posiciones[nodo] = (
                niv * SEPARACION_X + 60,
                (i - (total - 1) / 2) * SEPARACION_Y + 300,
            )
    return posiciones


# ---------------------------------------------------------------------------
# Panel del grafo global (BFS / DFS)
# ---------------------------------------------------------------------------

class PanelGrafo(QWidget):
    def __init__(self, titulo: str = "Grafo de búsqueda", parent=None):
        super().__init__(parent)
        self._items = {}
        self._scene = QGraphicsScene()
        self._scene.setBackgroundBrush(QBrush(COLOR_FONDO))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        titulo_lbl = QLabel(titulo)
        titulo_lbl.setStyleSheet(
            "color:#212121;font-family:'Ubuntu';font-size:12px;font-weight:bold;"
        )
        layout.addWidget(titulo_lbl)

        self._view = QGraphicsView(self._scene)
        self._view.setRenderHint(QPainter.Antialiasing)
        self._view.setStyleSheet("border:1px solid #E0E0E0;background:#FAFAFA;")
        self._view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self._view)

        layout.addWidget(self._crear_leyenda())
        self.mostrar_vacio()

    def _crear_leyenda(self):
        lbl = QLabel(
            "<span style='color:#4CAF50'>●</span> Inicio &nbsp;"
            "<span style='color:#FDD835'>●</span> Actual &nbsp;"
            "<span style='color:#42A5F5'>●</span> Disponible &nbsp;"
            "<span style='color:#90A4AE'>●</span> Bloqueado &nbsp;"
            "<span style='color:#EF5350'>●</span> Objetivo"
        )
        lbl.setStyleSheet(
            "color:#616161;font-family:'Ubuntu';font-size:9px;"
            "padding:6px;background:#F5F5F5;border-radius:4px;"
        )
        lbl.setTextFormat(Qt.TextFormat.RichText)
        return lbl

    def mostrar_vacio(self, mensaje: str = "Selecciona algoritmo e inicia"):
        self._scene.clear()
        self._items.clear()
        texto = QGraphicsTextItem(mensaje)
        texto.setFont(QFont("Ubuntu", 13))
        texto.setDefaultTextColor(QColor("#BDBDBD"))
        texto.setPos(0, 0)
        self._scene.addItem(texto)
        rect = self._scene.itemsBoundingRect()
        if rect.isValid():
            self._view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    def cargar_grafo(self, grafo: dict, inicio: str, objetivo: str, bloqueados: set):
        try:
            self._scene.clear()
            self._items.clear()
            posiciones = _calcular_posiciones(grafo)

            for origen, vecinos in grafo.items():
                x1, y1 = posiciones[origen]
                for destino in vecinos:
                    if destino in posiciones:
                        x2, y2 = posiciones[destino]
                        _dibujar_flecha(self._scene, x1, y1, x2, y2)

            for nodo, (x, y) in posiciones.items():
                if nodo == inicio:
                    color = COLOR_INICIO
                elif nodo == objetivo:
                    color = COLOR_OBJETIVO
                elif nodo in bloqueados:
                    color = COLOR_BLOQUEADO
                else:
                    color = COLOR_DISPONIBLE

                item = NodoItem(nodo, x, y, color)
                self._scene.addItem(item)
                self._items[nodo] = item

            self._ajustar_vista()
        except Exception:
            pass

    def actualizar_nodo(self, nodo_id: str, estado: str):
        try:
            if nodo_id not in self._items:
                return
            colores = {
                "actual":        COLOR_ACTUAL,
                "disponible":    COLOR_DISPONIBLE,
                "frontera":      COLOR_DISPONIBLE,
                "visitado":      COLOR_DISPONIBLE,
                "bloqueado":     COLOR_BLOQUEADO,
                "desbloqueado":  COLOR_DISPONIBLE,
                "inicio":        COLOR_INICIO,
                "objetivo":      COLOR_OBJETIVO,
            }
            self._items[nodo_id].actualizar_color(colores.get(estado, COLOR_DISPONIBLE))
        except Exception:
            pass

    def marcar_camino(self, camino):
        if not camino:
            return
        try:
            for nodo in camino[1:-1]:
                if nodo in self._items:
                    self._items[nodo].actualizar_color(COLOR_DISPONIBLE)
        except Exception:
            pass

    def _ajustar_vista(self):
        rect = self._scene.itemsBoundingRect()
        if rect.isValid():
            self._view.fitInView(rect.adjusted(-20, -20, 20, 20),
                                 Qt.AspectRatioMode.KeepAspectRatio)


# ---------------------------------------------------------------------------
# Panel del subgrafo de Bucarest (A*)
# ---------------------------------------------------------------------------

class PanelSubgrafo(QWidget):
    """
    Muestra el subgrafo de Bucarest como un grafo de ciudades con costos y
    heurística, sin coordenadas visibles ni apariencia de mapa.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items      = {}
        self._scene      = QGraphicsScene()
        self._scene.setBackgroundBrush(QBrush(QColor("#F8F9FA")))
        self._grafo_local = {}
        self._heuristica  = {}
        self._inicio_local = ""
        self._obj_local    = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._titulo_lbl = QLabel("Problema de Bucarest — A*")
        self._titulo_lbl.setStyleSheet(
            "color:#212121;font-family:'Ubuntu';font-size:12px;font-weight:bold;"
        )
        layout.addWidget(self._titulo_lbl)

        self._view = QGraphicsView(self._scene)
        self._view.setRenderHint(QPainter.Antialiasing)
        self._view.setStyleSheet("border:1px solid #E0E0E0;background:#F8F9FA;")
        self._view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self._view)

        self._mostrar_placeholder()

    def _mostrar_placeholder(self):
        self._scene.clear()
        self._items.clear()
        texto = QGraphicsTextItem("Esperando nodo bloqueado...")
        texto.setFont(QFont("Ubuntu", 11))
        texto.setDefaultTextColor(QColor("#BDBDBD"))
        texto.setPos(10, 10)
        self._scene.addItem(texto)
        rect = self._scene.itemsBoundingRect()
        if rect.isValid():
            self._view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    def cargar_subgrafo(self, resultado_local: dict, nodo_bloqueado: str):
        """
        Recibe el resultado_local del A* de Bucarest y dibuja el subgrafo
        completo con costos en aristas y heurística por nodo.
        """
        self._grafo_local  = resultado_local.get("grafo_local", {})
        self._heuristica   = resultado_local.get("heuristica", {})
        self._inicio_local = resultado_local.get("inicio", "")
        self._obj_local    = resultado_local.get("objetivo", "")

        self._titulo_lbl.setText(
            f"Problema de Bucarest — A*   (desbloqueando: {nodo_bloqueado})"
        )
        self._redibujar()

    def _redibujar(self):
        self._scene.clear()
        self._items.clear()

        if not self._grafo_local:
            self._mostrar_placeholder()
            return

        # Posiciones por niveles para que el grafo se lea de izquierda a derecha
        posiciones = self._calcular_pos_subgrafo()

        # Dibujar aristas con costos
        for origen, vecinos in self._grafo_local.items():
            if origen not in posiciones:
                continue
            x1, y1 = posiciones[origen]
            for (destino, costo) in vecinos:
                if destino in posiciones:
                    x2, y2 = posiciones[destino]
                    _dibujar_flecha(self._scene, x1, y1, x2, y2,
                                    color=COLOR_SUB_ARISTA, peso=str(costo))

        # Dibujar nodos
        for nodo, (x, y) in posiciones.items():
            if nodo == self._inicio_local:
                color = COLOR_INICIO
            elif nodo == self._obj_local:
                color = COLOR_OBJETIVO
            else:
                color = COLOR_DISPONIBLE

            item = NodoItem(nodo, x, y, color)
            self._scene.addItem(item)
            self._items[nodo] = item

            # Heurística debajo del nodo
            h_val = self._heuristica.get(nodo, "")
            if h_val != "":
                h_lbl = QGraphicsTextItem(f"h={h_val:.2f}")
                h_lbl.setFont(QFont("Monospace", 7))
                h_lbl.setDefaultTextColor(QColor("#607D8B"))
                h_lbl.setPos(x - 15, y + RADIO + 2)
                self._scene.addItem(h_lbl)

        self._ajustar_vista()

    def _calcular_pos_subgrafo(self) -> dict:
        """
        Distribución por niveles para que el subgrafo se vea como grafo
        dirigido y no como un mapa cartesiano.
        """
        from collections import deque
        if not self._inicio_local:
            return {}

        nivel = {self._inicio_local: 0}
        cola  = deque([self._inicio_local])
        while cola:
            n = cola.popleft()
            for (v, _) in self._grafo_local.get(n, []):
                if v not in nivel:
                    nivel[v] = nivel[n] + 1
                    cola.append(v)

        por_nivel = {}
        for nodo, niv in nivel.items():
            por_nivel.setdefault(niv, []).append(nodo)

        posiciones = {}
        sep_x = 120
        sep_y = 70
        cx    = 60
        for niv, nodos in por_nivel.items():
            total = len(nodos)
            for i, nodo in enumerate(sorted(nodos)):
                posiciones[nodo] = (
                    niv * sep_x + cx,
                    (i - (total - 1) / 2) * sep_y + 90,
                )
        return posiciones

    def _ajustar_vista(self):
        rect = self._scene.itemsBoundingRect()
        if rect.isValid():
            self._view.fitInView(rect.adjusted(-20, -20, 20, 20),
                                 Qt.AspectRatioMode.KeepAspectRatio)

    def limpiar(self):
        self._grafo_local  = {}
        self._heuristica   = {}
        self._inicio_local = ""
        self._obj_local    = ""
        self._titulo_lbl.setText("Problema de Bucarest — A*")
        self._mostrar_placeholder()



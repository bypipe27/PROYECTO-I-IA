import math

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPolygonF
from PyQt5.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsPolygonItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


# Paleta de colores moderna y minimalista
COLOR_INICIO = QColor("#4CAF50")
COLOR_OBJETIVO = QColor("#FF5252")
COLOR_VISITADO = QColor("#42A5F5")
COLOR_ACTUAL = QColor("#FFB74D")
COLOR_FRONTERA = QColor("#26C6DA")
COLOR_BLOQUEADO = QColor("#90A4AE")
COLOR_DEFAULT = QColor("#78909C")
COLOR_BORDE = QColor("#FFFFFF")
COLOR_ARISTA = QColor("#B0BEC5")
COLOR_FONDO = QColor("#FAFAFA")

RADIO = 20
SEPARACION_X = 140
SEPARACION_Y = 100


class NodoItem(QGraphicsEllipseItem):
    def __init__(self, nodo_id: str, x: float, y: float, color: QColor):
        super().__init__(-RADIO, -RADIO, RADIO * 2, RADIO * 2)
        self.setPos(x, y)
        self._label = QGraphicsTextItem(nodo_id, self)
        self._label.setFont(QFont("Monospace", 11, QFont.Bold))
        self._label.setDefaultTextColor(Qt.GlobalColor.white)
        rect = self._label.boundingRect()
        self._label.setPos(-rect.width() / 2, -rect.height() / 2)
        self.actualizar_color(color)

    def actualizar_color(self, color: QColor):
        self.setBrush(QBrush(color))
        self.setPen(QPen(COLOR_BORDE, 2))


def _dibujar_flecha(scene: QGraphicsScene, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    dist = math.hypot(dx, dy)
    if dist == 0:
        return

    ux, uy = dx / dist, dy / dist
    sx, sy = x1 + ux * RADIO, y1 + uy * RADIO
    ex, ey = x2 - ux * RADIO, y2 - uy * RADIO

    linea = QGraphicsLineItem(sx, sy, ex, ey)
    linea.setPen(QPen(COLOR_ARISTA, 1.5))
    scene.addItem(linea)

    angulo = math.atan2(ey - sy, ex - sx)
    tam = 10
    p1 = QPointF(ex + tam * math.cos(angulo + math.radians(150)), ey + tam * math.sin(angulo + math.radians(150)))
    p2 = QPointF(ex + tam * math.cos(angulo - math.radians(150)), ey + tam * math.sin(angulo - math.radians(150)))
    punta = QGraphicsPolygonItem(QPolygonF([QPointF(ex, ey), p1, p2]))
    punta.setBrush(QBrush(COLOR_ARISTA))
    punta.setPen(QPen(Qt.PenStyle.NoPen))
    scene.addItem(punta)


def _calcular_posiciones(grafo: dict) -> dict:
    from collections import deque

    inicio = next(iter(grafo))
    nivel = {inicio: 0}
    cola = deque([inicio])

    while cola:
        nodo = cola.popleft()
        for vecino in grafo.get(nodo, []):
            if vecino not in nivel:
                nivel[vecino] = nivel[nodo] + 1
                cola.append(vecino)

    posiciones = {}
    por_nivel = {}
    for nodo, niv in nivel.items():
        por_nivel.setdefault(niv, []).append(nodo)

    for niv, nodos in por_nivel.items():
        total = len(nodos)
        for i, nodo in enumerate(sorted(nodos)):
            posiciones[nodo] = (niv * SEPARACION_X + 60, (i - (total - 1) / 2) * SEPARACION_Y + 300)

    return posiciones


class PanelGrafo(QWidget):
    def __init__(self, titulo: str = "Grafo de búsqueda", parent=None):
        super().__init__(parent)
        self._items = {}
        self._scene = QGraphicsScene()
        self._scene.setBackgroundBrush(QBrush(COLOR_FONDO))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        titulo_lbl = QLabel(titulo)
        titulo_lbl.setStyleSheet("color: #212121; font-family: 'Ubuntu'; font-size: 12px; font-weight: bold;")
        layout.addWidget(titulo_lbl)

        self._view = QGraphicsView(self._scene)
        self._view.setRenderHint(QPainter.Antialiasing)
        self._view.setStyleSheet("border: 1px solid #E0E0E0; background: #FAFAFA;")
        self._view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self._view)
        
        layout.addWidget(self._crear_leyenda())
        self.mostrar_vacio()

    def _crear_leyenda(self):
        lbl = QLabel(
            "<span style='color:#4CAF50'>●</span> Inicio  "
            "<span style='color:#FFB74D'>●</span> Actual  "
            "<span style='color:#26C6DA'>●</span> Frontera  "
            "<span style='color:#42A5F5'>●</span> Visitado  "
            "<span style='color:#90A4AE'>●</span> Bloqueado  "
            "<span style='color:#FF5252'>●</span> Objetivo"
        )
        lbl.setStyleSheet("color: #616161; font-family: 'Ubuntu'; font-size: 10px; padding: 8px; background: #F5F5F5; border-radius: 4px;")
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
                    color = COLOR_DEFAULT

                item = NodoItem(nodo, x, y, color)
                self._scene.addItem(item)
                self._items[nodo] = item

            rect = self._scene.itemsBoundingRect()
            if rect.isValid():
                self._view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        except Exception:
            pass

    def actualizar_nodo(self, nodo_id: str, estado: str):
        try:
            if nodo_id not in self._items:
                return
            colores = {
                "actual": COLOR_ACTUAL,
                "frontera": COLOR_FRONTERA,
                "visitado": COLOR_VISITADO,
                "bloqueado": COLOR_BLOQUEADO,
                "desbloqueado": COLOR_VISITADO,
                "inicio": COLOR_INICIO,
                "objetivo": COLOR_OBJETIVO,
            }
            self._items[nodo_id].actualizar_color(colores.get(estado, COLOR_DEFAULT))
        except Exception:
            pass

    def marcar_camino(self, camino):
        if not camino:
            return
        try:
            for nodo in camino[1:-1]:
                if nodo in self._items:
                    self._items[nodo].actualizar_color(COLOR_VISITADO)
        except Exception:
            pass
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
	QHBoxLayout,
	QComboBox,
	QLabel,
	QMainWindow,
	QPushButton,
	QSplitter,
	QTextEdit,
	QVBoxLayout,
	QWidget,
)

from interfaz.panel_grafo import PanelGrafo
from logica.busqueda import bfs_pasos, dfs_pasos
from logica.grafos import generar_bloqueados, generar_grafo_dag


class VentanaPrincipal(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("Escape Room Solver")
		self.setMinimumSize(1100, 700)
		self._grafo = {}
		self._inicio = ""
		self._objetivo = ""
		self._bloqueados = set()
		self._ultimo_resultado = None
		self._generador_busqueda = None
		self._nodo_actual = None
		self._nodos_visitados = set()
		self._timer_busqueda = QTimer(self)
		self._timer_busqueda.timeout.connect(self._avanzar_busqueda)
		self._construir_ui()
		self._preparar_partida()

	def _construir_ui(self):
		central = QWidget()
		self.setCentralWidget(central)

		root = QVBoxLayout(central)
		root.setContentsMargins(10, 10, 10, 10)
		root.setSpacing(8)

		barra = QHBoxLayout()
		titulo = QLabel("Escape Room Solver")
		titulo.setStyleSheet("font-size: 16px; font-weight: bold;")
		barra.addWidget(titulo)
		barra.addStretch()

		self._selector_algoritmo = QComboBox()
		self._selector_algoritmo.addItem("Selecciona algoritmo...", None)
		self._selector_algoritmo.addItem("Amplitud (BFS)", "bfs")
		self._selector_algoritmo.addItem("Profundidad (DFS)", "dfs")
		self._selector_algoritmo.currentIndexChanged.connect(self._actualizar_estado_inicio)
		barra.addWidget(self._selector_algoritmo)

		self._btn_start = QPushButton("Iniciar")
		self._btn_start.clicked.connect(self._ejecutar_busqueda)
		self._btn_start.setEnabled(False)
		barra.addWidget(self._btn_start)

		root.addLayout(barra)

		splitter_superior = QSplitter(Qt.Horizontal)
		splitter_superior.setChildrenCollapsible(False)

		self._panel_grafo = PanelGrafo("Grafo de prueba")
		splitter_superior.addWidget(self._panel_grafo)

		panel_derecho = QWidget()
		panel_layout = QVBoxLayout(panel_derecho)
		panel_layout.setContentsMargins(8, 8, 8, 8)
		panel_layout.setSpacing(6)

		etiqueta = QLabel("Panel derecho")
		etiqueta.setStyleSheet("font-weight: bold;")
		panel_layout.addWidget(etiqueta)
		panel_layout.addStretch()
		splitter_superior.addWidget(panel_derecho)
		splitter_superior.setSizes([760, 340])

		self._consola = QTextEdit()
		self._consola.setReadOnly(True)
		self._consola.setMinimumHeight(180)
		self._consola.setPlaceholderText("Mensajes de ejecución...")

		root.addWidget(splitter_superior)
		root.addWidget(self._consola)
		root.setStretch(1, 1)
		root.setStretch(2, 0)

	def _preparar_partida(self):
		self._consola.clear()
		self._ultimo_resultado = None
		self._grafo, self._inicio, self._objetivo = generar_grafo_dag(n=11, densidad=0.3)
		self._bloqueados = generar_bloqueados(self._grafo, self._inicio, self._objetivo)
		self._panel_grafo.mostrar_vacio()

		self._log("Selecciona un algoritmo para comenzar.")
		self._log(f"Grafo preparado: {len(self._grafo)} nodos")
		self._log(f"Inicio: {self._inicio} | Objetivo: {self._objetivo}")
		self._actualizar_estado_inicio()

	def _actualizar_estado_inicio(self):
		algoritmo = self._selector_algoritmo.currentData()
		self._btn_start.setEnabled(algoritmo is not None and not self._timer_busqueda.isActive())

	def _ejecutar_busqueda(self):
		if self._timer_busqueda.isActive():
			return

		algoritmo = self._selector_algoritmo.currentData()
		if algoritmo not in {"bfs", "dfs"}:
			self._log("Debes elegir BFS o DFS antes de iniciar.")
			return

		self._consola.clear()
		self._panel_grafo.cargar_grafo(self._grafo, self._inicio, self._objetivo, self._bloqueados)
		self._generador_busqueda = bfs_pasos(self._grafo, self._inicio, self._objetivo, self._bloqueados)
		if algoritmo == "dfs":
			self._generador_busqueda = dfs_pasos(self._grafo, self._inicio, self._objetivo, self._bloqueados)

		self._nodo_actual = None
		self._nodos_visitados = set()
		self._ultimo_resultado = None

		nombre = "AMPLITUD" if algoritmo == "bfs" else "PROFUNDIDAD"

		self._log(f"Ejecutando búsqueda en {nombre} paso a paso...")
		self._btn_start.setEnabled(False)
		self._selector_algoritmo.setEnabled(False)
		self._timer_busqueda.start(650)

	def _avanzar_busqueda(self):
		if self._generador_busqueda is None:
			self._detener_busqueda()
			return

		try:
			paso = next(self._generador_busqueda)
		except StopIteration:
			self._detener_busqueda()
			return

		tipo = paso["tipo"]

		if tipo == "expandir":
			nodo = paso["nodo"]
			self._marcar_nodo_actual(nodo)
			self._nodos_visitados.add(nodo)
			self._panel_grafo.actualizar_nodo(nodo, "actual")
			self._log(f"Expandiendo {nodo} | profundidad {paso['profundidad']}")
		elif tipo == "descubrir":
			vecino = paso["vecino"]
			self._panel_grafo.actualizar_nodo(vecino, "frontera")
			self._log(f"Se agrega {vecino} a la frontera")
		elif tipo == "bloqueado":
			vecino = paso["vecino"]
			self._panel_grafo.actualizar_nodo(vecino, "bloqueado")
			self._log(f"Nodo bloqueado detectado: {vecino}")
		elif tipo == "objetivo":
			camino = paso["camino"]
			self._log(f"Objetivo alcanzado en {paso['nodo']}")
			self._panel_grafo.marcar_camino(camino)
		elif tipo == "fin":
			self._ultimo_resultado = paso
			if paso["exito"]:
				camino = paso["camino"] or []
				self._panel_grafo.marcar_camino(camino)
				self._log(f"Camino encontrado: {' -> '.join(camino)}")
			else:
				self._log("No se encontró camino al objetivo.")

			self._log(f"Nodos expandidos: {paso['nodos_expandidos']}")
			self._log(f"Profundidad máxima: {paso['profundidad']}")
			self._log(f"Tiempo: {paso['tiempo']:.6f} s")
			self._log(f"Bloqueados encontrados: {paso['bloqueados_encontrados']}")
			self._detener_busqueda()

	def _marcar_nodo_actual(self, nodo):
		if self._nodo_actual and self._nodo_actual != nodo:
			if self._nodo_actual == self._inicio:
				self._panel_grafo.actualizar_nodo(self._nodo_actual, "inicio")
			elif self._nodo_actual == self._objetivo:
				self._panel_grafo.actualizar_nodo(self._nodo_actual, "objetivo")
			elif self._nodo_actual in self._bloqueados:
				self._panel_grafo.actualizar_nodo(self._nodo_actual, "bloqueado")
			else:
				self._panel_grafo.actualizar_nodo(self._nodo_actual, "visitado")
		self._nodo_actual = nodo

	def _detener_busqueda(self):
		self._timer_busqueda.stop()
		self._generador_busqueda = None
		self._nodo_actual = None
		self._selector_algoritmo.setEnabled(True)
		self._actualizar_estado_inicio()

	def _log(self, mensaje: str):
		self._consola.append(f"> {mensaje}")

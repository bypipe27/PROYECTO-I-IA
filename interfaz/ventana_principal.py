from PyQt5.QtCore import Qt, QSize
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont, QIcon
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
		self.setMinimumSize(950, 700)
		
		self._grafo = {}
		self._inicio = ""
		self._objetivo = ""
		self._bloqueados = set()
		self._ultimo_resultado = None
		self._generador_busqueda = None
		self._nodo_actual = None
		self._nodos_visitados = set()
		self._resueltos_local = 0
		self._fallidos_local = 0
		self._expandidos_local_total = 0
		self._costo_local_total = 0
		self._timer_busqueda = QTimer(self)
		self._timer_busqueda.timeout.connect(self._avanzar_busqueda)
		
		self._construir_ui()
		self._aplicar_estilos()
		self._preparar_partida()

	def _construir_ui(self):
		central = QWidget()
		self.setCentralWidget(central)

		root = QVBoxLayout(central)
		root.setContentsMargins(12, 12, 12, 12)
		root.setSpacing(10)

		# Barra superior con título y controles
		barra = QHBoxLayout()
		barra.setContentsMargins(0, 0, 0, 0)
		barra.setSpacing(16)
		
		titulo = QLabel("Escape Room Solver")
		titulo_font = QFont("Ubuntu", 18, QFont.Bold)
		titulo.setFont(titulo_font)
		barra.addWidget(titulo)
		barra.addStretch()

		self._selector_algoritmo = QComboBox()
		self._selector_algoritmo.addItem("Selecciona algoritmo...", None)
		self._selector_algoritmo.addItem("Amplitud (BFS)", "bfs")
		self._selector_algoritmo.addItem("Profundidad (DFS)", "dfs")
		self._selector_algoritmo.currentIndexChanged.connect(self._actualizar_estado_inicio)
		self._selector_algoritmo.setMinimumWidth(200)
		barra.addWidget(self._selector_algoritmo)

		self._btn_start = QPushButton("Iniciar")
		self._btn_start.clicked.connect(self._ejecutar_busqueda)
		self._btn_start.setEnabled(False)
		self._btn_start.setMinimumWidth(90)
		barra.addWidget(self._btn_start)

		root.addLayout(barra)

		# Divisor principal (grafo + panel derecho) - obtiene más espacio
		splitter_superior = QSplitter(Qt.Orientation.Horizontal)
		splitter_superior.setChildrenCollapsible(False)

		self._panel_grafo = PanelGrafo("Grafo de búsqueda")
		splitter_superior.addWidget(self._panel_grafo)

		# Panel derecho mejorado
		panel_derecho = QWidget()
		panel_layout = QVBoxLayout(panel_derecho)
		panel_layout.setContentsMargins(12, 12, 12, 12)
		panel_layout.setSpacing(8)

		# Información
		info_label = QLabel("Información")
		info_font = QFont("Ubuntu", 11, QFont.Bold)
		info_label.setFont(info_font)
		panel_layout.addWidget(info_label)
		
		self._info_texto = QLabel("")
		self._info_texto.setWordWrap(True)
		self._info_texto.setAlignment(Qt.AlignmentFlag.AlignTop)
		info_font_small = QFont("Ubuntu", 9)
		self._info_texto.setFont(info_font_small)
		panel_layout.addWidget(self._info_texto)

		local_label = QLabel("Puzzle local (A*)")
		local_label.setFont(info_font)
		panel_layout.addWidget(local_label)

		self._local_info_texto = QLabel("Esperando nodo bloqueado...")
		self._local_info_texto.setWordWrap(True)
		self._local_info_texto.setAlignment(Qt.AlignmentFlag.AlignTop)
		self._local_info_texto.setFont(info_font_small)
		panel_layout.addWidget(self._local_info_texto)

		self._consola_local = QTextEdit()
		self._consola_local.setReadOnly(True)
		self._consola_local.setPlaceholderText("Eventos del subproblema A*...")
		self._consola_local.setMinimumHeight(170)
		self._consola_local.setFont(QFont("Monospace", 9))
		panel_layout.addWidget(self._consola_local)
		
		panel_layout.addStretch()
		splitter_superior.addWidget(panel_derecho)
		splitter_superior.setSizes([650, 300])

		root.addWidget(splitter_superior, 1)

		# Consola de mensajes
		consola_label = QLabel("Registro de ejecución")
		consola_font = QFont("Ubuntu", 11, QFont.Bold)
		consola_label.setFont(consola_font)
		root.addWidget(consola_label)
		
		self._consola = QTextEdit()
		self._consola.setReadOnly(True)
		self._consola.setMinimumHeight(140)
		self._consola.setPlaceholderText("Mensajes de ejecución...")
		consola_edit_font = QFont("Monospace", 9)
		self._consola.setFont(consola_edit_font)

		root.addWidget(self._consola)

	def _preparar_partida(self):
		self._consola.clear()
		self._consola_local.clear()
		self._ultimo_resultado = None
		self._resueltos_local = 0
		self._fallidos_local = 0
		self._expandidos_local_total = 0
		self._costo_local_total = 0
		self._grafo, self._inicio, self._objetivo = generar_grafo_dag(n=11, densidad=0.3)
		self._bloqueados = generar_bloqueados(self._grafo, self._inicio, self._objetivo)
		self._panel_grafo.mostrar_vacio()

		self._actualizar_info()
		self._log("Selecciona un algoritmo para comenzar.")
		self._actualizar_estado_inicio()
	
	def _actualizar_info(self):
		info = f"""<b>Estado:</b> Preparado<br>
		<b>Nodos:</b> {len(self._grafo)}<br>
		<b>Inicio:</b> {self._inicio}<br>
		<b>Objetivo:</b> {self._objetivo}<br>
		<b>Bloqueados activos:</b> {len(self._bloqueados)}"""
		self._info_texto.setText(info)

		local_info = f"""<b>Resueltos:</b> {self._resueltos_local}<br>
		<b>Fallidos:</b> {self._fallidos_local}<br>
		<b>Expandidos local:</b> {self._expandidos_local_total}<br>
		<b>Costo local total:</b> {self._costo_local_total}"""
		self._local_info_texto.setText(local_info)

	def _actualizar_estado_inicio(self):
		algoritmo = self._selector_algoritmo.currentData()
		self._btn_start.setEnabled(algoritmo is not None and not self._timer_busqueda.isActive())

	def _aplicar_estilos(self):
		"""Aplica estilos modernos y minimalistas a toda la interfaz."""
		paleta = """
		QMainWindow {
			background-color: #FFFFFF;
		}
		QPushButton {
			background-color: #2196F3;
			color: white;
			border: none;
			padding: 8px 16px;
			border-radius: 4px;
			font-weight: bold;
			font-family: "Ubuntu";
		}
		QPushButton:hover {
			background-color: #1976D2;
		}
		QPushButton:pressed {
			background-color: #1565C0;
		}
		QPushButton:disabled {
			background-color: #BDBDBD;
		}
		QComboBox {
			background-color: #F5F5F5;
			color: #212121;
			border: 1px solid #E0E0E0;
			padding: 6px;
			border-radius: 4px;
			font-family: "Ubuntu";
		}
		QComboBox:hover {
			border: 1px solid #2196F3;
		}
		QTextEdit {
			background-color: #FAFAFA;
			color: #212121;
			border: 1px solid #E0E0E0;
			border-radius: 4px;
			padding: 8px;
			font-family: "Monospace";
		}
		QLabel {
			color: #212121;
			font-family: "Ubuntu";
		}
		QSplitter::handle {
			background-color: #E0E0E0;
		}
		"""
		self.setStyleSheet(paleta)

	def _ejecutar_busqueda(self):
		if self._timer_busqueda.isActive():
			return

		algoritmo = self._selector_algoritmo.currentData()
		if algoritmo not in {"bfs", "dfs"}:
			self._log("⚠️ Elige BFS o DFS antes de iniciar.")
			return

		self._consola.clear()
		self._consola_local.clear()
		self._panel_grafo.cargar_grafo(self._grafo, self._inicio, self._objetivo, self._bloqueados)
		self._generador_busqueda = bfs_pasos(self._grafo, self._inicio, self._objetivo, self._bloqueados)
		if algoritmo == "dfs":
			self._generador_busqueda = dfs_pasos(self._grafo, self._inicio, self._objetivo, self._bloqueados)

		self._nodo_actual = None
		self._nodos_visitados = set()
		self._ultimo_resultado = None
		self._resueltos_local = 0
		self._fallidos_local = 0
		self._expandidos_local_total = 0
		self._costo_local_total = 0
		self._actualizar_info()

		nombre = "AMPLITUD (BFS)" if algoritmo == "bfs" else "PROFUNDIDAD (DFS)"

		self._log(f"🔍 Iniciando búsqueda: {nombre}")
		self._btn_start.setEnabled(False)
		self._selector_algoritmo.setEnabled(False)
		self._timer_busqueda.start(650)

	def _avanzar_busqueda(self):
		if self._generador_busqueda is None:
			self._detener_busqueda()
			return

		try:
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
				self._log(f"→ Expandiendo nodo {nodo}")
			elif tipo == "descubrir":
				vecino = paso["vecino"]
				self._panel_grafo.actualizar_nodo(vecino, "frontera")
				self._log(f"◆ Nodo descubierto: {vecino}")
			elif tipo == "bloqueado":
				vecino = paso["vecino"]
				self._panel_grafo.actualizar_nodo(vecino, "bloqueado")
				self._log(f"✗ Bloqueado: {vecino}")
			elif tipo == "subproblema_inicio":
				vecino = paso["vecino"]
				self._log(f"🧩 Iniciando A* para desbloquear {vecino}")
				self._log_local(f"Inicio subproblema {vecino}: {paso['inicio_local']} -> {paso['objetivo_local']}")
			elif tipo == "subproblema_evento":
				self._log_local(paso["mensaje"])
			elif tipo == "desbloqueado":
				vecino = paso["vecino"]
				resultado_local = paso["resultado_local"]
				self._panel_grafo.actualizar_nodo(vecino, "desbloqueado")
				self._resueltos_local += 1
				self._expandidos_local_total += resultado_local["nodos_expandidos"]
				self._costo_local_total += resultado_local["costo_total"]
				self._log(f"🔓 Nodo desbloqueado: {vecino}")
				self._log_local(f"Resuelto {vecino} | costo={resultado_local['costo_total']} | expandidos={resultado_local['nodos_expandidos']}")
				self._actualizar_info()
			elif tipo == "subproblema_fallido":
				vecino = paso["vecino"]
				resultado_local = paso["resultado_local"]
				self._fallidos_local += 1
				self._log(f"❌ No se pudo desbloquear: {vecino}")
				self._log_local(f"Falló {vecino} | expandidos={resultado_local['nodos_expandidos']}")
				self._actualizar_info()
			elif tipo == "objetivo":
				camino = paso["camino"]
				self._log(f"✓ ¡Objetivo encontrado! {paso['nodo']}")
				self._panel_grafo.marcar_camino(camino)
			elif tipo == "fin":
				self._ultimo_resultado = paso
				self._resueltos_local = paso.get("subproblemas_resueltos", self._resueltos_local)
				self._fallidos_local = paso.get("subproblemas_fallidos", self._fallidos_local)
				self._expandidos_local_total = paso.get("expandidos_local_total", self._expandidos_local_total)
				self._costo_local_total = paso.get("costo_local_total", self._costo_local_total)
				if paso["exito"]:
					camino = paso["camino"] or []
					self._panel_grafo.marcar_camino(camino)
					self._log(f"✓ Camino: {' → '.join(camino)}")
				else:
					self._log("✗ No se encontró camino al objetivo.")

				self._log(f"📊 Nodos expandidos: {paso['nodos_expandidos']}")
				self._log(f"📏 Profundidad: {paso['profundidad']}")
				self._log(f"⏱️  Tiempo: {paso['tiempo']:.6f} s")
				self._log(f"🧠 Subproblemas A* resueltos: {self._resueltos_local} | fallidos: {self._fallidos_local}")
				self._actualizar_info()
				self._detener_busqueda()
		except KeyboardInterrupt:
			self._detener_busqueda()
		except Exception as e:
			self._log(f"⚠️  Error durante la búsqueda: {str(e)}")
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

	def _log_local(self, mensaje: str):
		self._consola_local.append(f"> {mensaje}")

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
	QHBoxLayout,
	QLabel,
	QMainWindow,
	QPushButton,
	QSplitter,
	QTextEdit,
	QVBoxLayout,
	QWidget,
)

from interfaz.panel_grafo import PanelGrafo
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
		self._construir_ui()
		self._generar_y_mostrar()

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

		self._btn_generar = QPushButton("Nuevo grafo")
		self._btn_generar.clicked.connect(self._generar_y_mostrar)
		barra.addWidget(self._btn_generar)

		self._btn_start = QPushButton("Iniciar")
		self._btn_start.clicked.connect(self._inicio_pendiente)
		barra.addWidget(self._btn_start)

		self._btn_reset = QPushButton("Reset")
		self._btn_reset.clicked.connect(self._generar_y_mostrar)
		barra.addWidget(self._btn_reset)

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

	def _generar_y_mostrar(self):
		self._consola.clear()
		self._grafo, self._inicio, self._objetivo = generar_grafo_dag(n=11, densidad=0.3)
		self._bloqueados = generar_bloqueados(self._grafo, self._inicio, self._objetivo)

		self._panel_grafo.cargar_grafo(self._grafo, self._inicio, self._objetivo, self._bloqueados)

		self._log(f"Grafo generado: {len(self._grafo)} nodos")
		self._log(f"Inicio: {self._inicio} | Objetivo: {self._objetivo}")
		self._log(f"Bloqueados: {sorted(self._bloqueados)}")

	def _inicio_pendiente(self):
		self._log("La ejecución del buscador se puede conectar después.")

	def _log(self, mensaje: str):
		self._consola.append(f"> {mensaje}")

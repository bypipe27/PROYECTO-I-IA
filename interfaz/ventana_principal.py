from PyQt5.QtCore import Qt, QSize
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
	QHBoxLayout,
	QComboBox,
    QFrame,
	QLabel,
	QMainWindow,
	QPushButton,
	QSplitter,
	QTextEdit,
	QVBoxLayout,
	QWidget,
)

from interfaz.panel_grafo import PanelGrafo, PanelSubgrafo
from logica.busqueda import bfs_pasos, dfs_pasos
from logica.grafos import generar_bloqueados, generar_grafo_dag


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Escape Room Solver")
        self.setMinimumSize(1100, 720)

        # Estado de la búsqueda
        self._grafo               = {}
        self._inicio              = ""
        self._objetivo            = ""
        self._bloqueados          = set()
        self._ultimo_resultado    = None
        self._generador_busqueda  = None
        self._nodo_actual         = None
        self._nodos_visitados     = set()

        # Estadísticas
        self._expandidos_global   = 0
        self._profundidad_global  = 0
        self._resueltos_local     = 0
        self._fallidos_local      = 0
        self._expandidos_local    = 0
        self._costo_local         = 0

        self._timer_busqueda = QTimer(self)
        self._timer_busqueda.timeout.connect(self._avanzar_busqueda)

        self._construir_ui()
        self._aplicar_estilos()
        self._preparar_partida()

    # -----------------------------------------------------------------------
    # Construcción de la UI
    # -----------------------------------------------------------------------

    def _construir_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        # ── Barra superior ──────────────────────────────────────────────────
        barra = QHBoxLayout()
        barra.setSpacing(12)

        titulo = QLabel("Escape Room Solver")
        titulo.setFont(QFont("Ubuntu", 16, QFont.Bold))
        barra.addWidget(titulo)
        barra.addStretch()

        self._selector_algoritmo = QComboBox()
        self._selector_algoritmo.addItem("Selecciona algoritmo...", None)
        self._selector_algoritmo.addItem("Amplitud (BFS)", "bfs")
        self._selector_algoritmo.addItem("Profundidad (DFS)", "dfs")
        self._selector_algoritmo.currentIndexChanged.connect(self._actualizar_estado_inicio)
        self._selector_algoritmo.setMinimumWidth(190)
        barra.addWidget(self._selector_algoritmo)

        self._btn_start = QPushButton("▶  Iniciar")
        self._btn_start.clicked.connect(self._ejecutar_busqueda)
        self._btn_start.setEnabled(False)
        self._btn_start.setMinimumWidth(100)
        barra.addWidget(self._btn_start)

        self._btn_reset = QPushButton("↺  Nuevo grafo")
        self._btn_reset.clicked.connect(self._preparar_partida)
        self._btn_reset.setMinimumWidth(110)
        barra.addWidget(self._btn_reset)

        root.addLayout(barra)

        # ── Splitter principal: izquierda (grafo global) | derecha (puzzle) ─
        splitter_h = QSplitter(Qt.Orientation.Horizontal)
        splitter_h.setChildrenCollapsible(False)

        # Panel izquierdo: grafo global
        izq = QWidget()
        izq_layout = QVBoxLayout(izq)
        izq_layout.setContentsMargins(0, 0, 0, 0)
        izq_layout.setSpacing(6)

        self._panel_grafo = PanelGrafo("Grafo Global — Búsqueda no informada")
        izq_layout.addWidget(self._panel_grafo)

        # Consola global debajo del grafo
        lbl_consola_g = QLabel("Registro global")
        lbl_consola_g.setFont(QFont("Ubuntu", 10, QFont.Bold))
        izq_layout.addWidget(lbl_consola_g)

        self._consola = QTextEdit()
        self._consola.setReadOnly(True)
        self._consola.setMaximumHeight(130)
        self._consola.setFont(QFont("Monospace", 8))
        self._consola.setPlaceholderText("Eventos de la búsqueda global...")
        izq_layout.addWidget(self._consola)

        splitter_h.addWidget(izq)

        # Panel derecho: subgrafo A* + estadísticas + consola local
        der = QWidget()
        der_layout = QVBoxLayout(der)
        der_layout.setContentsMargins(0, 0, 0, 0)
        der_layout.setSpacing(6)

        # Sub-panel del subgrafo A*
        self._panel_subgrafo = PanelSubgrafo()
        der_layout.addWidget(self._panel_subgrafo, stretch=3)

        # Estadísticas
        stats_frame = self._construir_stats()
        der_layout.addWidget(stats_frame)

        # Consola local A*
        lbl_consola_l = QLabel("Registro A* (subproblema)")
        lbl_consola_l.setFont(QFont("Ubuntu", 10, QFont.Bold))
        der_layout.addWidget(lbl_consola_l)

        self._consola_local = QTextEdit()
        self._consola_local.setReadOnly(True)
        self._consola_local.setMaximumHeight(120)
        self._consola_local.setFont(QFont("Monospace", 8))
        self._consola_local.setPlaceholderText("Eventos del subproblema A*...")
        der_layout.addWidget(self._consola_local)

        splitter_h.addWidget(der)
        splitter_h.setSizes([620, 400])

        root.addWidget(splitter_h, stretch=1)

    def _construir_stats(self) -> QFrame:
        """Cuadro de estadísticas con dos columnas: Global | Local."""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet(
            "QFrame { background:#F5F5F5; border:1px solid #E0E0E0;"
            " border-radius:6px; padding:4px; }"
        )

        layout = QHBoxLayout(frame)
        layout.setSpacing(16)

        # Columna Global
        col_g = QVBoxLayout()
        lbl_g = QLabel("Global Search")
        lbl_g.setFont(QFont("Ubuntu", 9, QFont.Bold))
        col_g.addWidget(lbl_g)

        self._lbl_exp_g = QLabel("Nodes Expanded: —")
        self._lbl_exp_g.setFont(QFont("Ubuntu", 8))
        col_g.addWidget(self._lbl_exp_g)

        self._lbl_prof_g = QLabel("Depth: —")
        self._lbl_prof_g.setFont(QFont("Ubuntu", 8))
        col_g.addWidget(self._lbl_prof_g)

        layout.addLayout(col_g)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color:#BDBDBD;")
        layout.addWidget(sep)

        # Columna Local
        col_l = QVBoxLayout()
        lbl_l = QLabel("Local Puzzle (A*)")
        lbl_l.setFont(QFont("Ubuntu", 9, QFont.Bold))
        col_l.addWidget(lbl_l)

        self._lbl_exp_l = QLabel("Nodes Expanded: —")
        self._lbl_exp_l.setFont(QFont("Ubuntu", 8))
        col_l.addWidget(self._lbl_exp_l)

        self._lbl_cost_l = QLabel("Total Cost: —")
        self._lbl_cost_l.setFont(QFont("Ubuntu", 8))
        col_l.addWidget(self._lbl_cost_l)

        self._lbl_resueltos = QLabel("Solved: 0 | Failed: 0")
        self._lbl_resueltos.setFont(QFont("Ubuntu", 8))
        col_l.addWidget(self._lbl_resueltos)

        layout.addLayout(col_l)
        layout.addStretch()

        return frame

    # -----------------------------------------------------------------------
    # Estilos
    # -----------------------------------------------------------------------

    def _aplicar_estilos(self):
        self.setStyleSheet("""
        QMainWindow { background-color: #FFFFFF; }
        QPushButton {
            background-color: #2196F3; color: white; border: none;
            padding: 7px 14px; border-radius: 4px; font-weight: bold;
            font-family: 'Ubuntu';
        }
        QPushButton:hover   { background-color: #1976D2; }
        QPushButton:pressed { background-color: #1565C0; }
        QPushButton:disabled { background-color: #BDBDBD; }
        QComboBox {
            background-color: #F5F5F5; color: #212121;
            border: 1px solid #E0E0E0; padding: 6px;
            border-radius: 4px; font-family: 'Ubuntu';
        }
        QComboBox:hover { border: 1px solid #2196F3; }
        QTextEdit {
            background-color: #FAFAFA; color: #212121;
            border: 1px solid #E0E0E0; border-radius: 4px;
            padding: 6px; font-family: 'Monospace';
        }
        QLabel  { color: #212121; font-family: 'Ubuntu'; }
        QSplitter::handle { background-color: #E0E0E0; width: 2px; }
        """)

    # -----------------------------------------------------------------------
    # Preparar partida
    # -----------------------------------------------------------------------

    def _preparar_partida(self):
        if self._timer_busqueda.isActive():
            self._timer_busqueda.stop()
            self._generador_busqueda = None

        self._consola.clear()
        self._consola_local.clear()
        self._ultimo_resultado    = None
        self._expandidos_global   = 0
        self._profundidad_global  = 0
        self._resueltos_local     = 0
        self._fallidos_local      = 0
        self._expandidos_local    = 0
        self._costo_local         = 0

        self._grafo, self._inicio, self._objetivo = generar_grafo_dag(n=11, densidad=0.3)
        self._bloqueados = generar_bloqueados(self._grafo, self._inicio, self._objetivo)
        self._panel_grafo.mostrar_vacio()
        self._panel_subgrafo.limpiar()
        self._actualizar_stats()

        self._log(f"Grafo generado | Inicio: {self._inicio} | "
                  f"Objetivo: {self._objetivo} | "
                  f"Bloqueados: {sorted(self._bloqueados)}")
        self._log("Selecciona un algoritmo y presiona Iniciar.")
        self._actualizar_estado_inicio()

    # -----------------------------------------------------------------------
    # Control de la búsqueda
    # -----------------------------------------------------------------------

    def _actualizar_estado_inicio(self):
        algoritmo = self._selector_algoritmo.currentData()
        self._btn_start.setEnabled(
            algoritmo is not None and not self._timer_busqueda.isActive()
        )

    def _ejecutar_busqueda(self):
        if self._timer_busqueda.isActive():
            return

        algoritmo = self._selector_algoritmo.currentData()
        if algoritmo not in {"bfs", "dfs"}:
            self._log("⚠️ Elige BFS o DFS antes de iniciar.")
            return

        self._consola.clear()
        self._consola_local.clear()
        self._panel_subgrafo.limpiar()
        self._panel_grafo.cargar_grafo(
            self._grafo, self._inicio, self._objetivo, self._bloqueados
        )

        if algoritmo == "bfs":
            self._generador_busqueda = bfs_pasos(
                self._grafo, self._inicio, self._objetivo, self._bloqueados
            )
        else:
            self._generador_busqueda = dfs_pasos(
                self._grafo, self._inicio, self._objetivo, self._bloqueados
            )

        self._nodo_actual         = None
        self._nodos_visitados     = set()
        self._ultimo_resultado    = None
        self._expandidos_global   = 0
        self._profundidad_global  = 0
        self._resueltos_local     = 0
        self._fallidos_local      = 0
        self._expandidos_local    = 0
        self._costo_local         = 0
        self._actualizar_stats()

        nombre = "AMPLITUD (BFS)" if algoritmo == "bfs" else "PROFUNDIDAD (DFS)"
        self._log(f"🔍 Iniciando búsqueda: {nombre}")
        self._btn_start.setEnabled(False)
        self._btn_reset.setEnabled(False)
        self._selector_algoritmo.setEnabled(False)
        self._timer_busqueda.start(600)

    def _avanzar_busqueda(self):
        if self._generador_busqueda is None:
            self._detener_busqueda()
            return

        try:
            paso = next(self._generador_busqueda)
        except StopIteration:
            self._detener_busqueda()
            return
        except Exception as e:
            self._log(f"⚠️ Error: {e}")
            self._detener_busqueda()
            return

        tipo = paso["tipo"]

        if tipo == "expandir":
            nodo = paso["nodo"]
            self._expandidos_global += 1
            self._profundidad_global = max(
                self._profundidad_global, paso["profundidad"]
            )
            self._marcar_nodo_actual(nodo)
            self._nodos_visitados.add(nodo)
            self._panel_grafo.actualizar_nodo(nodo, "actual")
            self._log(f"→ Expandiendo nodo {nodo}")
            self._actualizar_stats()

        elif tipo == "descubrir":
            vecino = paso["vecino"]
            self._panel_grafo.actualizar_nodo(vecino, "disponible")
            self._log(f"◆ Descubierto: {vecino}")

        elif tipo == "bloqueado":
            vecino = paso["vecino"]
            self._panel_grafo.actualizar_nodo(vecino, "bloqueado")
            self._log(f"🔒 Encontrado nodo bloqueado: {vecino}")
            self._log(f"   ↳ Iniciando A* para resolver el problema de Bucarest de {vecino}...")

        elif tipo == "subproblema_inicio":
            vecino          = paso["vecino"]
            resultado_local = paso["resultado_local"]
            # ── NUEVO: dibujar el subgrafo en el panel derecho ──
            self._panel_subgrafo.cargar_subgrafo(resultado_local, vecino)
            self._log_local(
                f"▶ Subproblema de {vecino}: "
                f"{paso['inicio_local']} → {paso['objetivo_local']}"
            )

        elif tipo == "subproblema_evento":
            self._log_local(f"  {paso['mensaje']}")

        elif tipo == "desbloqueado":
            vecino          = paso["vecino"]
            resultado_local = paso["resultado_local"]
            self._panel_grafo.actualizar_nodo(vecino, "disponible")
            self._resueltos_local += 1
            self._expandidos_local += resultado_local["nodos_expandidos"]
            self._costo_local      += resultado_local["costo_total"]
            self._log(f"🔓 Nodo {vecino} desbloqueado — "
                      f"costo={resultado_local['costo_total']} | "
                      f"expandidos={resultado_local['nodos_expandidos']}")
            self._log_local(f"✔ Puzzle resuelto → desbloqueando nodo global {vecino}")
            self._actualizar_stats()

        elif tipo == "subproblema_fallido":
            vecino          = paso["vecino"]
            resultado_local = paso["resultado_local"]
            self._fallidos_local += 1
            self._log(f"❌ No se pudo desbloquear: {vecino}")
            self._log_local(f"✘ Puzzle fallido ({vecino}) | "
                            f"expandidos={resultado_local['nodos_expandidos']}")
            self._actualizar_stats()

        elif tipo == "objetivo":
            camino = paso["camino"]
            self._log(f"🏁 ¡Objetivo {paso['nodo']} alcanzado!")
            self._panel_grafo.marcar_camino(camino)

        elif tipo == "fin":
            self._ultimo_resultado = paso
            if paso["exito"]:
                camino = paso["camino"] or []
                self._panel_grafo.marcar_camino(camino)
                self._log(f"✅ Camino: {' → '.join(camino)}")
            else:
                self._log("✗ No se encontró camino al objetivo.")

            self._log(f"📊 Nodos expandidos (global): {paso['nodos_expandidos']}")
            self._log(f"📏 Profundidad: {paso['profundidad']}")
            self._log(f"⏱️  Tiempo: {paso['tiempo']:.4f} s")
            self._log(f"🧩 Subproblemas resueltos: {self._resueltos_local} | "
                      f"fallidos: {self._fallidos_local}")
            self._actualizar_stats()
            self._detener_busqueda()

    # -----------------------------------------------------------------------
    # Helpers de UI
    # -----------------------------------------------------------------------

    def _marcar_nodo_actual(self, nodo):
        if self._nodo_actual and self._nodo_actual != nodo:
            prev = self._nodo_actual
            if prev == self._inicio:
                self._panel_grafo.actualizar_nodo(prev, "inicio")
            elif prev == self._objetivo:
                self._panel_grafo.actualizar_nodo(prev, "objetivo")
            elif prev in self._bloqueados:
                self._panel_grafo.actualizar_nodo(prev, "bloqueado")
            else:
                self._panel_grafo.actualizar_nodo(prev, "disponible")
        self._nodo_actual = nodo

    def _detener_busqueda(self):
        self._timer_busqueda.stop()
        self._generador_busqueda = None
        self._nodo_actual        = None
        self._selector_algoritmo.setEnabled(True)
        self._btn_reset.setEnabled(True)
        self._actualizar_estado_inicio()

    def _actualizar_stats(self):
        self._lbl_exp_g.setText(f"Nodes Expanded: {self._expandidos_global}")
        self._lbl_prof_g.setText(f"Depth: {self._profundidad_global}")
        self._lbl_exp_l.setText(f"Nodes Expanded: {self._expandidos_local}")
        self._lbl_cost_l.setText(f"Total Cost: {self._costo_local}")
        self._lbl_resueltos.setText(
            f"Solved: {self._resueltos_local} | Failed: {self._fallidos_local}"
        )

    def _log(self, mensaje: str):
        self._consola.append(f"> {mensaje}")

    def _log_local(self, mensaje: str):
        self._consola_local.append(f"> {mensaje}")

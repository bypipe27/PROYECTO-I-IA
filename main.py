import sys
import signal

from PyQt5.QtWidgets import QApplication

from interfaz.ventana_principal import VentanaPrincipal


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec_())

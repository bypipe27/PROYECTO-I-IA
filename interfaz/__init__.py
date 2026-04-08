"""Paquete de interfaz con importación diferida de widgets PyQt5."""

__all__ = ["PanelGrafo", "VentanaPrincipal"]


def __getattr__(name):
	if name == "PanelGrafo":
		from .panel_grafo import PanelGrafo

		return PanelGrafo
	if name == "VentanaPrincipal":
		from .ventana_principal import VentanaPrincipal

		return VentanaPrincipal
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

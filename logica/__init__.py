"""Paquete de lógica con exportación diferida de utilidades de grafos."""

__all__ = ["bfs", "generar_bloqueados", "generar_grafo_dag", "visualizar_grafo"]


def __getattr__(name):
	if name in __all__:
		from . import grafos

		return getattr(grafos, name)
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

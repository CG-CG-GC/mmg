from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from app.application.errors import GraphUnavailableError

if TYPE_CHECKING:
    from app.domain.grafo import Graph
    from app.persistence.repositories import (
        EntidadCreateData,
        EntidadRepository,
        EvidenciaCreateData,
        EvidenciaRepository,
        RelacionCreateData,
        RelacionRepository,
    )


class GraphApplicationService:
    """Coordina persistencia y la proyección del grafo en memoria.

    Los repositorios conservan sus contratos y administran sus propias transacciones.
    Después de cada escritura confirmada, el servicio reconstruye el grafo completo y
    solo publica la nueva instancia cuando la reconstrucción terminó correctamente.
    Si falla, invalida el estado en memoria para no exponer una proyección obsoleta.
    """

    def __init__(
        self,
        *,
        session_factory: Any,
        entidad_repository: EntidadRepository,
        relacion_repository: RelacionRepository,
        evidencia_repository: EvidenciaRepository,
        graph_loader: Callable[[Any], Graph] | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._entidades = entidad_repository
        self._relaciones = relacion_repository
        self._evidencias = evidencia_repository
        if graph_loader is None:
            from app.persistence.graph_loader import load_graph_from_database

            graph_loader = load_graph_from_database
        self._graph_loader = graph_loader
        self._graph: Graph | None = None
        self.reconstruir_grafo()

    @property
    def graph(self) -> Graph:
        """Devuelve el grafo vigente; falla explícitamente si quedó invalidado."""
        if self._graph is None:
            raise GraphUnavailableError(
                "El grafo no está disponible. Ejecute reconstruir_grafo() antes de consultarlo."
            )
        return self._graph

    def reconstruir_grafo(self) -> Graph:
        """Reconstruye una instancia completa y la publica de forma atómica."""
        try:
            candidate = self._graph_loader(self._session_factory)
        except Exception:
            # No conservar una proyección que ya podría no representar la BD.
            self._graph = None
            raise
        self._graph = candidate
        return candidate

    def crear_entidad(self, data: EntidadCreateData):
        self._require_graph()
        created = self._entidades.create(data)
        self._refresh_after_write()
        return created

    def eliminar_entidad(self, entity_id: int) -> bool:
        self._require_graph()
        deleted = self._entidades.delete_by_id(entity_id)
        if deleted:
            self._refresh_after_write()
        return deleted

    def crear_relacion(self, data: RelacionCreateData):
        self._require_graph()
        created = self._relaciones.create(data)
        self._refresh_after_write()
        return created

    def eliminar_relacion(self, relation_id: int) -> bool:
        self._require_graph()
        deleted = self._relaciones.delete_by_id(relation_id)
        if deleted:
            self._refresh_after_write()
        return deleted

    def crear_evidencia(self, data: EvidenciaCreateData):
        self._require_graph()
        created = self._evidencias.create(data)
        self._refresh_after_write()
        return created

    def _require_graph(self) -> None:
        if self._graph is None:
            raise GraphUnavailableError(
                "No se puede operar sin un grafo vigente; reconstruya desde persistencia."
            )

    def _refresh_after_write(self) -> None:
        try:
            candidate = self._graph_loader(self._session_factory)
        except Exception:
            # La escritura del repositorio ya confirmó su transacción. No podemos
            # revertirla sin cambiar sus contratos; invalidamos el grafo y fallamos.
            self._graph = None
            raise
        self._graph = candidate

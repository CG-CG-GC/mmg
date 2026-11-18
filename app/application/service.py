from __future__ import annotations

import threading
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from app.application.errors import GraphUnavailableError
from app.domain.errores import EntidadNoEncontradaError

# Serializa carga y publicación del grafo para todas las instancias del proceso.
# Sin esto, una reconstrucción leída antes de un commit puede publicarse después de
# otra más reciente y dejar el grafo atrasado. Solo cubre un proceso: ver HANDOFF.
_PUBLICACION_GRAFO = threading.RLock()

if TYPE_CHECKING:
    from app.domain.grafo import Graph
    from app.persistence.repositories import EntidadUpdateData, RelacionUpdateData
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
        with _PUBLICACION_GRAFO:
            return self._cargar_y_publicar()

    def crear_entidad(self, data: EntidadCreateData):
        self._require_graph()
        created = self._entidades.create(data)
        self._refresh_after_write()
        return created

    def actualizar_entidad(self, entity_id: int, data: EntidadUpdateData):
        self._require_graph()
        updated = self._entidades.update(entity_id, data)
        self._refresh_after_write()
        return updated

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

    def actualizar_relacion(self, relation_id: int, data: RelacionUpdateData):
        graph = self.graph
        for entity_id in (data.origen_id, data.destino_id):
            if not graph.existe_entidad(entity_id):
                raise EntidadNoEncontradaError(
                    f"No existe entidad referenciada con id {entity_id}."
                )
        updated = self._relaciones.update(relation_id, data)
        self._refresh_after_write()
        return updated

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

    def refrescar_tras_escritura(self) -> None:
        """Reconstruye el grafo tras una escritura confirmada fuera de los CRUD."""
        self._refresh_after_write()

    def _require_graph(self) -> None:
        if self._graph is None:
            raise GraphUnavailableError(
                "No se puede operar sin un grafo vigente; reconstruya desde persistencia."
            )

    def _refresh_after_write(self) -> None:
        # La escritura del repositorio ya confirmó su transacción. La carga y la
        # publicación van juntas bajo el cerrojo, así que el último snapshot publicado
        # es el último leído.
        with _PUBLICACION_GRAFO:
            self._cargar_y_publicar()

    def _cargar_y_publicar(self) -> Graph:
        try:
            candidate = self._graph_loader(self._session_factory)
        except Exception:
            # No conservar una proyección que ya podría no representar la BD.
            self._graph = None
            raise
        self._graph = candidate
        return candidate

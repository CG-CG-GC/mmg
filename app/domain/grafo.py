from collections import deque

from app.domain.entidad import Entidad
from app.domain.errores import (
    EntidadDuplicadaError,
    EntidadNoEncontradaError,
    ErrorValidacion,
    InvarianteGrafoError,
    RelacionDuplicadaError,
    RelacionNoEncontradaError,
)
from app.domain.relacion import Relacion
from app.domain.resultados_grafo import BFSResult, DFSResult, PathResult
from app.domain.tipos import EntityId, RelationId


class Graph:
    def __init__(self) -> None:
        self._entidades_por_id: dict[EntityId, Entidad] = {}
        self._adyacencia: dict[EntityId, list[Relacion]] = {}

    def agregar_entidad(self, entidad: Entidad) -> Entidad:
        if not isinstance(entidad, Entidad):
            raise ErrorValidacion("Se esperaba una instancia de Entidad.")
        if entidad.id in self._entidades_por_id:
            raise EntidadDuplicadaError(f"La entidad con id {entidad.id} ya existe.")
        self._entidades_por_id[entidad.id] = entidad
        self._adyacencia[entidad.id] = []
        return entidad

    def buscar_entidad(self, entidad_id: EntityId) -> Entidad | None:
        return self._entidades_por_id.get(entidad_id)

    def existe_entidad(self, entidad_id: EntityId) -> bool:
        return entidad_id in self._entidades_por_id

    def eliminar_entidad(self, entidad_id: EntityId) -> Entidad:
        if entidad_id not in self._entidades_por_id:
            raise EntidadNoEncontradaError(f"No existe entidad con id {entidad_id}.")

        entidad_eliminada = self._entidades_por_id.pop(entidad_id)
        self._adyacencia.pop(entidad_id, None)

        for origen_id, relaciones in self._adyacencia.items():
            self._adyacencia[origen_id] = [
                relacion
                for relacion in relaciones
                if relacion.destino_id != entidad_id and relacion.origen_id != entidad_id
            ]

        return entidad_eliminada

    def agregar_relacion(self, relacion: Relacion) -> Relacion:
        if not isinstance(relacion, Relacion):
            raise ErrorValidacion("Se esperaba una instancia de Relacion.")
        if not self.existe_entidad(relacion.origen_id):
            raise EntidadNoEncontradaError(f"No existe origen con id {relacion.origen_id}.")
        if not self.existe_entidad(relacion.destino_id):
            raise EntidadNoEncontradaError(f"No existe destino con id {relacion.destino_id}.")
        if self.existe_relacion(relacion.id):
            raise RelacionDuplicadaError(f"La relación con id {relacion.id} ya existe.")
        if self._es_relacion_duplicada(relacion):
            raise RelacionDuplicadaError(
                "Ya existe una relación con el mismo origen, destino y tipo."
            )

        self._adyacencia[relacion.origen_id].append(relacion)
        return relacion

    def buscar_relacion(self, relacion_id: RelationId) -> Relacion | None:
        for relaciones in self._adyacencia.values():
            for relacion in relaciones:
                if relacion.id == relacion_id:
                    return relacion
        return None

    def existe_relacion(self, relacion_id: RelationId) -> bool:
        return self.buscar_relacion(relacion_id) is not None

    def eliminar_relacion(self, relacion_id: RelationId) -> Relacion:
        for relaciones in self._adyacencia.values():
            for idx, relacion in enumerate(relaciones):
                if relacion.id == relacion_id:
                    return relaciones.pop(idx)
        raise RelacionNoEncontradaError(f"No existe relación con id {relacion_id}.")

    def obtener_vecinos(self, entidad_id: EntityId) -> list[Entidad]:
        if entidad_id not in self._entidades_por_id:
            raise EntidadNoEncontradaError(f"No existe entidad con id {entidad_id}.")

        vecinos: list[Entidad] = []
        vistos: set[EntityId] = set()
        for relacion in self._adyacencia[entidad_id]:
            if relacion.destino_id not in vistos:
                vistos.add(relacion.destino_id)
                vecinos.append(self._entidades_por_id[relacion.destino_id])
        return vecinos

    def bfs(self, id_inicial: EntityId) -> BFSResult:
        if id_inicial not in self._entidades_por_id:
            raise EntidadNoEncontradaError(f"No existe entidad inicial con id {id_inicial}.")

        visitados: set[EntityId] = {id_inicial}
        cola: deque[EntityId] = deque([id_inicial])
        orden_recorrido: list[EntityId] = []
        niveles: dict[EntityId, int] = {id_inicial: 0}
        predecesores: dict[EntityId, EntityId | None] = {id_inicial: None}

        while cola:
            actual = cola.popleft()
            orden_recorrido.append(actual)

            for relacion in self._adyacencia[actual]:
                vecino_id = relacion.destino_id
                if vecino_id in visitados:
                    continue
                visitados.add(vecino_id)
                predecesores[vecino_id] = actual
                niveles[vecino_id] = niveles[actual] + 1
                cola.append(vecino_id)

        return BFSResult(
            orden_recorrido=orden_recorrido,
            niveles=niveles,
            predecesores=predecesores,
        )

    def dfs(self, id_inicial: EntityId) -> DFSResult:
        if id_inicial not in self._entidades_por_id:
            raise EntidadNoEncontradaError(f"No existe entidad inicial con id {id_inicial}.")

        visitados: set[EntityId] = set()
        orden_recorrido: list[EntityId] = []

        def visitar(actual: EntityId) -> None:
            visitados.add(actual)
            orden_recorrido.append(actual)

            for relacion in self._adyacencia[actual]:
                vecino_id = relacion.destino_id
                if vecino_id in visitados:
                    continue
                visitar(vecino_id)

        visitar(id_inicial)
        return DFSResult(orden_recorrido=orden_recorrido)

    def buscar_camino(self, id_origen: EntityId, id_destino: EntityId) -> PathResult:
        if id_origen not in self._entidades_por_id:
            raise EntidadNoEncontradaError(f"No existe origen con id {id_origen}.")
        if id_destino not in self._entidades_por_id:
            raise EntidadNoEncontradaError(f"No existe destino con id {id_destino}.")
        if id_origen == id_destino:
            return PathResult(
                encontrado=True,
                entidades_camino=[id_origen],
                relaciones_camino=[],
            )

        bfs_result = self.bfs(id_origen)
        if id_destino not in bfs_result.predecesores:
            return PathResult(encontrado=False, entidades_camino=[], relaciones_camino=[])

        entidades_camino_reverso: list[EntityId] = []
        actual = id_destino
        while actual is not None:
            entidades_camino_reverso.append(actual)
            if actual == id_origen:
                break
            actual = bfs_result.predecesores.get(actual)

        if not entidades_camino_reverso or entidades_camino_reverso[-1] != id_origen:
            return PathResult(encontrado=False, entidades_camino=[], relaciones_camino=[])

        entidades_camino = list(reversed(entidades_camino_reverso))
        relaciones_camino: list[RelationId] = []

        for idx in range(len(entidades_camino) - 1):
            origen = entidades_camino[idx]
            destino = entidades_camino[idx + 1]
            relacion = self._buscar_relacion_entre(origen, destino)
            if relacion is None:
                raise InvarianteGrafoError(
                    f"No existe relación entre {origen} y {destino} durante reconstrucción."
                )
            relaciones_camino.append(relacion.id)

        return PathResult(
            encontrado=True,
            entidades_camino=entidades_camino,
            relaciones_camino=relaciones_camino,
        )

    def _es_relacion_duplicada(self, relacion: Relacion) -> bool:
        return any(
            actual.destino_id == relacion.destino_id and actual.tipo == relacion.tipo
            for actual in self._adyacencia[relacion.origen_id]
        )

    def _buscar_relacion_entre(self, origen_id: EntityId, destino_id: EntityId) -> Relacion | None:
        for relacion in self._adyacencia[origen_id]:
            if relacion.destino_id == destino_id:
                return relacion
        return None

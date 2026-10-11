from dataclasses import dataclass

from app.domain.tipos import EntityId, RelationId


@dataclass(slots=True)
class BFSResult:
    orden_recorrido: list[EntityId]
    niveles: dict[EntityId, int]
    predecesores: dict[EntityId, EntityId | None]


@dataclass(slots=True)
class DFSResult:
    orden_recorrido: list[EntityId]


@dataclass(slots=True)
class PathResult:
    encontrado: bool
    entidades_camino: list[EntityId]
    relaciones_camino: list[RelationId]

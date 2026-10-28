from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.schemas import (
    BFSRequest,
    DFSRequest,
    EntityCreateRequest,
    EntityResponse,
    EvidenceCreateRequest,
    EvidenceResponse,
    PathRequest,
    RelationCreateRequest,
    RelationResponse,
)
from app.persistence.repositories import (
    EntidadCreateData,
    EvidenciaCreateData,
    RelacionCreateData,
)

router = APIRouter(prefix="/api/v1")


def _repositories(request: Request):
    state = request.app.state
    return state.entidad_repository, state.relacion_repository


@router.get("/entidades", response_model=list[EntityResponse])
def listar_entidades(request: Request) -> list[EntityResponse]:
    entidad_repository, _ = _repositories(request)
    return entidad_repository.list_all()


@router.post("/entidades", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)
def crear_entidad(payload: EntityCreateRequest, request: Request) -> EntityResponse:
    service = request.app.state.graph_service
    created = service.crear_entidad(EntidadCreateData(**payload.model_dump()))
    return created


@router.get("/entidades/{entity_id}", response_model=EntityResponse)
def obtener_entidad(entity_id: int, request: Request) -> EntityResponse:
    entidad_repository, _ = _repositories(request)
    entity = entidad_repository.get_by_id(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"No existe entidad con id {entity_id}.")
    return entity


@router.delete("/entidades/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_entidad(entity_id: int, request: Request) -> Response:
    deleted = request.app.state.graph_service.eliminar_entidad(entity_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"No existe entidad con id {entity_id}.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/relaciones", response_model=list[RelationResponse])
def listar_relaciones(request: Request) -> list[RelationResponse]:
    _, relation_repository = _repositories(request)
    return relation_repository.list_all()


@router.post("/relaciones", response_model=RelationResponse, status_code=status.HTTP_201_CREATED)
def crear_relacion(payload: RelationCreateRequest, request: Request) -> RelationResponse:
    entity_repository, _ = _repositories(request)
    for entity_id in (payload.origen_id, payload.destino_id):
        if entity_repository.get_by_id(entity_id) is None:
            raise HTTPException(status_code=404, detail=f"No existe entidad con id {entity_id}.")
    created = request.app.state.graph_service.crear_relacion(
        RelacionCreateData(**payload.model_dump())
    )
    return created


@router.get("/relaciones/{relation_id}", response_model=RelationResponse)
def obtener_relacion(relation_id: int, request: Request) -> RelationResponse:
    _, relation_repository = _repositories(request)
    relation = relation_repository.get_by_id(relation_id)
    if relation is None:
        raise HTTPException(status_code=404, detail=f"No existe relación con id {relation_id}.")
    return relation


@router.delete("/relaciones/{relation_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_relacion(relation_id: int, request: Request) -> Response:
    deleted = request.app.state.graph_service.eliminar_relacion(relation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"No existe relación con id {relation_id}.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/relaciones/{relation_id}/evidencias",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_evidencia(
    relation_id: int, payload: EvidenceCreateRequest, request: Request
) -> EvidenceResponse:
    _, relation_repository = _repositories(request)
    if relation_repository.get_by_id(relation_id) is None:
        raise HTTPException(status_code=404, detail=f"No existe relación con id {relation_id}.")
    data = EvidenciaCreateData(relacion_id=relation_id, **payload.model_dump())
    return request.app.state.graph_service.crear_evidencia(data)


@router.get("/grafo")
def obtener_grafo(request: Request) -> dict[str, list[dict[str, object]]]:
    entity_repository, relation_repository = _repositories(request)
    entities = entity_repository.list_all()
    relations = relation_repository.list_all()
    nodes = [
        {
            "data": {
                "id": str(entity.id),
                "entity_id": entity.id,
                "label": entity.valor,
                "tipo": entity.tipo.value,
                "descripcion": entity.descripcion,
            }
        }
        for entity in entities
    ]
    edges = [
        {
            "data": {
                "id": str(relation.id),
                "relation_id": relation.id,
                "source": str(relation.origen_id),
                "target": str(relation.destino_id),
                "tipo": relation.tipo.value,
                "descripcion": relation.descripcion,
            }
        }
        for relation in relations
    ]
    return {"nodes": nodes, "edges": edges}


@router.post("/algoritmos/bfs")
def ejecutar_bfs(payload: BFSRequest, request: Request) -> dict[str, object]:
    result = request.app.state.graph_service.graph.bfs(payload.id_inicial)
    return {
        "orden_recorrido": result.orden_recorrido,
        "niveles": result.niveles,
        "predecesores": result.predecesores,
    }


@router.post("/algoritmos/dfs")
def ejecutar_dfs(payload: DFSRequest, request: Request) -> dict[str, object]:
    result = request.app.state.graph_service.graph.dfs(payload.id_inicial)
    return {"orden_recorrido": result.orden_recorrido}


@router.post("/algoritmos/camino")
def buscar_camino(payload: PathRequest, request: Request) -> dict[str, object]:
    result = request.app.state.graph_service.graph.buscar_camino(
        payload.id_origen, payload.id_destino
    )
    return {
        "encontrado": result.encontrado,
        "entidades_camino": result.entidades_camino,
        "relaciones_camino": result.relaciones_camino,
    }

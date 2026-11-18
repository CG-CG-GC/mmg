from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.tipos import TipoEntidad, TipoRelacion


class EntityCreateRequest(BaseModel):
    tipo: TipoEntidad
    valor: str = Field(min_length=1)
    # Se recibe explícitamente porque la política de normalización por tipo
    # todavía debe aprobarse; la API no la inventa.
    valor_normalizado: str = Field(min_length=1)
    descripcion: str | None = None
    metadata: dict[str, Any] | None = None


class EntityUpdateRequest(BaseModel):
    tipo: TipoEntidad
    valor: str = Field(min_length=1)
    valor_normalizado: str = Field(min_length=1)
    descripcion: str | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("valor", "valor_normalizado")
    @classmethod
    def reject_blank_values(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("El valor no puede estar vacío.")
        return value


class EntityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: TipoEntidad
    valor: str
    valor_normalizado: str
    descripcion: str | None = None
    metadata: dict[str, Any] | None = None


class RelationCreateRequest(BaseModel):
    origen_id: int = Field(gt=0)
    destino_id: int = Field(gt=0)
    tipo: TipoRelacion
    descripcion: str | None = None
    fecha: date | datetime | None = None


class RelationUpdateRequest(BaseModel):
    origen_id: int = Field(gt=0)
    destino_id: int = Field(gt=0)
    tipo: TipoRelacion
    descripcion: str | None = None
    fecha: date | datetime | None = None


class EvidenceCreateRequest(BaseModel):
    fuente: str = Field(min_length=1)
    descripcion: str | None = None
    fecha: date | datetime | None = None


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fuente: str
    descripcion: str | None = None
    fecha: date | datetime | None = None


class RelationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    origen_id: int
    destino_id: int
    tipo: TipoRelacion
    descripcion: str | None = None
    fecha: date | datetime | None = None
    evidencias: list[EvidenceResponse] = Field(default_factory=list)


class BFSRequest(BaseModel):
    id_inicial: int = Field(gt=0)


class DFSRequest(BaseModel):
    id_inicial: int = Field(gt=0)


class PathRequest(BaseModel):
    id_origen: int = Field(gt=0)
    id_destino: int = Field(gt=0)

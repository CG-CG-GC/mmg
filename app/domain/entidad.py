from dataclasses import dataclass
from typing import Any

from app.domain.errores import EntidadInvalidaError
from app.domain.tipos import EntityId, TipoEntidad


@dataclass(slots=True)
class Entidad:
    id: EntityId
    tipo: TipoEntidad
    valor: str
    descripcion: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.id, int) or isinstance(self.id, bool) or self.id <= 0:
            raise EntidadInvalidaError("El id de entidad debe ser un int positivo.")
        if not isinstance(self.tipo, TipoEntidad):
            raise EntidadInvalidaError("El tipo de entidad es inválido.")
        if not isinstance(self.valor, str) or not self.valor.strip():
            raise EntidadInvalidaError("El valor de entidad es obligatorio y no puede estar vacío.")
        if self.descripcion is not None and not isinstance(self.descripcion, str):
            raise EntidadInvalidaError("La descripción debe ser str o None.")
        if self.metadata is not None and not isinstance(self.metadata, dict):
            raise EntidadInvalidaError("La metadata debe ser dict o None.")

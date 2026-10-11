from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.errores import RelacionInvalidaError
from app.domain.evidencia import Evidencia
from app.domain.tipos import EntityId, RelationId, TipoRelacion


@dataclass(slots=True)
class Relacion:
    id: RelationId
    origen_id: EntityId
    destino_id: EntityId
    tipo: TipoRelacion
    descripcion: str | None = None
    fecha: date | datetime | None = None
    evidencias: list[Evidencia] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.id, int) or isinstance(self.id, bool) or self.id <= 0:
            raise RelacionInvalidaError("El id de relación debe ser un int positivo.")
        if not isinstance(self.origen_id, int) or isinstance(self.origen_id, bool) or self.origen_id <= 0:
            raise RelacionInvalidaError("El origen_id debe ser un int positivo.")
        if not isinstance(self.destino_id, int) or isinstance(self.destino_id, bool) or self.destino_id <= 0:
            raise RelacionInvalidaError("El destino_id debe ser un int positivo.")
        if not isinstance(self.tipo, TipoRelacion):
            raise RelacionInvalidaError("El tipo de relación es inválido.")
        if self.descripcion is not None and not isinstance(self.descripcion, str):
            raise RelacionInvalidaError("La descripción de relación debe ser str o None.")
        if self.fecha is not None and not isinstance(self.fecha, (date, datetime)):
            raise RelacionInvalidaError("La fecha de relación debe ser date/datetime o None.")
        if not isinstance(self.evidencias, list):
            raise RelacionInvalidaError("Las evidencias deben ser una lista.")
        for evidencia in self.evidencias:
            if not isinstance(evidencia, Evidencia):
                raise RelacionInvalidaError("Cada evidencia debe ser una instancia de Evidencia.")

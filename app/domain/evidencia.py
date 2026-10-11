from dataclasses import dataclass
from datetime import date, datetime

from app.domain.errores import EvidenciaInvalidaError
from app.domain.tipos import EvidenceId


@dataclass(slots=True)
class Evidencia:
    id: EvidenceId
    fuente: str
    descripcion: str | None = None
    fecha: date | datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.id, int) or isinstance(self.id, bool) or self.id <= 0:
            raise EvidenciaInvalidaError("El id de evidencia debe ser un int positivo.")
        if not isinstance(self.fuente, str) or not self.fuente.strip():
            raise EvidenciaInvalidaError("La fuente de evidencia es obligatoria.")
        if self.descripcion is not None and not isinstance(self.descripcion, str):
            raise EvidenciaInvalidaError("La descripción de evidencia debe ser str o None.")
        if self.fecha is not None and not isinstance(self.fecha, (date, datetime)):
            raise EvidenciaInvalidaError("La fecha de evidencia debe ser date/datetime o None.")

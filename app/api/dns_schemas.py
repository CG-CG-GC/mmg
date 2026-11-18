from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.application.dns_lookup import (
    EstadoConsultaTipo,
    RegistroDns,
    ResultadoConsultaDns,
)
from app.application.incorporacion_dns import (
    MAX_REGISTROS_INCORPORACION,
    IncorporacionDnsResultado,
    RegistroSolicitadoDns,
    SolicitudIncorporacionDns,
)
from app.persistence.incorporacion_dns import ObjetoIncorporado


class DnsQueryRequest(BaseModel):
    dominio: str = Field(min_length=1, max_length=512)
    # Si se omite, se consultan A, AAAA, CNAME, MX y NS.
    tipos: list[str] | None = Field(default=None, min_length=1, max_length=5)


class DnsRecordResponse(BaseModel):
    tipo: str
    valor: str
    estado: str
    fuente: str
    consultado_en: datetime
    prioridad: int | None = None

    @classmethod
    def desde_servicio(cls, registro: RegistroDns) -> DnsRecordResponse:
        return cls(
            tipo=registro.tipo,
            valor=registro.valor,
            estado=registro.estado,
            fuente=registro.fuente,
            consultado_en=registro.consultado_en,
            prioridad=registro.prioridad,
        )


class DnsTypeStatusResponse(BaseModel):
    tipo: str
    estado: str
    descartados: int

    @classmethod
    def desde_servicio(cls, estado: EstadoConsultaTipo) -> DnsTypeStatusResponse:
        return cls(tipo=estado.tipo, estado=estado.estado, descartados=estado.descartados)


class DnsQueryResponse(BaseModel):
    dominio: str
    fuente: str
    consultado_en: datetime
    registros: list[DnsRecordResponse]
    estados: list[DnsTypeStatusResponse]

    @classmethod
    def desde_servicio(cls, resultado: ResultadoConsultaDns) -> DnsQueryResponse:
        return cls(
            dominio=resultado.dominio,
            fuente=resultado.fuente,
            consultado_en=resultado.consultado_en,
            registros=[DnsRecordResponse.desde_servicio(r) for r in resultado.registros],
            estados=[DnsTypeStatusResponse.desde_servicio(e) for e in resultado.estados],
        )


class RegistroIncorporacionRequest(BaseModel):
    # Los límites semánticos (tipo, IP, fuente tras recortar espacios) los valida la aplicación.
    tipo: str = Field(max_length=8)
    valor: str = Field(min_length=1, max_length=64)
    fuente: str = Field(min_length=1, max_length=256)
    consultado_en: datetime


class IncorporacionDnsRequest(BaseModel):
    dominio: str = Field(min_length=1, max_length=512)
    registros: list[RegistroIncorporacionRequest] = Field(
        min_length=1, max_length=MAX_REGISTROS_INCORPORACION
    )

    def a_solicitud(self) -> SolicitudIncorporacionDns:
        return SolicitudIncorporacionDns(
            dominio=self.dominio,
            registros=tuple(
                RegistroSolicitadoDns(
                    tipo=registro.tipo,
                    valor=registro.valor,
                    fuente=registro.fuente,
                    consultado_en=registro.consultado_en,
                )
                for registro in self.registros
            ),
        )


class ObjetoIncorporadoResponse(BaseModel):
    id: int
    estado: Literal["creada", "reutilizada"]

    @classmethod
    def desde_persistencia(cls, objeto: ObjetoIncorporado) -> ObjetoIncorporadoResponse:
        return cls(id=objeto.id, estado=objeto.estado)


class ProcedenciaResponse(BaseModel):
    # Dato declarado por el cliente; el servidor no lo verifica.
    declarada_por: Literal["cliente"] = "cliente"
    fuente: str
    consultado_en: datetime


class RegistroIncorporadoResponse(BaseModel):
    tipo: str
    valor: str
    entidad: ObjetoIncorporadoResponse
    relacion: ObjetoIncorporadoResponse
    evidencia: ObjetoIncorporadoResponse
    procedencia: ProcedenciaResponse


class IncorporacionDnsResponse(BaseModel):
    dominio: ObjetoIncorporadoResponse
    resultados: list[RegistroIncorporadoResponse]

    @classmethod
    def desde_servicio(cls, resultado: IncorporacionDnsResultado) -> IncorporacionDnsResponse:
        return cls(
            dominio=ObjetoIncorporadoResponse.desde_persistencia(resultado.dominio),
            resultados=[
                RegistroIncorporadoResponse(
                    tipo=registro.tipo,
                    valor=registro.valor,
                    entidad=ObjetoIncorporadoResponse.desde_persistencia(registro.entidad),
                    relacion=ObjetoIncorporadoResponse.desde_persistencia(registro.relacion),
                    evidencia=ObjetoIncorporadoResponse.desde_persistencia(registro.evidencia),
                    procedencia=ProcedenciaResponse(
                        fuente=registro.fuente, consultado_en=registro.consultado_en
                    ),
                )
                for registro in resultado.registros
            ],
        )

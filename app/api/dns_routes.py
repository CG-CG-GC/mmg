from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.dns_schemas import (
    DnsQueryRequest,
    DnsQueryResponse,
    IncorporacionDnsRequest,
    IncorporacionDnsResponse,
)
from app.application.dns_lookup import TIPOS_REGISTRO_INICIALES

router = APIRouter(prefix="/api/v1/osint", tags=["osint"])


@router.post("/dns", response_model=DnsQueryResponse)
def consultar_dns(payload: DnsQueryRequest, request: Request) -> DnsQueryResponse:
    """Consulta registros DNS publicos. No escribe en la base de datos ni en el grafo."""
    tipos = payload.tipos if payload.tipos is not None else TIPOS_REGISTRO_INICIALES
    resultado = request.app.state.dns_service.consultar(payload.dominio, tipos)
    return DnsQueryResponse.desde_servicio(resultado)


@router.post("/dns/incorporaciones", response_model=IncorporacionDnsResponse)
def incorporar_dns(payload: IncorporacionDnsRequest, request: Request) -> IncorporacionDnsResponse:
    """Guarda los registros A y AAAA elegidos. No consulta DNS de nuevo."""
    resultado = request.app.state.incorporacion_dns_service.incorporar(payload.a_solicitud())
    return IncorporacionDnsResponse.desde_servicio(resultado)

from datetime import UTC, datetime

import pytest

from app.application.dns_lookup import (
    DnsLookupService,
    DominioInvalidoError,
    TipoRegistroInvalidoError,
    normalizar_dominio,
)
from app.integrations.dns_google import (
    GoogleDohProvider,
    ProveedorDnsHttpError,
    ProveedorDnsRedError,
    ProveedorDnsRespuestaError,
    ProveedorDnsTimeoutError,
    RespuestaCrudaDns,
)

AHORA = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)


class ProveedorFalso:
    fuente = "falso"

    def __init__(self, respuestas):
        self.respuestas = respuestas
        self.llamadas = []

    def consultar(self, dominio, tipo):
        self.llamadas.append((dominio, tipo))
        valor = self.respuestas.get(tipo, RespuestaCrudaDns(0, ()))
        if isinstance(valor, Exception):
            raise valor
        return valor


def servicio(respuestas):
    proveedor = ProveedorFalso(respuestas)
    return DnsLookupService(proveedor, reloj=lambda: AHORA), proveedor


def estados(resultado):
    return {e.tipo: e for e in resultado.estados}


def test_consulta_exitosa_por_tipo_con_metadatos():
    svc, _ = servicio(
        {
            "A": RespuestaCrudaDns(0, ((1, "93.184.216.34"),)),
            "AAAA": RespuestaCrudaDns(0, ((28, "2606:2800:220:1:248:1893:25c8:1946"),)),
            "MX": RespuestaCrudaDns(0, ((15, "10 Mail.Example.com."),)),
            "NS": RespuestaCrudaDns(0, ((2, "a.iana-servers.net."),)),
            "CNAME": RespuestaCrudaDns(0, ((5, "alias.example.net."),)),
        }
    )
    r = svc.consultar("Example.COM")
    assert r.dominio == "example.com"
    assert r.fuente == "falso"
    assert r.consultado_en == AHORA
    por_tipo = {x.tipo: x for x in r.registros}
    assert set(por_tipo) == {"A", "AAAA", "CNAME", "MX", "NS"}
    assert por_tipo["MX"].valor == "mail.example.com"
    assert por_tipo["MX"].prioridad == 10
    assert por_tipo["A"].estado == "encontrado"
    assert por_tipo["A"].fuente == "falso"
    assert por_tipo["A"].consultado_en == AHORA
    assert all(e.estado == "ok" for e in r.estados)


def test_respuesta_vacia_y_nxdomain_no_generan_registros():
    svc, _ = servicio({"A": RespuestaCrudaDns(3, ()), "NS": RespuestaCrudaDns(0, ())})
    r = svc.consultar("example.com", ["A", "NS"])
    assert r.registros == ()
    assert estados(r)["A"].estado == "dominio_inexistente"
    assert estados(r)["NS"].estado == "sin_registros"


def test_estado_dns_de_error_se_distingue():
    svc, _ = servicio({"A": RespuestaCrudaDns(2, ())})
    assert estados(svc.consultar("example.com", ["A"]))["A"].estado == "error_dns"


@pytest.mark.parametrize(
    ("error", "esperado"),
    [
        (ProveedorDnsTimeoutError(), "error_timeout"),
        (ProveedorDnsRedError(), "error_red"),
        (ProveedorDnsHttpError(), "error_http"),
        (ProveedorDnsRespuestaError(), "error_respuesta"),
    ],
)
def test_errores_del_proveedor_son_parciales_y_no_generan_registros(error, esperado):
    svc, _ = servicio({"A": error, "NS": RespuestaCrudaDns(0, ((2, "ns1.example.com."),))})
    r = svc.consultar("example.com", ["A", "NS"])
    assert estados(r)["A"].estado == esperado
    assert [x.valor for x in r.registros] == ["ns1.example.com"]


def test_duplicados_se_eliminan_y_cname_intermedio_se_ignora():
    svc, _ = servicio(
        {
            "A": RespuestaCrudaDns(
                0, ((5, "www.example.net."), (1, "1.2.3.4"), (1, "1.2.3.4"), (1, "1.2.3.5"))
            ),
            "MX": RespuestaCrudaDns(0, ((15, "10 m.example.com."), (15, "20 m.example.com."),
                                        (15, "10 M.example.com"))),
        }
    )
    r = svc.consultar("example.com", ["A", "MX"])
    assert [x.valor for x in r.registros if x.tipo == "A"] == ["1.2.3.4", "1.2.3.5"]
    assert [x.prioridad for x in r.registros if x.tipo == "MX"] == [10, 20]


def test_valores_invalidos_se_descartan_y_se_cuentan():
    svc, _ = servicio(
        {
            "A": RespuestaCrudaDns(0, ((1, "999.1.1.1"), (1, "<script>"), (1, "8.8.8.8"))),
            "MX": RespuestaCrudaDns(0, ((15, "0 ."), (15, "x mail.example.com."), (15, "5"))),
            "NS": RespuestaCrudaDns(0, ((2, "bad name.example.com."),)),
        }
    )
    r = svc.consultar("example.com", ["A", "MX", "NS"])
    assert [x.valor for x in r.registros] == ["8.8.8.8"]
    assert estados(r)["A"].descartados == 2
    assert estados(r)["MX"].estado == "sin_registros"
    assert estados(r)["MX"].descartados == 3
    assert estados(r)["NS"].descartados == 1


@pytest.mark.parametrize(
    "entrada",
    ["", "   ", "localhost", "http://example.com", "example.com/path", "user@example.com",
     "exa mple.com", "1.2.3.4", "::1", "example.com:80", "-a.example.com", "a..com",
     "a" * 64 + ".com", ("a" * 60 + ".") * 5 + "com", "example.123", None, 5],
)
def test_dominio_invalido_se_rechaza_sin_consultar(entrada):
    svc, proveedor = servicio({})
    with pytest.raises(DominioInvalidoError):
        svc.consultar(entrada)
    assert proveedor.llamadas == []


def test_dominio_se_normaliza_idna_y_punto_final():
    assert normalizar_dominio(" Bücher.example. ") == "xn--bcher-kva.example"


def test_tipo_invalido_o_vacio_se_rechaza():
    svc, _ = servicio({})
    for tipos in (["TXT"], [], "A", [1]):
        with pytest.raises(TipoRegistroInvalidoError):
            svc.consultar("example.com", tipos)


def test_tipos_repetidos_consultan_una_vez():
    svc, proveedor = servicio({})
    svc.consultar("example.com", ["a", "A"])
    assert proveedor.llamadas == [("example.com", "A")]


# Adaptador: transporte falso, sin red.
def proveedor_http(estado, cuerpo):
    capturado = {}

    def transporte(url, timeout):
        capturado["url"] = url
        capturado["timeout"] = timeout
        return estado, cuerpo

    return GoogleDohProvider(timeout=2, transporte=transporte), capturado


def test_adaptador_parsea_respuesta_y_ignora_items_malformados():
    cuerpo = b'{"Status":0,"Answer":[{"type":1,"data":"1.2.3.4"},{"type":"x"},5,{"type":1}]}'
    prov, capturado = proveedor_http(200, cuerpo)
    r = prov.consultar("example.com", "A")
    assert r == RespuestaCrudaDns(0, ((1, "1.2.3.4"),))
    assert capturado["url"] == "https://dns.google/resolve?name=example.com&type=A"
    assert capturado["timeout"] == 2


def test_adaptador_sin_answer_es_respuesta_vacia():
    prov, _ = proveedor_http(200, b'{"Status":3}')
    assert prov.consultar("example.com", "A") == RespuestaCrudaDns(3, ())


@pytest.mark.parametrize(
    ("estado", "cuerpo", "error"),
    [
        (503, b"", ProveedorDnsHttpError),
        (200, b"no es json", ProveedorDnsRespuestaError),
        (200, b"[]", ProveedorDnsRespuestaError),
        (200, b'{"Answer":[]}', ProveedorDnsRespuestaError),
        (200, b'{"Status":0,"Answer":"x"}', ProveedorDnsRespuestaError),
        (200, b"\xff\xfe", ProveedorDnsRespuestaError),
        pytest.param(200, b"x" * (64 * 1024 + 1), ProveedorDnsRespuestaError, id="grande"),
    ],
)
def test_adaptador_clasifica_errores(estado, cuerpo, error):
    prov, _ = proveedor_http(estado, cuerpo)
    with pytest.raises(error):
        prov.consultar("example.com", "A")


def test_adaptador_valida_timeout_y_tipo():
    with pytest.raises(ValueError):
        GoogleDohProvider(timeout=0)
    prov, _ = proveedor_http(200, b'{"Status":0}')
    with pytest.raises(ValueError):
        prov.consultar("example.com", "TXT")


@pytest.mark.parametrize(
    "entrada",
    ["straße.de", "ｅxample.com", "example。com", "ﬁsh.com", "ς.gr"],
)
def test_transformacion_idna_no_equivalente_se_rechaza_sin_consultar(entrada):
    svc, proveedor = servicio({})
    with pytest.raises(DominioInvalidoError):
        svc.consultar(entrada)
    assert proveedor.llamadas == []


@pytest.mark.parametrize(
    "entrada",
    ["\u0130stanbul.tr", "xn--bogus.de", "xn--invalid-zz.de"],
)
def test_i_con_punto_y_a_labels_invalidas_se_rechazan_antes_de_consultar(entrada):
    svc, proveedor = servicio({})

    with pytest.raises(DominioInvalidoError):
        svc.consultar(entrada)

    assert proveedor.llamadas == []


def test_a_label_se_consulta_tal_cual_y_strasse_es_otro_nombre():
    svc, proveedor = servicio({"A": RespuestaCrudaDns(0, ())})

    svc.consultar("xn--strae-oqa.de", ["A"])
    svc.consultar("strasse.de", ["A"])

    assert [dominio for dominio, _ in proveedor.llamadas] == ["xn--strae-oqa.de", "strasse.de"]

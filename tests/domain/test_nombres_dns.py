import pytest

from app.domain.nombres_dns import NombreDnsNoEquivalenteError, convertir_dominio

# Todos los caracteres no ASCII van como escapes para que el archivo sea estable.
STRASSE_SHARP_S = "stra\xdfe.de"
MUNCHEN = "m\xfcnchen.de"
MUNCHEN_NFD = "mu\u0308nchen.de"  # u + di\xe9resis combinante, forma descompuesta
A_LABEL_STRASSE = "xn--strae-oqa.de"
A_LABEL_MUNCHEN = "xn--mnchen-3ya.de"


@pytest.mark.parametrize(
    "entrada",
    [
        STRASSE_SHARP_S,
        "\uff45\uff58\uff41\uff4d\uff50\uff4c\uff45.com",  # example en ancho completo
        "example\u3002com",  # separador ideogr\xe1fico
        "\ufb01sh.com",  # ligadura fi
        "ab\xadc.com",  # guion blando
        "\u03c2.gr",  # sigma final, IDNA 2003 la une a sigma
        "\u0130stanbul.tr",  # I con punto: cambia de longitud al pasar a min\xfasculas
    ],
)
def test_transformaciones_no_equivalentes_se_rechazan(entrada):
    with pytest.raises(NombreDnsNoEquivalenteError):
        convertir_dominio(entrada)


def test_sharp_s_rechazada_con_orientacion_al_usuario():
    with pytest.raises(NombreDnsNoEquivalenteError, match="xn--"):
        convertir_dominio(STRASSE_SHARP_S)


def test_strasse_ascii_se_conserva_como_otro_nombre():
    assert convertir_dominio("strasse.de") == "strasse.de"


def test_a_label_valida_se_conserva_sin_reinterpretar():
    assert convertir_dominio(A_LABEL_STRASSE) == A_LABEL_STRASSE
    assert convertir_dominio(A_LABEL_STRASSE) != "strasse.de"


@pytest.mark.parametrize("entrada", [MUNCHEN, MUNCHEN_NFD, "M\xdcNCHEN.de"])
def test_munchen_se_canonicaliza_en_forma_a_label(entrada):
    assert convertir_dominio(entrada.lower()) == A_LABEL_MUNCHEN


def test_ascii_sin_cambios_y_etiquetas_de_varios_niveles():
    assert convertir_dominio("www.example.com") == "www.example.com"
    assert convertir_dominio("b\xfccher.example") == "xn--bcher-kva.example"


def test_sigma_minuscula_se_acepta():
    assert convertir_dominio("\u03c3.gr") == "xn--4xa.gr"


@pytest.mark.parametrize(
    "entrada",
    [
        "\u0130stanbul.tr",  # I con punto
        "I\u0307stanbul.tr",  # forma descompuesta de I con punto
        "\u1e9e.de",  # sharp s mayuscula, se convierte en ss al bajar
        "\uff33TRA\xdfE.de",  # ancho completo con sharp s
        "\u0130.tr",
    ],
)
def test_i_con_punto_y_sharp_s_mayuscula_se_rechazan_antes_de_minusculas(entrada):
    with pytest.raises(NombreDnsNoEquivalenteError):
        convertir_dominio(entrada)


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("M\xdcNCHEN.de", "xn--mnchen-3ya.de"),
        ("XN--MNCHEN-3YA.DE", "xn--mnchen-3ya.de"),
        ("  Example.COM.  ", "example.com"),
        ("M\xfcnchen.de.", "xn--mnchen-3ya.de"),
        ("sub.M\xdcNCHEN.de", "sub.xn--mnchen-3ya.de"),
    ],
)
def test_espacios_punto_final_y_mayusculas_se_tratan_con_seguridad(entrada, esperado):
    assert convertir_dominio(entrada) == esperado


def _a_label_con_contenido(texto):
    return "xn--" + texto.encode("punycode").decode("ascii") + ".example"


@pytest.mark.parametrize(
    "etiqueta",
    [
        "xn--",  # carga vacia
        "xn--abc-",  # guion final
        "xn--bogus",  # decodifica a caracteres de control o sin forma canonica
        "xn--invalid-zz",  # carga Punycode mal formada
        "xn--a",  # decodifica a un byte de control
        "xn--mnchen-3ya-",  # guion final tras una carga valida
        "xn--mnchen_3ya",  # caracter fuera del alfabeto de Punycode
        "xn--" + "a" * 60,  # supera 63 caracteres
    ],
)
def test_a_label_malformada_se_rechaza(etiqueta):
    with pytest.raises(NombreDnsNoEquivalenteError):
        convertir_dominio(etiqueta + ".example")


@pytest.mark.parametrize(
    "contenido",
    [
        "\xadx",  # guion blando: formato (Cf)
        "x\u2028y",  # separador de linea (Zl)
        "\u0301x",  # marca combinante inicial
        "x\ufb01",  # ligadura, no es NFKC
        "\uff45x",  # ancho completo, no es NFKC
        "\xe9 y",  # espacio dentro de la etiqueta
        "x\xe9\ue000",  # uso privado (Co)
        "\xdcnchen",  # mayuscula en el contenido decodificado
    ],
)
def test_a_label_con_contenido_decodificado_prohibido_se_rechaza(contenido):
    with pytest.raises(NombreDnsNoEquivalenteError):
        convertir_dominio(_a_label_con_contenido(contenido))


def test_a_label_valida_del_alcance_se_acepta_y_no_se_reinterpreta():
    assert convertir_dominio("xn--mnchen-3ya.de") == "xn--mnchen-3ya.de"
    assert convertir_dominio("xn--strae-oqa.de") == "xn--strae-oqa.de"
    assert convertir_dominio(_a_label_con_contenido("\u03c3")) == _a_label_con_contenido("\u03c3")


@pytest.mark.parametrize("entrada", ["", "   ", ".", "a..b", "example\u3002com"])
def test_nombres_vacios_o_con_separadores_no_validos_se_rechazan(entrada):
    with pytest.raises(NombreDnsNoEquivalenteError):
        convertir_dominio(entrada)

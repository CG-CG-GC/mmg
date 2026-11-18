"""Política única de nombres DNS: forma canónica y validación de IDNA.

Es la regla que usan la consulta DNS, la incorporación y la persistencia. Decide sobre
el texto original, antes de cualquier conversión a minúsculas, porque `lower()` puede
ocultar un cambio de significado (por ejemplo `İ` pasa a `i` más punto combinante).

Límites: no implementa IDNA 2008. Las etiquetas Unicode se aceptan solo si IDNA 2003
no las cambiaría. Las A-label `xn--` se validan con criterios conservadores y se
conservan tal cual. Ver P-06.
"""

from __future__ import annotations

import re
import unicodedata
from encodings import idna as codec_idna

SEPARADORES_NO_ASCII = ("。", "．", "｡")
PREFIJO_A_LABEL = "xn--"
MAX_LONGITUD_ETIQUETA = 63
_CONTENIDO_A_LABEL = re.compile(r"^[a-z0-9-]+$")
_ASCII_PERMITIDO_EN_DECODIFICADO = re.compile(r"^[a-z0-9-]$")


class NombreDnsNoEquivalenteError(ValueError):
    """El nombre no puede convertirse ni validarse sin cambiar su significado DNS."""


def convertir_dominio(entrada: str) -> str:
    """Devuelve la forma canónica ASCII del nombre, en minúsculas.

    Acepta el texto tal como lo escribió el usuario: recorta espacios de borde, quita
    un único punto final y valida cada etiqueta. Las etiquetas ASCII se devuelven en
    minúsculas; las A-label `xn--` se validan y se conservan.
    """
    if not isinstance(entrada, str):
        raise NombreDnsNoEquivalenteError("el nombre debe ser texto")
    texto = entrada.strip()
    if texto.endswith("."):
        texto = texto[:-1]
    if not texto:
        raise NombreDnsNoEquivalenteError("el nombre está vacío")
    if any(separador in texto for separador in SEPARADORES_NO_ASCII):
        raise NombreDnsNoEquivalenteError(
            "usa un separador que no es un punto ASCII; escriba los puntos del nombre"
        )
    etiquetas = texto.split(".")
    if not all(etiquetas):
        raise NombreDnsNoEquivalenteError("el nombre tiene una etiqueta vacía")
    return ".".join(_convertir_etiqueta(etiqueta) for etiqueta in etiquetas)


def _convertir_etiqueta(etiqueta: str) -> str:
    if etiqueta.isascii():
        minusculas = etiqueta.lower()
        if minusculas.startswith(PREFIJO_A_LABEL):
            validar_a_label(minusculas)
        return minusculas
    forma = unicodedata.normalize("NFC", etiqueta)
    minusculas = forma.lower()
    if len(minusculas) != len(forma):
        raise NombreDnsNoEquivalenteError(
            f"la etiqueta {etiqueta!r} cambia de longitud al pasar a minúsculas"
        )
    try:
        if codec_idna.nameprep(minusculas) != minusculas:
            raise NombreDnsNoEquivalenteError(_motivo_de_transformacion(etiqueta))
        ascii_ = PREFIJO_A_LABEL + minusculas.encode("punycode").decode("ascii")
    except UnicodeError as exc:
        raise NombreDnsNoEquivalenteError(
            f"la etiqueta {etiqueta!r} no puede codificarse como nombre IDNA"
        ) from exc
    validar_a_label(ascii_)
    return ascii_


def validar_a_label(etiqueta: str) -> None:
    """Valida una A-label `xn--` ya en minúsculas. Lanza NombreDnsNoEquivalenteError.

    Criterios: carga Punycode válida y de forma canónica; contenido decodificado con al
    menos un carácter no ASCII, en minúsculas, en NFC y NFKC, sin caracteres de control,
    formato, espacio ni separadores; sin marca combinante inicial. Esto no implementa
    IDNA 2008: una etiqueta que pase estas reglas puede seguir siendo inválida para él.
    """

    def no_valida(motivo: str) -> NombreDnsNoEquivalenteError:
        return NombreDnsNoEquivalenteError(f"la etiqueta {etiqueta!r} no es una A-label válida: {motivo}")

    if len(etiqueta) > MAX_LONGITUD_ETIQUETA:
        raise no_valida("supera 63 caracteres")
    carga = etiqueta[len(PREFIJO_A_LABEL):]
    if not _CONTENIDO_A_LABEL.match(carga) or carga.endswith("-"):
        raise no_valida("el contenido después de xn-- no es Punycode")
    try:
        decodificada = carga.encode("ascii").decode("punycode")
    except UnicodeError as exc:
        raise no_valida("la carga Punycode no se puede decodificar") from exc
    if decodificada.isascii():
        raise no_valida("no codifica ningún carácter no ASCII")
    if (
        decodificada != unicodedata.normalize("NFC", decodificada)
        or decodificada != decodificada.lower()
        or unicodedata.normalize("NFKC", decodificada) != decodificada
    ):
        raise no_valida("el contenido decodificado no está en forma canónica")
    if unicodedata.category(decodificada[0]) in ("Mn", "Mc", "Me"):
        raise no_valida("empieza por una marca combinante")
    for caracter in decodificada:
        if not _caracter_permitido(caracter):
            raise no_valida(f"contiene el carácter prohibido {caracter!r}")
    if decodificada.encode("punycode").decode("ascii") != carga:
        raise no_valida("la carga Punycode no es la codificación canónica")


def _caracter_permitido(caracter: str) -> bool:
    if caracter.isascii():
        return bool(_ASCII_PERMITIDO_EN_DECODIFICADO.match(caracter))
    if caracter in SEPARADORES_NO_ASCII:
        return False
    return unicodedata.category(caracter)[0] not in ("C", "Z")


def _motivo_de_transformacion(etiqueta: str) -> str:
    if "ß" in etiqueta:
        return (
            f"la etiqueta {etiqueta!r} contiene ß, que IDNA 2003 convertiría en «ss» "
            "y otro nombre DNS; use la forma A-label (xn--) del nombre que desea consultar"
        )
    return (
        f"la etiqueta {etiqueta!r} se transformaría en otro nombre al convertirla (IDNA 2003); "
        "use la forma A-label (xn--) del nombre que desea consultar"
    )

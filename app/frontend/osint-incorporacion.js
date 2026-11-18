"use strict";

// Lógica pura de la incorporación DNS: sin DOM ni red. Arma el lote con los datos de cada
// registro consultado y resume la respuesta. Las reglas de negocio las valida el backend.
const incorporableTypes = ["A", "AAAA"];
const maxIncorporacionRegistros = 100;

function recordKey(record) {
  return `${record.tipo}|${record.valor}|${record.prioridad ?? ""}`;
}

function esIncorporable(record) {
  return incorporableTypes.includes(record.tipo);
}

// Solo los A y AAAA elegidos. Fuente y fecha son las que llegaron con cada registro.
function construirSolicitudIncorporacion(result, selectedKeys) {
  const registros = result.registros
    .filter((record) => esIncorporable(record) && selectedKeys.has(recordKey(record)))
    .map(({ tipo, valor, fuente, consultado_en }) => ({ tipo, valor, fuente, consultado_en }));
  return { dominio: result.dominio, registros };
}

function motivoSolicitudInvalida(solicitud) {
  if (!solicitud.registros.length) return "Elegí al menos un registro A o AAAA para incorporar.";
  if (solicitud.registros.length > maxIncorporacionRegistros) {
    return `Un lote admite como máximo ${maxIncorporacionRegistros} registros.`;
  }
  return "";
}

// La respuesta llega del servidor: se valida la forma antes de mostrar o dar por guardado el lote.
function respuestaIncorporacionValida(data) {
  const objetoValido = (item) => Boolean(item) && Number.isInteger(item.id)
    && (item.estado === "creada" || item.estado === "reutilizada");
  if (!data || !objetoValido(data.dominio) || !Array.isArray(data.resultados)) return false;
  return data.resultados.every((item) => Boolean(item)
    && typeof item.tipo === "string" && typeof item.valor === "string"
    && objetoValido(item.entidad) && objetoValido(item.relacion) && objetoValido(item.evidencia)
    && Boolean(item.procedencia) && item.procedencia.declarada_por === "cliente"
    && typeof item.procedencia.fuente === "string" && typeof item.procedencia.consultado_en === "string");
}

// Los reutilizados se cuentan aparte: nunca se presentan como elementos nuevos.
function resumirIncorporacion(data) {
  const contar = (objetos) => ({
    creados: objetos.filter((item) => item.estado === "creada").length,
    reutilizados: objetos.filter((item) => item.estado === "reutilizada").length,
  });
  const resultados = data.resultados;
  const unicos = (valores) => [...new Set(valores)];
  return {
    dominio: data.dominio.estado,
    entidades: contar(resultados.map((item) => item.entidad)),
    relaciones: contar(resultados.map((item) => item.relacion)),
    evidencias: contar(resultados.map((item) => item.evidencia)),
    fuentes: unicos(resultados.map((item) => item.procedencia.fuente)),
    consultados: unicos(resultados.map((item) => item.procedencia.consultado_en)),
    registros: resultados.map((item) => ({
      tipo: item.tipo,
      valor: item.valor,
      entidad: item.entidad.estado,
      relacion: item.relacion.estado,
      evidencia: item.evidencia.estado,
    })),
  };
}

// Sin una respuesta válida no se sabe si el lote se guardó: por eso "incierto" es el caso por defecto.
function clasificarFalloIncorporacion(error) {
  if (!error.status) return "incierto";
  if (error.status === 422) return "validacion";
  if (error.status === 409) return "conflicto";
  if (error.status === 503 && error.persistencia === "confirmada") return "guardado_sin_grafo";
  if (error.status === 503) return "ocupada";
  return "incierto";
}

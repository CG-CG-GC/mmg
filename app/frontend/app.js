"use strict";

const $ = (selector) => document.querySelector(selector);
const state = { entities: [], relations: [], cy: null, ready: false, selection: null };
const entitySelects = ["#relation-origin", "#relation-target", "#algorithm-origin", "#algorithm-target"];
const entityTypes = {
  PERSONA: "Persona", ORGANIZACION: "Organización", EMAIL: "Email", USUARIO: "Usuario",
  DOMINIO: "Dominio", SITIO_WEB: "Sitio web", IP: "IP",
};
const relationTypes = {
  POSEE: "Posee", UTILIZA: "Utiliza", TRABAJA_EN: "Trabaja en",
  ADMINISTRA: "Administra", PERTENECE_A: "Pertenece a", APUNTA_A: "Apunta a",
};
const typeColors = {
  PERSONA: "#315b42", ORGANIZACION: "#6d5635", EMAIL: "#77514a",
  USUARIO: "#435d70", DOMINIO: "#665774", SITIO_WEB: "#4b6a69", IP: "#635f46",
};

function message(element, text, kind = "") {
  element.textContent = text;
  element.classList.toggle("error", kind === "error");
  element.classList.toggle("success", kind === "success");
}

async function api(path, options = {}) {
  let response;
  try {
    response = await fetch(`/api/v1${path}`, options);
  } catch (error) {
    throw new Error("No se pudo conectar con el servidor. Comprobá que esté en ejecución.");
  }
  if (!response.ok) {
    let body;
    try {
      body = await response.json();
    } catch (error) {
      throw new Error(`El servidor respondió con un error HTTP ${response.status}.`);
    }
    let detail = body?.detail;
    if (Array.isArray(detail)) {
      detail = detail.map((item) => `${item.loc.slice(1).join(".")}: ${item.msg}`).join("; ");
    }
    const error = new Error(typeof detail === "string" ? detail : `Error HTTP ${response.status}.`);
    error.status = response.status;
    error.persistencia = body?.persistencia;
    throw error;
  }
  return response.json();
}

function post(path, payload) {
  return api(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

function put(path, payload) {
  return api(path, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

function explainUpdateError(error) {
  const explanations = {
    404: "El registro o una entidad relacionada ya no existe.",
    409: "Conflicto: ya existe un registro con esos datos.",
    422: "Revisá los campos indicados.",
    500: "El servidor no pudo completar la actualización. Si la escritura se confirmó, el registro podría haberse guardado; actualizá antes de reintentar.",
  };
  return error.status
    ? `${explanations[error.status] || "No se pudo completar la actualización."} ${error.message}`
    : error.message;
}

function entityName(id) {
  const entity = state.entities.find((item) => item.id === Number(id));
  return entity ? `${entity.valor} · ${entityTypes[entity.tipo] || entity.tipo} (#${entity.id})` : `Entidad #${id}`;
}

function option(value, text) {
  const item = document.createElement("option");
  item.value = value;
  item.textContent = text;
  return item;
}

function updateSelects() {
  for (const selector of entitySelects) {
    const select = $(selector);
    const previous = select.value;
    select.replaceChildren(option("", state.entities.length ? "Seleccioná una entidad" : "No hay entidades disponibles"));
    for (const entity of state.entities) select.append(option(String(entity.id), entityName(entity.id)));
    if (state.entities.some((entity) => String(entity.id) === previous)) select.value = previous;
    select.disabled = !state.ready || state.entities.length === 0;
  }
  $("#relation-form button[type=submit]").disabled = !state.ready || state.entities.length === 0;
  $("#algorithm-form button[type=submit]").disabled = !state.ready || state.entities.length === 0;
}

function appendDetail(list, label, value) {
  const term = document.createElement("dt");
  const description = document.createElement("dd");
  term.textContent = label;
  description.textContent = value == null || value === "" ? "Sin especificar" : String(value);
  list.append(term, description);
}

function setSelectedElement(kind, id) {
  state.selection = { kind, id: Number(id) };
  if (!state.cy) return;
  state.cy.elements().unselect();
  const prefix = kind === "entity" ? "n" : "e";
  const selected = state.cy.getElementById(`${prefix}${id}`);
  if (selected.length) selected.select();
}

function appendEditorField(form, { name, label: labelText, value = "", type = "text", options, rows = 2 }) {
  const id = `edit-${name}`;
  const label = document.createElement("label");
  label.htmlFor = id;
  label.textContent = labelText;
  let control;
  if (options) {
    control = document.createElement("select");
    control.append(option("", "Seleccioná una opción"));
    for (const [valueOption, text] of options) control.append(option(valueOption, text));
    control.value = value;
  } else if (type === "textarea") {
    control = document.createElement("textarea");
    control.rows = rows;
    control.value = value;
  } else {
    control = document.createElement("input");
    control.type = type;
    control.value = value;
  }
  control.id = id;
  control.name = name;
  control.required = name === "tipo" || name === "valor" || name === "valor_normalizado"
    || name === "origen_id" || name === "destino_id";
  form.append(label, control);
  return control;
}

function editorActions(form, onCancel) {
  const actions = document.createElement("div");
  actions.className = "edit-form-actions";
  const save = document.createElement("button");
  save.type = "submit";
  save.className = "primary";
  save.textContent = "Guardar cambios";
  const cancel = document.createElement("button");
  cancel.type = "button";
  cancel.textContent = "Cancelar";
  cancel.addEventListener("click", onCancel);
  actions.append(save, cancel);
  form.append(actions);
  const status = document.createElement("p");
  status.className = "form-message";
  status.setAttribute("role", "status");
  status.setAttribute("aria-live", "polite");
  form.append(status);
  return { save, cancel, status };
}

function showEntityEditor(entity) {
  const selection = $("#selection");
  const form = document.createElement("form");
  form.id = "entity-edit-form";
  form.className = "edit-form";
  const heading = document.createElement("h3");
  heading.textContent = `Editar entidad #${entity.id}`;
  form.append(heading);
  appendEditorField(form, {
    name: "tipo", label: "Tipo", value: entity.tipo,
    options: Object.entries(entityTypes),
  });
  appendEditorField(form, { name: "valor", label: "Valor", value: entity.valor });
  appendEditorField(form, {
    name: "valor_normalizado", label: "Valor normalizado", value: entity.valor_normalizado,
  });
  appendEditorField(form, {
    name: "descripcion", label: "Descripción", value: entity.descripcion || "", type: "textarea",
  });
  appendEditorField(form, {
    name: "metadata", label: "Metadatos JSON", value: entity.metadata ? JSON.stringify(entity.metadata, null, 2) : "", type: "textarea",
  });
  const { save, cancel, status } = editorActions(form, () => showEntity(entity.id));
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    let metadata = null;
    const rawMetadata = data.get("metadata").trim();
    if (rawMetadata) {
      try {
        metadata = JSON.parse(rawMetadata);
      } catch {
        message(status, "Los metadatos deben ser JSON válido.", "error");
        return;
      }
      if (!metadata || typeof metadata !== "object" || Array.isArray(metadata)) {
        message(status, "Los metadatos deben ser un objeto JSON.", "error");
        return;
      }
    }
    if (!window.confirm(`¿Guardar los cambios de la entidad #${entity.id}?`)) return;
    save.disabled = true;
    cancel.disabled = true;
    message(status, "Guardando cambios…");
    try {
      await put(`/entidades/${entity.id}`, {
        tipo: data.get("tipo"),
        valor: validateText(data.get("valor"), "El valor"),
        valor_normalizado: validateText(
          data.get("valor_normalizado"),
          "El valor normalizado",
        ),
        descripcion: data.get("descripcion") || null,
        metadata,
      });
      if (await refresh({ selection: { kind: "entity", id: entity.id } })) {
        message($("#notice"), `Entidad #${entity.id} actualizada.`, "success");
      } else {
        message($("#notice"), "Cambios guardados, pero no se pudo actualizar la vista. Usá Actualizar.", "error");
      }
    } catch (error) {
      message(status, explainUpdateError(error), "error");
    } finally {
      if (form.isConnected) {
        save.disabled = false;
        cancel.disabled = false;
      }
    }
  });
  selection.replaceChildren(form);
}

function showRelationEditor(relation) {
  const selection = $("#selection");
  const form = document.createElement("form");
  form.id = "relation-edit-form";
  form.className = "edit-form";
  const heading = document.createElement("h3");
  heading.textContent = `Editar relación #${relation.id}`;
  form.append(heading);
  appendEditorField(form, {
    name: "origen_id", label: "Origen", value: String(relation.origen_id),
    options: state.entities.map((entity) => [String(entity.id), entityName(entity.id)]),
  });
  appendEditorField(form, {
    name: "tipo", label: "Tipo", value: relation.tipo,
    options: Object.entries(relationTypes),
  });
  appendEditorField(form, {
    name: "destino_id", label: "Destino", value: String(relation.destino_id),
    options: state.entities.map((entity) => [String(entity.id), entityName(entity.id)]),
  });
  appendEditorField(form, {
    name: "descripcion", label: "Descripción", value: relation.descripcion || "", type: "textarea",
  });
  appendEditorField(form, {
    name: "fecha", label: "Fecha (formato ISO)", value: relation.fecha || "",
    type: "text",
  });
  const note = document.createElement("p");
  note.className = "field-help";
  note.textContent = `Las ${relation.evidencias.length} evidencia(s) asociada(s) se conservan.`;
  form.append(note);
  const { save, cancel, status } = editorActions(form, () => showRelation(relation.id));
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!window.confirm(`¿Guardar los cambios de la relación #${relation.id}?`)) return;
    const data = new FormData(form);
    save.disabled = true;
    cancel.disabled = true;
    message(status, "Guardando cambios…");
    try {
      await put(`/relaciones/${relation.id}`, {
        origen_id: Number(data.get("origen_id")),
        destino_id: Number(data.get("destino_id")),
        tipo: data.get("tipo"),
        descripcion: data.get("descripcion") || null,
        fecha: data.get("fecha").trim() || null,
      });
      if (await refresh({ selection: { kind: "relation", id: relation.id } })) {
        message($("#notice"), `Relación #${relation.id} actualizada.`, "success");
      } else {
        message($("#notice"), "Cambios guardados, pero no se pudo actualizar la vista. Usá Actualizar.", "error");
      }
    } catch (error) {
      message(status, explainUpdateError(error), "error");
    } finally {
      if (form.isConnected) {
        save.disabled = false;
        cancel.disabled = false;
      }
    }
  });
  selection.replaceChildren(form);
}

function showEntity(id) {
  const entity = state.entities.find((item) => item.id === Number(id));
  if (!entity) return;
  setSelectedElement("entity", entity.id);
  const list = document.createElement("dl");
  appendDetail(list, "Entidad", `#${entity.id}`);
  appendDetail(list, "Tipo", entityTypes[entity.tipo] || entity.tipo);
  appendDetail(list, "Valor", entity.valor);
  appendDetail(list, "Valor normalizado", entity.valor_normalizado);
  appendDetail(list, "Descripción", entity.descripcion);
  appendDetail(list, "Metadatos", entity.metadata == null ? null : JSON.stringify(entity.metadata, null, 2));
  const edit = document.createElement("button");
  edit.type = "button";
  edit.className = "edit-trigger";
  edit.textContent = "Editar entidad";
  edit.addEventListener("click", () => showEntityEditor(entity));
  $("#selection").replaceChildren(list, edit);
}

function showRelation(id) {
  const relation = state.relations.find((item) => item.id === Number(id));
  if (!relation) return;
  setSelectedElement("relation", relation.id);
  const list = document.createElement("dl");
  appendDetail(list, "Relación", `#${relation.id}`);
  appendDetail(list, "Origen", entityName(relation.origen_id));
  appendDetail(list, "Tipo", relationTypes[relation.tipo] || relation.tipo);
  appendDetail(list, "Destino", entityName(relation.destino_id));
  appendDetail(list, "Descripción", relation.descripcion);
  appendDetail(list, "Fecha", relation.fecha);
  appendDetail(list, "Evidencias", relation.evidencias.length);
  const edit = document.createElement("button");
  edit.type = "button";
  edit.className = "edit-trigger";
  edit.textContent = "Editar relación";
  edit.addEventListener("click", () => showRelationEditor(relation));
  $("#selection").replaceChildren(list, edit);
}

function selectElement(kind, id) {
  if (kind === "entity") showEntity(id); else showRelation(id);
}

function fillList(selector, items, describe, kind) {
  const list = $(selector);
  list.replaceChildren();
  if (!items.length) {
    const item = document.createElement("li");
    item.textContent = "No hay elementos.";
    list.append(item);
    return;
  }
  for (const item of items) {
    const li = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = describe(item);
    button.addEventListener("click", () => selectElement(kind, item.id));
    li.append(button);
    list.append(li);
  }
}

const layoutStorageKey = "mmg.layout";
const layoutOptions = {
  cose: { name: "cose", idealEdgeLength: 240, nodeRepulsion: 10000 },
  breadthfirst: { name: "breadthfirst", directed: true, spacingFactor: 1.4 },
  concentric: { name: "concentric", concentric: (node) => node.degree(), levelWidth: () => 1 },
  circle: { name: "circle" },
  grid: { name: "grid", spacingFactor: 1.3 },
};

function storedLayout() {
  try {
    const value = window.localStorage.getItem(layoutStorageKey);
    return Object.hasOwn(layoutOptions, value) ? value : "cose";
  } catch (error) {
    return "cose";
  }
}

function saveLayout(name) {
  try {
    window.localStorage.setItem(layoutStorageKey, name);
  } catch (error) {
    message($("#notice"), "La distribución se aplicó, pero el navegador no permitió recordarla.", "error");
  }
}

function applyLayout() {
  if (!state.cy || !state.cy.nodes().length) return;
  state.cy.layout({
    ...layoutOptions[$("#layout").value],
    animate: false, fit: true, padding: 45, nodeDimensionsIncludeLabels: true, avoidOverlap: true,
  }).run();
}

function fillStats(selector, items, label) {
  const list = $(selector);
  list.replaceChildren();
  const counts = new Map();
  for (const item of items) counts.set(item.tipo, (counts.get(item.tipo) || 0) + 1);
  if (!counts.size) {
    const empty = document.createElement("li");
    empty.textContent = "Sin elementos.";
    list.append(empty);
    return;
  }
  for (const [type, total] of [...counts].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))) {
    const li = document.createElement("li");
    const name = document.createElement("span");
    const count = document.createElement("strong");
    name.textContent = label[type] || type;
    count.textContent = String(total);
    li.append(name, count);
    list.append(li);
  }
}

function renderGraph(graph) {
  if (!state.cy) return;
  const nodes = graph.nodes.map(({ data }) => ({
    data: { ...data, id: `n${data.entity_id}`, color: typeColors[data.tipo] || "#555d50", display: `${data.label}\n${entityTypes[data.tipo] || data.tipo}` },
  }));
  const edges = graph.edges.map(({ data }) => ({
    data: { ...data, id: `e${data.relation_id}`, source: `n${data.source}`, target: `n${data.target}`, display: relationTypes[data.tipo] || data.tipo },
  }));
  state.cy.elements().remove();
  state.cy.add([...nodes, ...edges]);
  applyLayout();
}

function clearResult() {
  const paragraph = document.createElement("p");
  paragraph.className = "muted";
  paragraph.textContent = "Elegí un algoritmo y una entidad inicial.";
  $("#result").replaceChildren(paragraph);
  if (state.cy) state.cy.elements().removeClass("highlighted");
}

async function refresh(options = {}) {
  state.ready = false;
  updateSelects();
  message($("#notice"), "Actualizando datos del grafo…");
  try {
    const [graph, entities, relations] = await Promise.all([
      api("/grafo"), api("/entidades"), api("/relaciones"),
    ]);
    state.entities = entities;
    state.relations = relations;
    state.ready = true;
    updateSelects();
    renderGraph(graph);
    clearResult();
    message($("#algorithm-message"), "");
    const selected = options.selection;
    const selectionExists = selected && (selected.kind === "entity"
      ? entities.some((entity) => entity.id === selected.id)
      : relations.some((relation) => relation.id === selected.id));
    if (selectionExists) {
      if (selected.kind === "entity") showEntity(selected.id);
      else showRelation(selected.id);
    } else {
      state.selection = null;
      state.cy?.elements().unselect();
      $("#selection").replaceChildren(Object.assign(document.createElement("p"), {
        className: "muted", textContent: "Seleccioná una entidad o relación para consultar sus datos.",
      }));
    }
    fillList("#entity-list", entities, (entity) => entityName(entity.id), "entity");
    fillList("#relation-list", relations, (relation) =>
      `${entityName(relation.origen_id)} → ${relationTypes[relation.tipo] || relation.tipo} → ${entityName(relation.destino_id)} (#${relation.id})`, "relation");
    const entityCount = `${entities.length} ${entities.length === 1 ? "entidad" : "entidades"}`;
    const relationCount = `${relations.length} ${relations.length === 1 ? "relación" : "relaciones"}`;
    $("#graph-count").textContent = `${entityCount} · ${relationCount}`;
    fillStats("#entity-stats", entities, entityTypes);
    fillStats("#relation-stats", relations, relationTypes);
    const graphMessage = $("#graph-message");
    graphMessage.hidden = Boolean(state.cy && entities.length);
    graphMessage.textContent = state.cy ? "El grafo está vacío. Creá una entidad para comenzar." : "No se pudo cargar Cytoscape. Podés consultar los elementos en la lista.";
    message($("#notice"), state.cy ? "Datos actualizados." : "La visualización no está disponible; revisá la carga de Cytoscape.", state.cy ? "success" : "error");
    document.dispatchEvent(new Event("mmg:datos-actualizados"));
    return true;
  } catch (error) {
    message($("#notice"), `No se pudieron actualizar los datos: ${error.message}`, "error");
    $("#graph-message").hidden = false;
    $("#graph-message").textContent = "No se pudo cargar el grafo. Usá Actualizar para volver a intentar.";
    return false;
  }
}

function initializeGraph() {
  if (typeof cytoscape !== "function") return;
  state.cy = cytoscape({
    container: $("#graph"),
    elements: [],
    minZoom: 0.08,
    maxZoom: 3,
    style: [
      { selector: "node", style: {
        "background-color": "data(color)", "label": "data(display)", "color": "#252921",
        "text-valign": "bottom", "text-margin-y": 7, "font-size": 12, "text-wrap": "wrap",
        "text-max-width": 115, "width": 36, "height": 36, "border-width": 2, "border-color": "#fffef9",
      } },
      { selector: "edge", style: {
        "width": 2, "line-color": "#6b7468", "target-arrow-color": "#6b7468", "target-arrow-shape": "triangle",
        "curve-style": "bezier", "label": "data(display)", "font-size": 11, "text-rotation": "autorotate", "text-valign": "top", "color": "#252921",
        "text-background-color": "#f8f9f3", "text-background-opacity": 1, "text-background-padding": 2,
      } },
      { selector: "node:selected, node.highlighted", style: { "border-width": 4, "border-color": "#b37b24" } },
      { selector: "edge:selected, edge.highlighted", style: { "line-color": "#a46712", "target-arrow-color": "#a46712", "width": 4 } },
    ],
  });
  state.cy.on("tap", "node", (event) => showEntity(event.target.data("entity_id")));
  state.cy.on("tap", "edge", (event) => showRelation(event.target.data("relation_id")));
}

function formError(selector, error) {
  message($(selector), error.message, "error");
}

async function submitWrite(form, path, payload, output, success) {
  if (!window.confirm("Esta acción guardará datos en el proyecto. ¿Continuar?")) return;
  const button = form.querySelector("button[type=submit]");
  button.disabled = true;
  message($(output), "Guardando…");
  try {
    await post(path, payload);
    form.reset();
    const refreshed = await refresh();
    message($(output), refreshed ? success : `${success} No se pudo actualizar la vista; usá Actualizar.`, refreshed ? "success" : "error");
  } catch (error) {
    message($(output), `${error.message} Si el servidor falló después de guardar, los datos podrían haberse persistido; actualizá antes de reintentar.`, "error");
    await refresh();
  } finally {
    button.disabled = path === "/relaciones" && (!state.ready || !state.entities.length);
  }
}

function validateText(value, label) {
  if (!value.trim()) throw new Error(`${label} no puede estar vacío.`);
  return value;
}

$("#entity-form").addEventListener("submit", (event) => {
  event.preventDefault();
  try {
    const form = event.currentTarget;
    const data = new FormData(form);
    const payload = {
      tipo: data.get("tipo"),
      valor: validateText(data.get("valor"), "El valor"),
      valor_normalizado: validateText(data.get("valor_normalizado"), "El valor normalizado"),
      descripcion: data.get("descripcion") || null,
    };
    const metadata = data.get("metadata").trim();
    if (metadata) {
      let parsed;
      try { parsed = JSON.parse(metadata); } catch (error) { throw new Error("Los metadatos deben ser JSON válido."); }
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("Los metadatos deben ser un objeto JSON.");
      payload.metadata = parsed;
    }
    submitWrite(form, "/entidades", payload, "#entity-message", "Entidad creada.");
  } catch (error) { formError("#entity-message", error); }
});

$("#relation-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  const payload = {
    origen_id: Number(data.get("origen_id")), destino_id: Number(data.get("destino_id")),
    tipo: data.get("tipo"), descripcion: data.get("descripcion") || null, fecha: data.get("fecha") || null,
  };
  submitWrite(form, "/relaciones", payload, "#relation-message", "Relación creada.");
});

$("#algorithm").addEventListener("change", () => {
  const path = $("#algorithm").value === "camino";
  $("#algorithm-target-field").hidden = !path;
  $("#algorithm-target").required = path;
});

function showResult(algorithm, result) {
  const container = $("#result");
  container.replaceChildren();
  if (state.cy) state.cy.elements().removeClass("highlighted");
  const explanation = document.createElement("p");
  const ids = algorithm === "camino" ? result.entidades_camino : result.orden_recorrido;
  if (algorithm === "camino") {
    explanation.textContent = result.encontrado
      ? `Camino dirigido encontrado: ${result.relaciones_camino.length} relación(es).`
      : "No existe un camino dirigido entre las entidades seleccionadas.";
  } else {
    explanation.textContent = algorithm === "bfs"
      ? "BFS visitó las entidades alcanzables por niveles."
      : "DFS visitó las entidades alcanzables en profundidad.";
  }
  container.append(explanation);
  if (!ids.length) return;
  const list = document.createElement("ol");
  for (const id of ids) {
    const item = document.createElement("li");
    item.textContent = entityName(id) + (algorithm === "bfs" ? ` · nivel ${result.niveles[id]}` : "");
    list.append(item);
    if (state.cy) state.cy.getElementById(`n${id}`).addClass("highlighted");
  }
  container.append(list);
  if (algorithm === "camino" && state.cy) {
    for (const id of result.relaciones_camino) state.cy.getElementById(`e${id}`).addClass("highlighted");
  }
  const note = document.createElement("p");
  note.className = "field-help";
  note.textContent = algorithm === "camino"
    ? "El grafo resalta las entidades y relaciones devueltas por el servidor."
    : "El grafo resalta las entidades visitadas; el orden aparece en la lista.";
  container.append(note);
}

$("#algorithm-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = event.currentTarget.querySelector("button[type=submit]");
  const algorithm = $("#algorithm").value;
  const origin = Number($("#algorithm-origin").value);
  const payload = algorithm === "camino"
    ? { id_origen: origin, id_destino: Number($("#algorithm-target").value) }
    : { id_inicial: origin };
  button.disabled = true;
  message($("#algorithm-message"), "Calculando…");
  clearResult();
  try {
    const result = await post(`/algoritmos/${algorithm}`, payload);
    showResult(algorithm, result);
    message($("#algorithm-message"), "Cálculo completado.", "success");
  } catch (error) { formError("#algorithm-message", error); }
  finally { button.disabled = !state.ready || !state.entities.length; }
});

$("#refresh").addEventListener("click", () => refresh({ selection: state.selection }));
function zoom(factor) {
  if (!state.cy || !state.cy.elements().length) return;
  state.cy.zoom({
    level: state.cy.zoom() * factor,
    renderedPosition: { x: state.cy.width() / 2, y: state.cy.height() / 2 },
  });
}
$("#zoom-in").addEventListener("click", () => zoom(1.25));
$("#zoom-out").addEventListener("click", () => zoom(0.8));
$("#fit").addEventListener("click", () => {
  if (state.cy && state.cy.elements().length) state.cy.fit(undefined, 45);
});
let resizeTimer;
window.addEventListener("resize", () => {
  window.clearTimeout(resizeTimer);
  resizeTimer = window.setTimeout(() => {
    if (state.cy) {
      state.cy.resize();
      if (state.cy.elements().length) state.cy.fit(undefined, 45);
    }
  }, 150);
});
$("#layout").value = storedLayout();
$("#layout").addEventListener("change", (event) => {
  saveLayout(event.target.value);
  applyLayout();
});
initializeGraph();
refresh();

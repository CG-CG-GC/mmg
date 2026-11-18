"use strict";

// Prueba la incorporación DNS en la interfaz sin navegador ni Internet. Ejecuta app.js,
// osint-incorporacion.js y osint.js en un contexto vm con un DOM mínimo y un Cytoscape simulado.
// Imprime un JSON con las observaciones; las aserciones están en el test de pytest.
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const frontend = path.join(__dirname, "..", "..", "app", "frontend");
const scripts = ["app.js", "osint-incorporacion.js", "osint.js"].map((name) => fs.readFileSync(path.join(frontend, name), "utf8"));
const KEY_A1 = "A|192.0.2.1|";
const KEY_A2 = "A|192.0.2.2|";
const KEY_AAAA = "AAAA|2001:db8::1|";
const KEY_CNAME = "CNAME|alias.example.net|";

const env = { focused: null, timers: [], requests: [], mode: "ok", graphFails: false, layoutCalls: [], server: null, cyItems: null };

const flush = async () => {
  for (let turn = 0; turn < 20; turn += 1) await new Promise((resolve) => setImmediate(resolve));
};

function freshServer() {
  return {
    entidades: [
      { id: 1, tipo: "DOMINIO", valor: "example.com", valor_normalizado: "example.com", descripcion: null, metadata: null },
      { id: 5, tipo: "IP", valor: "192.0.2.2", valor_normalizado: "192.0.2.2", descripcion: null, metadata: null },
    ],
    relaciones: [{ id: 3, origen_id: 1, destino_id: 5, tipo: "APUNTA_A", descripcion: null, fecha: null, evidencias: [] }],
    nextId: 20,
  };
}

const queryFixture = {
  dominio: "example.com",
  fuente: "google-public-dns-doh",
  consultado_en: "2026-11-16T12:00:00Z",
  registros: [
    { tipo: "A", valor: "192.0.2.1", estado: "encontrado", fuente: "google-public-dns-doh", consultado_en: "2026-11-16T12:00:00Z", prioridad: null },
    { tipo: "A", valor: "192.0.2.2", estado: "encontrado", fuente: "google-public-dns-doh", consultado_en: "2026-11-16T12:00:00Z", prioridad: null },
    { tipo: "AAAA", valor: "2001:db8::1", estado: "encontrado", fuente: "google-public-dns-doh", consultado_en: "2026-11-16T12:00:00Z", prioridad: null },
    { tipo: "CNAME", valor: "alias.example.net", estado: "encontrado", fuente: "google-public-dns-doh", consultado_en: "2026-11-16T12:00:00Z", prioridad: null },
    { tipo: "MX", valor: "mail.example.com", estado: "encontrado", fuente: "google-public-dns-doh", consultado_en: "2026-11-16T12:00:00Z", prioridad: 10 },
    { tipo: "NS", valor: "ns1.example.com", estado: "encontrado", fuente: "google-public-dns-doh", consultado_en: "2026-11-16T12:00:00Z", prioridad: null },
  ],
  estados: ["A", "AAAA", "CNAME", "MX", "NS"].map((tipo) => ({ tipo, estado: "encontrado", descartados: 0 })),
};

// Reproduce la regla de reutilización del backend: entidades, relaciones y evidencias existentes no se duplican.
function incorporar(server, body) {
  const estado = (creado) => (creado ? "creada" : "reutilizada");
  let dominio = server.entidades.find((item) => item.tipo === "DOMINIO" && item.valor === body.dominio);
  const dominioCreado = !dominio;
  if (!dominio) {
    dominio = { id: server.nextId++, tipo: "DOMINIO", valor: body.dominio, valor_normalizado: body.dominio, descripcion: null, metadata: null };
    server.entidades.push(dominio);
  }
  const resultados = body.registros.map((registro) => {
    let ip = server.entidades.find((item) => item.tipo === "IP" && item.valor === registro.valor);
    const ipCreada = !ip;
    if (!ip) {
      ip = { id: server.nextId++, tipo: "IP", valor: registro.valor, valor_normalizado: registro.valor, descripcion: null, metadata: null };
      server.entidades.push(ip);
    }
    let relacion = server.relaciones.find((item) => item.origen_id === dominio.id && item.destino_id === ip.id);
    const relacionCreada = !relacion;
    if (!relacion) {
      relacion = { id: server.nextId++, origen_id: dominio.id, destino_id: ip.id, tipo: "APUNTA_A", descripcion: null, fecha: null, evidencias: [] };
      server.relaciones.push(relacion);
    }
    return {
      tipo: registro.tipo,
      valor: registro.valor,
      entidad: { id: ip.id, estado: estado(ipCreada) },
      relacion: { id: relacion.id, estado: estado(relacionCreada) },
      evidencia: { id: server.nextId++, estado: "creada" },
      procedencia: { declarada_por: "cliente", fuente: registro.fuente, consultado_en: registro.consultado_en },
    };
  });
  return { dominio: { id: dominio.id, estado: estado(dominioCreado) }, resultados };
}

function reply(status, body) {
  return { ok: status >= 200 && status < 300, status, json: async () => body };
}

function incorporationReply(options) {
  const body = JSON.parse(options.body);
  switch (env.mode) {
    case "ok": return reply(200, incorporar(env.server, body));
    case "422": return reply(422, { detail: "registros[0]: prueba de validación" });
    case "409": return reply(409, { detail: "Hay 2 entidades DOMINIO equivalentes a example.com." });
    case "busy": return reply(503, { detail: "La base de datos está ocupada por otra operación." });
    case "confirmed":
      incorporar(env.server, body);
      return reply(503, { detail: "Los datos de la incorporación sí se guardaron, pero el grafo no pudo reconstruirse.", persistencia: "confirmada" });
    case "network": throw new TypeError("fetch failed");
    case "timeout":
      return new Promise((_, reject) => options.signal.addEventListener("abort", () => {
        reject(Object.assign(new Error("aborted"), { name: "AbortError" }));
      }));
    case "malformed":
      return { ok: true, status: 200, json: async () => { throw new SyntaxError("Unexpected token <"); } };
    case "shape": return reply(200, { foo: 1 });
    case "500": return reply(500, { detail: "Ocurrió un error interno al acceder a los datos del proyecto." });
    default: throw new Error(`Modo no previsto: ${env.mode}`);
  }
}

async function fetchStub(url, options = {}) {
  const route = String(url).replace("/api/v1", "");
  if (route === "/osint/dns/incorporaciones") {
    env.requests.push({ route, body: JSON.parse(options.body) });
    return incorporationReply(options);
  }
  if (route === "/osint/dns") {
    env.requests.push({ route });
    return reply(200, queryFixture);
  }
  if (env.graphFails) return reply(503, { detail: "El grafo no está disponible." });
  if (route === "/grafo") {
    return reply(200, {
      nodes: env.server.entidades.map((item) => ({ data: { entity_id: item.id, label: item.valor, tipo: item.tipo } })),
      edges: env.server.relaciones.map((item) => ({ data: { relation_id: item.id, source: item.origen_id, target: item.destino_id, tipo: item.tipo } })),
    });
  }
  if (route === "/entidades") return reply(200, env.server.entidades);
  if (route === "/relaciones") return reply(200, env.server.relaciones);
  throw new Error(`Ruta no esperada: ${route}`);
}

// Solo selectores simples (etiqueta, #id, .clase, [atributo] y [atributo=valor]).
function matches(node, selector) {
  const tokens = selector.match(/[a-zA-Z]+|#[\w-]+|\.[\w-]+|\[[^\]]+\]/g) || [];
  return tokens.every((token) => {
    if (/^[a-zA-Z]+$/.test(token)) return node.tagName.toLowerCase() === token;
    if (token.startsWith("#")) return node.id === token.slice(1);
    if (token.startsWith(".")) return node.classes.has(token.slice(1));
    const [name, value] = token.slice(1, -1).split("=");
    return name in node.attributes && (value === undefined || node.attributes[name] === value);
  });
}

class FakeElement {
  constructor(doc, tag) {
    this.doc = doc;
    this.tagName = tag;
    this.children = [];
    this.attributes = {};
    this.classes = new Set();
    this.listeners = {};
    this.disabled = false;
    this.hidden = false;
    this.checked = false;
    this.value = "";
  }

  get id() { return this.attributes.id || ""; }
  get className() { return [...this.classes].join(" "); }
  set className(value) { this.classes = new Set(String(value).split(/\s+/).filter(Boolean)); }
  get textContent() {
    return this.children.map((child) => (typeof child === "string" ? child : child.textContent)).join("");
  }
  set textContent(value) { this.children = [String(value)]; }

  get dataset() {
    const attributes = this.attributes;
    const name = (key) => `data-${key.replace(/[A-Z]/g, (letter) => `-${letter.toLowerCase()}`)}`;
    return new Proxy({}, {
      get: (_, key) => attributes[name(key)],
      set: (_, key, value) => { attributes[name(key)] = String(value); return true; },
    });
  }

  get classList() {
    const classes = this.classes;
    return {
      add: (...names) => names.forEach((name) => classes.add(name)),
      remove: (...names) => names.forEach((name) => classes.delete(name)),
      toggle: (name, force) => {
        const on = force ?? !classes.has(name);
        if (on) classes.add(name);
        else classes.delete(name);
        return on;
      },
      contains: (name) => classes.has(name),
    };
  }

  setAttribute(name, value) {
    this.attributes[name] = String(value);
    if (name === "id") this.doc.ids.set(String(value), this);
  }

  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = [...nodes]; }
  addEventListener(type, listener) { (this.listeners[type] ||= []).push(listener); }

  // Como un navegador, un botón deshabilitado no recibe clics.
  trigger(type, extra = {}) {
    if (this.disabled && type === "click") return;
    const event = { type, target: this, preventDefault() {}, ...extra };
    for (const listener of this.listeners[type] || []) listener(event);
  }

  focus() { env.focused = this; }

  descendants() {
    return this.children
      .filter((child) => typeof child !== "string")
      .flatMap((child) => [child, ...child.descendants()]);
  }

  querySelectorAll(selector) { return this.descendants().filter((node) => matches(node, selector)); }
  querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
}

function createDocument() {
  const doc = {
    ids: new Map(),
    registry: new Map(),
    listeners: {},
    createElement: (tag) => new FakeElement(doc, tag),
    querySelector(selector) {
      if (/^#[\w-]+$/.test(selector)) {
        const id = selector.slice(1);
        if (!doc.ids.has(id)) doc.createElement("div").setAttribute("id", id);
        return doc.ids.get(id);
      }
      if (!doc.registry.has(selector)) doc.registry.set(selector, doc.createElement("div"));
      return doc.registry.get(selector);
    },
    addEventListener(type, listener) { (doc.listeners[type] ||= []).push(listener); },
    dispatchEvent(event) {
      for (const listener of doc.listeners[event.type] || []) listener(event);
      return true;
    },
  };
  return doc;
}

function createCytoscape(items) {
  const collection = (list) => Object.assign(list, {
    remove() {
      for (const item of list) items.delete(item.data.id);
      return collection([]);
    },
    unselect() { return this; },
    select() { return this; },
    addClass() { return this; },
    removeClass() { return this; },
  });
  return {
    add(elements) {
      for (const element of elements) {
        // Cytoscape rechaza ids repetidos: el fallo quedaría visible en la prueba.
        if (items.has(element.data.id)) throw new Error(`Id duplicado en Cytoscape: ${element.data.id}`);
        items.set(element.data.id, element);
      }
      return collection([]);
    },
    elements: () => collection([...items.values()]),
    nodes: () => collection([...items.values()].filter((item) => item.data.source === undefined)),
    getElementById: (id) => collection(items.has(id) ? [items.get(id)] : []),
    layout: (options) => ({ run() { env.layoutCalls.push(options.name); } }),
    on() {},
    zoom() { return 1; },
    width: () => 800,
    height: () => 600,
    fit() {},
    resize() {},
  };
}

function createContext(storage) {
  const doc = createDocument();
  const context = {
    console,
    document: doc,
    AbortController,
    Event: class { constructor(type) { this.type = type; } },
    MutationObserver: class { observe() {} },
    sessionStorage: {
      getItem: (key) => (storage.has(key) ? storage.get(key) : null),
      setItem: (key, value) => storage.set(key, String(value)),
      removeItem: (key) => storage.delete(key),
    },
    cytoscape: () => {
      env.cyItems = new Map();
      return createCytoscape(env.cyItems);
    },
    fetch: fetchStub,
    window: {
      setTimeout: (fn, ms) => {
        const timer = { fn, ms, cleared: false };
        env.timers.push(timer);
        return timer;
      },
      clearTimeout: (timer) => { if (timer) timer.cleared = true; },
      addEventListener() {},
    },
  };
  vm.createContext(context);
  for (const source of scripts) vm.runInContext(source, context);
  return { context, doc };
}

// Estado inicial como en index.html: todos los tipos marcados y controles de incorporación cerrados.
async function openSession(storage) {
  const ctx = createContext(storage);
  await flush();
  for (const type of ["A", "AAAA", "CNAME", "MX", "NS"]) ctx.doc.querySelector(`#osint-type-${type}`).checked = true;
  ctx.doc.querySelector("#osint-confirm").hidden = true;
  return ctx;
}

async function query(ctx) {
  ctx.doc.querySelector("#osint-domain").value = "example.com";
  ctx.doc.querySelector("#osint-form").trigger("submit");
  await flush();
}

function checkbox(ctx, attribute, key) {
  return ctx.doc.querySelector("#osint-preview").querySelectorAll(`input[${attribute}]`)
    .find((input) => input.dataset.key === key);
}

// Devuelve false si el control está deshabilitado: el usuario no puede cambiarlo.
function toggle(ctx, attribute, key, value) {
  const input = checkbox(ctx, attribute, key);
  if (input.disabled) return false;
  input.checked = value;
  input.trigger("change");
  return true;
}

function snapshot(ctx) {
  const { doc } = ctx;
  const preview = doc.querySelector("#osint-preview");
  const message = doc.querySelector("#osint-incorporate-message");
  return {
    message: message.textContent,
    messageError: message.classList.contains("error"),
    messageSuccess: message.classList.contains("success"),
    count: doc.querySelector("#osint-incorporate-count").textContent,
    openDisabled: doc.querySelector("#osint-incorporate-open").disabled,
    openText: doc.querySelector("#osint-incorporate-open").textContent,
    refreshVisible: !doc.querySelector("#osint-incorporate-refresh").hidden,
    confirmOpen: !doc.querySelector("#osint-confirm").hidden,
    selectedChecked: preview.querySelectorAll("input[data-incorporar]").filter((input) => input.checked).length,
    incorporateDisabled: preview.querySelectorAll("input[data-incorporar]").filter((input) => input.disabled).length,
    badges: preview.querySelectorAll(".osint-badge").filter((node) => node.textContent === "Incorporado").length,
    result: doc.querySelector("#osint-incorporate-result").textContent,
    focused: env.focused ? env.focused.id : "",
    requests: env.requests.filter((request) => request.route === "/osint/dns/incorporaciones").length,
  };
}

function resetEnv(mode) {
  Object.assign(env, { focused: null, timers: [], requests: [], mode, graphFails: false, layoutCalls: [], server: freshServer() });
}

// Revisa e incorpora las claves indicadas, abre la confirmación y envía el lote.
async function attempt(mode, keys, storage = new Map()) {
  resetEnv(mode);
  const ctx = await openSession(storage);
  await query(ctx);
  for (const key of keys) {
    toggle(ctx, "data-revisado", key, true);
    toggle(ctx, "data-incorporar", key, true);
  }
  ctx.doc.querySelector("#osint-incorporate-open").trigger("click");
  env.focused = null;
  ctx.doc.querySelector("#osint-confirm-send").trigger("click");
  await flush();
  if (mode === "timeout") {
    // Dispara el temporizador de incorporación (30 s) sin esperar en tiempo real.
    for (const timer of env.timers.filter((item) => item.ms === 30000 && !item.cleared)) {
      timer.cleared = true;
      timer.fn();
    }
    await flush();
  }
  return ctx;
}

async function scenarioSuccess() {
  resetEnv("ok");
  const storage = new Map();
  const ctx = await openSession(storage);
  await query(ctx);
  const unreviewedDisabled = checkbox(ctx, "data-incorporar", KEY_A1).disabled;
  const cnameHasControl = ctx.doc.querySelector("#osint-preview").querySelectorAll("input[data-incorporar]")
    .some((input) => input.dataset.key === KEY_CNAME);
  const notes = ctx.doc.querySelector("#osint-preview").querySelectorAll(".osint-note").map((node) => node.textContent);
  for (const key of [KEY_A1, KEY_A2, KEY_AAAA, KEY_CNAME]) toggle(ctx, "data-revisado", key, true);
  toggle(ctx, "data-incorporar", KEY_A1, true);
  toggle(ctx, "data-incorporar", KEY_A2, true);
  toggle(ctx, "data-incorporar", KEY_AAAA, true);
  const selectedBeforeSend = snapshot(ctx);

  // Sin revisión no se puede seleccionar; al desmarcar Revisado se quita la selección.
  toggle(ctx, "data-revisado", KEY_AAAA, false);
  const afterUnreview = snapshot(ctx).count;
  toggle(ctx, "data-revisado", KEY_AAAA, true);
  toggle(ctx, "data-incorporar", KEY_AAAA, true);

  ctx.doc.querySelector("#layout").value = "circle";
  vm.runInContext("showEntity(1)", ctx.context);
  const selectionBefore = vm.runInContext("JSON.stringify(state.selection)", ctx.context);

  ctx.doc.querySelector("#osint-incorporate-open").trigger("click");
  const confirmText = ctx.doc.querySelector("#osint-confirm").textContent;
  const confirmFocus = env.focused ? env.focused.id : "";
  const requestsBeforeConfirm = env.requests.length;

  const send = ctx.doc.querySelector("#osint-confirm-send");
  send.trigger("click");
  send.trigger("click");
  await flush();
  const sent = env.requests.find((request) => request.route === "/osint/dns/incorporaciones");
  const after = snapshot(ctx);
  const nodeIds = [...env.cyItems.values()].filter((item) => item.data.source === undefined).map((item) => item.data.id).sort();
  const edgeIds = [...env.cyItems.values()].filter((item) => item.data.source !== undefined).map((item) => item.data.id).sort();
  const layoutSelected = ctx.doc.querySelector("#layout").value;
  const selectionAfter = vm.runInContext("JSON.stringify(state.selection)", ctx.context);
  return {
    unreviewedDisabled,
    cnameHasControl,
    notes,
    selectedBeforeSend: { count: selectedBeforeSend.count, selectedChecked: selectedBeforeSend.selectedChecked },
    afterUnreview,
    selectionBefore,
    confirmText,
    confirmFocus,
    requestsBeforeConfirm,
    body: sent.body,
    after,
    graph: { nodeIds, edgeIds, serverEntities: env.server.entidades.length, serverRelations: env.server.relaciones.length },
    layoutSelected,
    lastLayoutCall: env.layoutCalls[env.layoutCalls.length - 1],
    selectionAfter,
  };
}

async function scenarioConfirmControls() {
  resetEnv("ok");
  const ctx = await openSession(new Map());
  await query(ctx);
  toggle(ctx, "data-revisado", KEY_A1, true);
  toggle(ctx, "data-incorporar", KEY_A1, true);
  ctx.doc.querySelector("#osint-incorporate-open").trigger("click");
  ctx.doc.querySelector("#osint-confirm-cancel").trigger("click");
  const cancel = snapshot(ctx);
  ctx.doc.querySelector("#osint-incorporate-open").trigger("click");
  ctx.doc.querySelector("#osint-confirm").trigger("keydown", { key: "Escape" });
  const escape = snapshot(ctx);
  return { cancel, escape };
}

async function scenarioRecovery() {
  const ctx = await attempt("confirmed", [KEY_A1, KEY_A2]);
  const sentState = snapshot(ctx);
  env.graphFails = true;
  ctx.doc.querySelector("#osint-incorporate-refresh").trigger("click");
  await flush();
  const failed = snapshot(ctx);
  env.graphFails = false;
  ctx.doc.querySelector("#osint-incorporate-refresh").trigger("click");
  await flush();
  const recovered = snapshot(ctx);
  return { sentState, failed, recovered };
}

async function scenarioSession() {
  const storage = new Map();
  const ctx = await attempt("422", [KEY_A1, KEY_A2], storage);
  const afterError = snapshot(ctx);
  const restored = await openSession(storage);
  await flush();
  const restoredSnapshot = snapshot(restored);
  await query(restored);
  const newQuery = snapshot(restored);
  return { afterError, restored: restoredSnapshot, newQuery };
}

function pureChecks() {
  const ctx = createContext(new Map());
  const run = (code) => vm.runInContext(code, ctx.context);
  return {
    respuestaVacia: run("respuestaIncorporacionValida({})"),
    respuestaCorrecta: run(`respuestaIncorporacionValida({
      dominio: { id: 1, estado: "creada" },
      resultados: [{ tipo: "A", valor: "192.0.2.1",
        entidad: { id: 2, estado: "creada" }, relacion: { id: 3, estado: "creada" }, evidencia: { id: 4, estado: "creada" },
        procedencia: { declarada_por: "cliente", fuente: "x", consultado_en: "2026-11-16T12:00:00Z" } }],
    })`),
    clasificacionConfirmada: run(`clasificarFalloIncorporacion({ status: 503, persistencia: "confirmada" })`),
    clasificacionOcupada: run(`clasificarFalloIncorporacion({ status: 503 })`),
    clasificacionConflicto: run(`clasificarFalloIncorporacion({ status: 409 })`),
    clasificacionValidacion: run(`clasificarFalloIncorporacion({ status: 422 })`),
    clasificacionHttp500: run(`clasificarFalloIncorporacion({ status: 500 })`),
    clasificacionSinRespuesta: run(`clasificarFalloIncorporacion(new TypeError("red"))`),
    motivoVacio: run(`motivoSolicitudInvalida({ dominio: "a.com", registros: [] })`),
    resumenReutilizados: run(`JSON.stringify(resumirIncorporacion({
      dominio: { id: 1, estado: "reutilizada" },
      resultados: [
        { tipo: "A", valor: "192.0.2.1", entidad: { id: 2, estado: "creada" }, relacion: { id: 3, estado: "creada" }, evidencia: { id: 4, estado: "creada" }, procedencia: { declarada_por: "cliente", fuente: "x", consultado_en: "2026-11-16T12:00:00Z" } },
        { tipo: "A", valor: "192.0.2.2", entidad: { id: 5, estado: "reutilizada" }, relacion: { id: 6, estado: "reutilizada" }, evidencia: { id: 7, estado: "creada" }, procedencia: { declarada_por: "cliente", fuente: "x", consultado_en: "2026-11-16T12:00:00Z" } },
      ],
    }))`),
  };
}

(async () => {
  const results = {};
  results.pure = pureChecks();
  results.success = await scenarioSuccess();
  results.confirmControls = await scenarioConfirmControls();
  results.recovery = await scenarioRecovery();
  results.session = await scenarioSession();
  const errorModes = { validacion: "422", conflicto: "409", ocupada: "busy", red: "network", tiempo: "timeout", formato: "malformed", forma: "shape", http500: "500" };
  results.errors = {};
  for (const [label, mode] of Object.entries(errorModes)) {
    const ctx = await attempt(mode, [KEY_A1, KEY_A2]);
    results.errors[label] = snapshot(ctx);
  }
  console.log(JSON.stringify(results));
})().catch((error) => {
  console.error(error);
  process.exit(1);
});

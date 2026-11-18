"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

function fakeElement() {
  const store = {};
  const target = function () {};
  return new Proxy(target, {
    get(_, key) {
      if (key in store) return store[key];
      if (key === Symbol.toPrimitive) return () => "";
      if (key === "length") return 0;
      if (key === "classList") return { toggle() {}, add() {}, remove() {} };
      return fakeElement();
    },
    set(_, key, value) { store[key] = value; return true; },
    apply() { return fakeElement(); },
  });
}

const elements = {};
const handlers = {};
const document = {
  querySelector(selector) {
    if (!elements[selector]) {
      elements[selector] = fakeElement();
      elements[selector].addEventListener = (type, handler) => { handlers[`${selector}:${type}`] = handler; };
    }
    return elements[selector];
  },
  createElement: () => fakeElement(),
};

const data = {
  entities: [
    { id: 1, tipo: "PERSONA", valor: "Ana", valor_normalizado: "ana", descripcion: null },
    { id: 2, tipo: "EMAIL", valor: "ana@example.com", valor_normalizado: "ana@example.com", descripcion: null },
  ],
  relations: [
    { id: 7, origen_id: 1, destino_id: 2, tipo: "POSEE", descripcion: null, evidencias: [] },
  ],
};

const context = {
  document,
  console,
  window: { addEventListener() {}, setTimeout, clearTimeout, confirm: () => true },
  fetch: async (url) => {
    const route = String(url).replace("/api/v1", "");
    const body = route === "/entidades" ? data.entities
      : route === "/relaciones" ? data.relations
        : { nodes: [], edges: [] };
    return { ok: true, status: 200, json: async () => body };
  },
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, "..", "..", "app", "frontend", "app.js"), "utf8"), context);

const sleep = () => new Promise((resolve) => setTimeout(resolve, 20));
const selection = () => vm.runInContext("JSON.stringify(state.selection)", context);

async function pressRefresh() {
  await handlers["#refresh:click"]();
  await sleep();
  return selection();
}

(async () => {
  await sleep();
  const results = {};

  vm.runInContext("showEntity(1)", context);
  results.entity = await pressRefresh();

  vm.runInContext("showRelation(7)", context);
  results.relation = await pressRefresh();

  data.relations = [];
  results.missingRelation = await pressRefresh();

  vm.runInContext("showEntity(2)", context);
  data.entities = data.entities.filter((entity) => entity.id !== 2);
  results.missingEntity = await pressRefresh();

  console.log(JSON.stringify(results));
})();

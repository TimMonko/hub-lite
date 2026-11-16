// The home page's sorting, filters and search. Plain JavaScript, no build.
//
// The plugin list is already in the page (templates/index.html). With no
// search term, this script only hides and reorders those cards, using their
// data-* attributes. With a term, it asks Pagefind, then shows the matching
// cards in Pagefind's order. Pagefind (its JS, WebAssembly and index) loads
// when the search box is focused, not when the page opens.

const PAGE_SIZE = 30; // search results shown per "Show more"
const FIRST_SCREEN = 9; // shown as soon as their data arrives; the rest follow

// Filter name (as in the plugin pages' data-pagefind-filter) -> the URL
// parameter the plugin pages link with, and the card's data-* attribute.
const FILTERS = {
  plugin_types: { param: "pluginType", attr: "pluginTypes", label: "Plugin type" },
  python_versions: { param: "python", attr: "pythonVersions", label: "Python" },
  reads: { param: "readerFileExtensions", attr: "reads", label: "Opens" },
  writes: { param: "writerFileExtensions", attr: "writes", label: "Saves" },
};

const finder = document.querySelector(".finder");
const form = finder.querySelector("form");
const input = form.querySelector("input[type=search]");
const typeBoxes = [...finder.querySelectorAll("input[name=pluginType]")];
const sortSelect = finder.querySelector("select[name=sort]");
const activeFilters = finder.querySelector(".active-filters");
const count = document.querySelector(".count");
const list = document.getElementById("plugins");
const moreButton = document.querySelector(".more");
const cards = [...list.children];
const cardByName = new Map(cards.map((card) => [card.dataset.name, card]));

// State: the search term, plugin types (any of), and other filters from the
// URL (all of; each a list of values).
const state = { q: "", types: new Set(), sort: "updated", other: {} };

// --- Pagefind, loaded on first need -------------------------------------

let pagefindPromise;
function pagefind() {
  pagefindPromise ??= import(new URL("pagefind/pagefind.js", document.baseURI)).then(
    async (pf) => {
      await pf.init(); // fetch the WebAssembly and index metadata now
      return pf;
    },
  );
  return pagefindPromise;
}

// --- Browsing: no search term -------------------------------------------

function values(card, filter) {
  const raw = card.dataset[FILTERS[filter].attr];
  return raw ? raw.split("|") : [];
}

function matchesFilters(card) {
  if (state.types.size && !values(card, "plugin_types").some((t) => state.types.has(t))) {
    return false;
  }
  return Object.entries(state.other).every(([filter, wanted]) =>
    wanted.every((value) => values(card, filter).includes(value)),
  );
}

const SORTS = {
  updated: (a, b) => b.dataset.updated.localeCompare(a.dataset.updated),
  released: (a, b) => b.dataset.released.localeCompare(a.dataset.released),
  name: (a, b) => a.dataset.title.localeCompare(b.dataset.title),
};

function browse() {
  const shown = cards.filter(matchesFilters).sort(SORTS[state.sort]);
  for (const card of cards) card.hidden = true;
  for (const card of shown) card.hidden = false;
  list.append(...shown); // moves them, in order, to the top of the list
  moreButton.hidden = true;
  count.textContent = `${shown.length} plugins`;
}

// --- Searching: Pagefind ------------------------------------------------

function pagefindFilters() {
  const filters = {};
  if (state.types.size) filters.plugin_types = { any: [...state.types] };
  for (const [filter, wanted] of Object.entries(state.other)) filters[filter] = wanted;
  return filters;
}

let results = []; // the current search's results, best first
let shownResults = 0;

async function search() {
  const term = state.q;
  const pf = await pagefind();
  const response = await pf.debouncedSearch(term, { filters: pagefindFilters() }, 150);
  // null: a newer keystroke replaced this search. A changed term: the box was
  // cleared (or changed) while this one ran, and browse() has the list now.
  if (response === null || state.q !== term) return;
  results = response.results;
  shownResults = 0;
  for (const card of cards) card.hidden = true;
  count.textContent =
    results.length === 1 ? `1 plugin matches “${state.q}”` : `${results.length} plugins match “${state.q}”`;
  // Each result costs a fetch, so fill the first screen first.
  await showMoreResults(FIRST_SCREEN);
  await showMoreResults(PAGE_SIZE - FIRST_SCREEN);
}

async function showMoreResults(size = PAGE_SIZE) {
  const batch = results.slice(shownResults, shownResults + size);
  const searchedFor = results;
  if (!batch.length) return;
  // Each result's data holds its URL; the URL's file name is the card's name.
  const pages = await Promise.all(batch.map((result) => result.data()));
  if (searchedFor !== results) return; // a newer search finished first
  const found = pages
    .map((page) => cardByName.get(decodeURIComponent(page.url.split("/").pop().replace(/\.html$/, ""))))
    .filter(Boolean);
  const before = list.children[cards.filter((c) => !c.hidden).length] ?? null;
  for (const card of found) {
    card.hidden = false;
    list.insertBefore(card, before);
  }
  shownResults += batch.length;
  moreButton.hidden = shownResults >= results.length;
  list.dataset.state = "results"; // for tests and the measuring script
}

// --- Wiring --------------------------------------------------------------

function update() {
  const searching = state.q.length > 0;
  sortSelect.disabled = searching;
  sortSelect.value = searching ? "relevance" : state.sort;
  sortSelect.title = searching ? "Search results are ordered by best match" : "";
  renderActiveFilters();
  writeUrl();
  if (searching) search();
  else browse();
}

function renderActiveFilters() {
  activeFilters.replaceChildren();
  for (const [filter, wanted] of Object.entries(state.other)) {
    for (const value of wanted) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = `${FILTERS[filter].label}: ${value} ✕`;
      button.setAttribute("aria-label", `Remove filter ${FILTERS[filter].label} ${value}`);
      button.addEventListener("click", () => {
        state.other[filter] = wanted.filter((v) => v !== value);
        if (!state.other[filter].length) delete state.other[filter];
        update();
      });
      activeFilters.append(button);
    }
  }
  activeFilters.hidden = !activeFilters.children.length;
}

function readUrl() {
  const params = new URLSearchParams(location.search);
  state.q = (params.get("q") ?? "").trim();
  state.types = new Set(params.getAll(FILTERS.plugin_types.param));
  state.sort = SORTS[params.get("sort")] ? params.get("sort") : "updated";
  for (const [filter, { param }] of Object.entries(FILTERS)) {
    if (filter !== "plugin_types" && params.getAll(param).length) state.other[filter] = params.getAll(param);
  }
  input.value = state.q;
  for (const box of typeBoxes) box.checked = state.types.has(box.value);
}

function writeUrl() {
  const params = new URLSearchParams();
  if (state.q) params.set("q", state.q);
  for (const type of state.types) params.append(FILTERS.plugin_types.param, type);
  for (const [filter, wanted] of Object.entries(state.other)) {
    for (const value of wanted) params.append(FILTERS[filter].param, value);
  }
  if (state.sort !== "updated") params.set("sort", state.sort);
  const query = params.toString();
  history.replaceState(null, "", query ? `?${query}` : location.pathname);
}

// Load Pagefind once the page is shown and the browser is idle, or as soon
// as someone heads for the search box, whichever comes first.
input.addEventListener("focus", pagefind, { once: true });
input.addEventListener("pointerenter", pagefind, { once: true });
const whenIdle = window.requestIdleCallback ?? ((callback) => setTimeout(callback, 1));
if (document.readyState === "complete") whenIdle(pagefind);
else window.addEventListener("load", () => whenIdle(pagefind), { once: true });
input.addEventListener("input", () => {
  state.q = input.value.trim();
  update();
});
input.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && input.value) {
    input.value = "";
    state.q = "";
    update();
  }
});
form.addEventListener("submit", (event) => event.preventDefault());
for (const box of typeBoxes) {
  box.addEventListener("change", () => {
    state.types = new Set(typeBoxes.filter((b) => b.checked).map((b) => b.value));
    update();
  });
}
sortSelect.addEventListener("change", () => {
  state.sort = sortSelect.value;
  update();
});
moreButton.addEventListener("click", () => showMoreResults());
document.addEventListener("keydown", (event) => {
  const typing = event.target.closest?.("input, select, textarea");
  if (event.key === "/" && !typing) {
    event.preventDefault();
    input.focus();
  }
});

finder.hidden = false;
readUrl();
update();

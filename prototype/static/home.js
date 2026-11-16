// The home page's search, filters and sorting. Plain JavaScript, no build.
//
// The plugin list is already in the page (templates/index.html). Pagefind
// only ranks: a search returns result ids, and each card carries its
// plugin's id (data-pf). Every filter and sort then runs on the cards'
// data-* attributes, the same way with or without a search term, and no
// result's data is fetched. Pagefind (JS, WebAssembly, index) loads once the
// page is shown and the browser is idle, or when someone heads for search.

const finder = document.querySelector(".finder");
const input = finder.querySelector("#q");
const typeMenu = finder.querySelector(".dropdown");
const typeBoxes = [...typeMenu.querySelectorAll("input[name=pluginType]")];
const typeValue = typeMenu.querySelector(".dropdown-value");
const formatInput = finder.querySelector("#format");
const formatMode = finder.querySelector("#formatMode");
const pythonSelect = finder.querySelector("#python");
const sinceInput = finder.querySelector("#updatedSince");
const sortSelect = finder.querySelector("#sort");
const clearButton = finder.querySelector(".clear");
const count = document.querySelector(".count");
const list = document.getElementById("plugins");
const cards = [...list.children];

const state = {
  q: "",
  types: new Set(), // any of
  format: "", // ".tif"
  formatMode: "any", // "any" | "opens" | "saves"
  python: "",
  since: "", // YYYY-MM-DD
  sort: "", // "" = best match while searching, else recently updated
};
let rank = null; // the current search's results: Pagefind id -> position

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

async function search() {
  const term = state.q;
  const pf = await pagefind();
  const response = await pf.debouncedSearch(term, {}, 120);
  // null: a newer keystroke replaced this search. A changed term: the box
  // was changed while this one ran.
  if (response === null || state.q !== term) return;
  rank = new Map(response.results.map((result, i) => [result.id, i]));
  render();
}

// --- Filtering and sorting ------------------------------------------------

function words(card, key) {
  const raw = card.dataset[key];
  return raw ? raw.split(" ") : [];
}

// ".tif" finds .tif and .tiff (starts with) and .ome.tif (ends with).
function normalizeFormat(text) {
  const ext = text.trim().toLowerCase().replace(/^\*+/, "");
  if (!ext || ext === ".") return "";
  return ext.startsWith(".") ? ext : `.${ext}`;
}

function matches(card) {
  if (rank && !rank.has(card.dataset.pf)) return false;
  if (state.types.size && !words(card, "types").some((t) => state.types.has(t))) return false;
  if (state.python && !words(card, "python").includes(state.python)) return false;
  if (state.since && !(card.dataset.updated >= state.since)) return false;
  if (state.format) {
    const formats = state.formatMode === "any"
      ? [...words(card, "opens"), ...words(card, "saves")]
      : words(card, state.formatMode);
    if (!formats.some((f) => f.startsWith(state.format) || f.endsWith(state.format))) return false;
  }
  return true;
}

const SORTS = {
  best: (a, b) => rank.get(a.dataset.pf) - rank.get(b.dataset.pf),
  updated: (a, b) => b.dataset.updated.localeCompare(a.dataset.updated),
  released: (a, b) => b.dataset.released.localeCompare(a.dataset.released),
  name: (a, b) => a.dataset.title.localeCompare(b.dataset.title),
};

function effectiveSort() {
  if (state.sort === "best" || !state.sort) return rank ? "best" : "updated";
  return state.sort;
}

function filtersActive() {
  return state.types.size || state.format || state.python || state.since;
}

function render() {
  const shown = cards.filter(matches).sort(SORTS[effectiveSort()]);
  for (const card of cards) card.hidden = true;
  for (const card of shown) card.hidden = false;
  list.append(...shown); // moves them, in order, to the top of the list

  const narrowed = rank || filtersActive();
  const matching = state.q ? ` match “${state.q}”` : "";
  count.textContent = narrowed
    ? `${shown.length} of ${cards.length} plugins${matching}`
    : `${cards.length} plugins`;
  list.dataset.state = rank ? "results" : "browse"; // for tests and measuring

  sortSelect.value = effectiveSort();
  sortSelect.options[0].disabled = !rank;
  typeValue.textContent = state.types.size
    ? typeBoxes.filter((b) => b.checked).map((b) => b.parentElement.textContent.trim()).join(", ")
    : "Any";
  clearButton.hidden = !filtersActive();
  writeUrl();
}

function update() {
  if (state.q) {
    search(); // renders when results arrive; until then the list stays
  } else {
    rank = null;
    render();
  }
}

// --- The URL holds the state, so a view can be shared -----------------------

function readUrl() {
  const params = new URLSearchParams(location.search);
  state.q = (params.get("q") ?? "").trim();
  state.types = new Set(params.getAll("pluginType"));
  state.format = normalizeFormat(params.get("format") ?? "");
  state.formatMode = ["opens", "saves"].includes(params.get("formatMode")) ? params.get("formatMode") : "any";
  // Plugin pages link with napari hub's older names for these.
  if (params.get("readerFileExtensions")) {
    state.format = normalizeFormat(params.get("readerFileExtensions"));
    state.formatMode = "opens";
  } else if (params.get("writerFileExtensions")) {
    state.format = normalizeFormat(params.get("writerFileExtensions"));
    state.formatMode = "saves";
  }
  state.python = params.get("python") ?? "";
  state.since = params.get("updatedSince") ?? "";
  state.sort = SORTS[params.get("sort")] ? params.get("sort") : "";

  input.value = state.q;
  for (const box of typeBoxes) box.checked = state.types.has(box.value);
  formatInput.value = state.format;
  formatMode.value = state.formatMode;
  pythonSelect.value = state.python;
  if (pythonSelect.value !== state.python) state.python = ""; // not an offered version
  sinceInput.value = state.since;
}

function writeUrl() {
  const params = new URLSearchParams();
  if (state.q) params.set("q", state.q);
  for (const type of state.types) params.append("pluginType", type);
  if (state.format) params.set("format", state.format);
  if (state.format && state.formatMode !== "any") params.set("formatMode", state.formatMode);
  if (state.python) params.set("python", state.python);
  if (state.since) params.set("updatedSince", state.since);
  if (state.sort) params.set("sort", state.sort);
  const query = params.toString();
  history.replaceState(null, "", query ? `?${query}` : location.pathname);
}

// --- Wiring --------------------------------------------------------------

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
finder.querySelector("form").addEventListener("submit", (event) => event.preventDefault());

for (const box of typeBoxes) {
  box.addEventListener("change", () => {
    state.types = new Set(typeBoxes.filter((b) => b.checked).map((b) => b.value));
    render();
  });
}
// Close the type menu on a click elsewhere or Escape.
document.addEventListener("click", (event) => {
  if (!typeMenu.contains(event.target)) typeMenu.open = false;
});
typeMenu.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    typeMenu.open = false;
    typeMenu.querySelector("summary").focus();
  }
});

formatInput.addEventListener("input", () => {
  state.format = normalizeFormat(formatInput.value);
  render();
});
formatMode.addEventListener("change", () => {
  state.formatMode = formatMode.value;
  render();
});
pythonSelect.addEventListener("change", () => {
  state.python = pythonSelect.value;
  render();
});
sinceInput.addEventListener("change", () => {
  state.since = sinceInput.value;
  render();
});
sortSelect.addEventListener("change", () => {
  state.sort = sortSelect.value;
  render();
});
clearButton.addEventListener("click", () => {
  Object.assign(state, { types: new Set(), format: "", formatMode: "any", python: "", since: "" });
  for (const box of typeBoxes) box.checked = false;
  formatInput.value = "";
  formatMode.value = "any";
  pythonSelect.value = "";
  sinceInput.value = "";
  render();
});

document.addEventListener("keydown", (event) => {
  const typing = event.target.closest?.("input, select, textarea");
  if (event.key === "/" && !typing) {
    event.preventDefault();
    input.focus();
  }
});

finder.hidden = false;
readUrl();
render(); // filters from the URL apply at once; search results follow
if (state.q) search();

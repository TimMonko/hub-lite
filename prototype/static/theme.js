// The navbar's light / dark / auto button, as on napari.org.
//
// The choice is saved in this browser (localStorage "theme"). "light" and
// "dark" set <html data-theme>, which napari-tokens.css, pygments.css and
// hub.css all follow; "auto" removes it, and the CSS follows the system
// setting. base.html applies a saved choice before the first paint.

const ORDER = ["light", "dark", "auto"];
const LABELS = {
  light: "Theme: light. Switch to dark",
  dark: "Theme: dark. Switch to follow the system",
  auto: "Theme: follows the system. Switch to light",
};
// The address bar's colour, as the header's (base.html's theme-color metas).
const NAVBAR = { light: "#80d1ff", dark: "#4d485c" };

function saved() {
  try {
    return localStorage.getItem("theme") ?? "auto";
  } catch {
    return "auto"; // storage blocked: the system setting decides
  }
}

function apply(mode) {
  const root = document.documentElement;
  if (mode === "auto") delete root.dataset.theme;
  else root.dataset.theme = mode;
  // Forced: both theme-color metas take the chosen header colour. Auto:
  // each goes back to its own (light, dark) colour.
  const metas = document.querySelectorAll('meta[name="theme-color"]');
  metas.forEach((meta, i) => {
    meta.content = mode === "auto" ? Object.values(NAVBAR)[i] : NAVBAR[mode];
  });
  const button = document.querySelector(".theme-toggle");
  button.dataset.mode = mode;
  button.querySelector(".visually-hidden").textContent = LABELS[mode];
  button.title = LABELS[mode];
}

const button = document.querySelector(".theme-toggle");
button.addEventListener("click", () => {
  const next = ORDER[(ORDER.indexOf(button.dataset.mode) + 1) % ORDER.length];
  try {
    if (next === "auto") localStorage.removeItem("theme");
    else localStorage.setItem("theme", next);
  } catch {
    // storage blocked: the choice lasts for this page only
  }
  apply(next);
});
apply(ORDER.includes(saved()) ? saved() : "auto");
button.hidden = false;

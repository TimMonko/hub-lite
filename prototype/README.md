# Prototype: plugin pages with Jinja and one small stylesheet

Not for merging. This answers "how should a remade plugin page be built, and
what does it cost?" for the stack decision in napari-plans.

- `page_model.py`: the page model. Every fact about a plugin is decided here,
  as plain values, with a comment saying where each comes from.
- `templates/`: `base.html` (site frame) and `plugin.html` (one page). All
  markup lives here. Asset paths are relative, so pages work from disk.
- `static/hub.css`: the hub's stylesheet, with readable class names and
  colour tokens (dark mode is one block).
- napari's shared colours (`napari-tokens.css`), code colours
  (`pygments.css`: `napari` light, `dracula` dark) and icons come from the
  `napari-sphinx-theme` package's `static/brand/` folder, the files
  napari.org uses; napari's logos (header, footer silhouette, favicon) come
  from the `napari-resources` package, as in napari itself. Both are
  dependencies, so bumping a version updates them. The theme is installed
  without Sphinx (`dependency-overrides` in `pyproject.toml`). Templates
  draw an icon inline with `icon("github")`.
- `build.py`: renders every plugin from the data `pixi run fetch-data` wrote.

```bash
pixi run fetch-data
pixi run python prototype/build.py   # pages, the Pagefind index, then the home page
```

## Measurements (2026-11-15, 707 plugins, same data, with header, footer and icons)

| | Today | Prototype |
|---|---|---|
| Plugin page HTML, median | 37.7 KB | 20.2 KB |
| Plugin page HTML, p90 | 49.1 KB | 31.0 KB |
| Largest page | 154 KB | 128 KB (the README) |
| CSS a plugin page loads | ~217 KB (3 files, one minified) | 28 KB (3 files; 22 KB is the code colours, light and dark) |
| Icons | PNGs and inline SVG | inline SVG, ~11 KB a page |
| Web fonts | Google Fonts, 2 families | none (system fonts) |
| Render all pages | 6.2 s | 3.4 to 6.2 s (Markdown and Pygments dominate; varies with machine load) |
| Pagefind index | 6.3 MB | 5.5 MB |
| Pagefind filters | 5 | 4 (see below) |

The prototype keeps the Pagefind names (`data-pagefind-body`, the `meta` and
`filter` names) so search keeps working.

What it leaves out, on purpose: the home page and browse list, and Google
Fonts (system fonts, as napari.org uses).

README fixes the prototype relies on are real stack branches, not prototype
code: one `<pre>` per code block (`hub/05`), and relative links, images and
heading anchors (`hub/06`).

## Found on the way

- **The OS facet is dead today.** None of the 707 plugins has classifiers in
  `plugin_page_data.json`, so every page says "Information not submitted" and
  the `os` filter carries no values. The prototype omits an empty filter, hence
  4 filters. The data contract should carry classifiers (R7).
- **Pagefind's `os` filter on today's site indexes HTML markup**, because the
  filter span wraps a `<ul>`. The prototype puts plain comma-joined text in a
  hidden span instead.

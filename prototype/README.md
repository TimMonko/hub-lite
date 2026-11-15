# Prototype: plugin pages with Jinja and one small stylesheet

Not for merging. This answers "how should a remade plugin page be built, and
what does it cost?" for the stack decision in napari-plans.

- `page_model.py`: the page model. Every fact about a plugin is decided here,
  as plain values, with a comment saying where each comes from.
- `templates/`: `base.html` (site frame) and `plugin.html` (one page). All
  markup lives here. Asset paths are relative, so pages work from disk.
- `static/hub.css`: one stylesheet with readable class names and colour
  tokens (dark mode is one block).
- `build.py`: renders every plugin from the data `pixi run fetch-data` wrote.

```bash
pixi run fetch-data
pixi run python prototype/build.py
pixi run python -m pagefind --site _build_proto
```

## Measurements (2026-11-15, 707 plugins, same data)

| | Today | Prototype |
|---|---|---|
| Plugin page HTML, median | 37.7 KB | 9.2 KB |
| Plugin page HTML, p90 | 49.1 KB | 19.7 KB |
| Largest page | 154 KB | 114 KB (the README) |
| CSS a plugin page loads | ~217 KB (3 files, one minified) | 7.4 KB (2 files) |
| Web fonts | Google Fonts, 2 families | none (system fonts) |
| Render all pages | 6.2 s | 3.4 s |
| Pagefind index | 6.3 MB | 5.5 MB |
| Pagefind filters | 5 | 4 (see below) |

The prototype keeps the Pagefind names (`data-pagefind-body`, the `meta` and
`filter` names) so search keeps working.

What it leaves out, on purpose: the home page and browse list, the header
icons, Google Fonts (Atkinson Hyperlegible would add the font files back).

## Found on the way

- **The OS facet is dead today.** None of the 707 plugins has classifiers in
  `plugin_page_data.json`, so every page says "Information not submitted" and
  the `os` filter carries no values. The prototype omits an empty filter, hence
  4 filters. The data contract should carry classifiers (R7).
- **Pagefind's `os` filter on today's site indexes HTML markup**, because the
  filter span wraps a `<ul>`. The prototype puts plain comma-joined text in a
  hidden span instead.
